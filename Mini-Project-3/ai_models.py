"""The three AI models behind the app, one small class each.

    ChatBot         HuggingFaceTB/SmolLM2-360M-Instruct   chat history -> reply
    SpeechToText    openai/whisper-small                  WAV bytes    -> text
    ImageGenerator  stabilityai/sd-turbo                  prompt       -> PNG image

Every model is loaded the first time it is needed (or by the warm-up thread in app.py) and then
kept in memory. A lock makes sure two requests never load the same model twice.
"""
import base64
import io
import threading
import wave

import numpy as np

CHAT_MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"
STT_MODEL = "openai/whisper-small"
IMAGE_MODEL = "stabilityai/sd-turbo"

SYSTEM_PROMPT = ("You are a friendly assistant inside an image generation app. Keep your answers short, "
                 "at most three sentences. When the user asks for an image prompt, answer with one vivid, "
                 "detailed prompt in a single sentence, without quotes.")


class LazyModel:
    """Base class: load() runs _load() only once, even if several requests arrive together."""

    def __init__(self, model_id):
        self.model_id = model_id
        self.ready = False
        self._lock = threading.Lock()

    def load(self):
        with self._lock:
            if not self.ready:
                self._load()
                self.ready = True
        return self

    def _load(self):
        raise NotImplementedError


class ChatBot(LazyModel):
    def __init__(self, model_id=CHAT_MODEL, max_turns=10):
        super().__init__(model_id)
        self.max_turns = max_turns

    def _load(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_id)

    def reply(self, history, max_new_tokens=160):
        """history: [{"role": "user" | "assistant", "content": "..."}, ...] -> the bot's answer."""
        import torch
        self.load()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history[-self.max_turns:]
        inputs = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True,
                                                    return_dict=True, return_tensors="pt")
        with torch.no_grad():
            output = self.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=True,
                                         temperature=0.7, top_p=0.9,
                                         pad_token_id=self.tokenizer.eos_token_id)
        new_tokens = output[0][inputs["input_ids"].shape[-1]:]          # only the new answer
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


class SpeechToText(LazyModel):
    def __init__(self, model_id=STT_MODEL):
        super().__init__(model_id)

    def _load(self):
        from transformers import pipeline
        self.asr = pipeline("automatic-speech-recognition", model=self.model_id)

    @staticmethod
    def read_wav(data):
        """16-bit WAV bytes -> mono float32 samples at 16 kHz (the rate Whisper expects)."""
        with wave.open(io.BytesIO(data), "rb") as f:
            rate, channels = f.getframerate(), f.getnchannels()
            audio = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)
        if rate != 16000:
            n = int(len(audio) * 16000 / rate)
            audio = np.interp(np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio).astype(np.float32)
        return audio

    def transcribe(self, wav_bytes):
        audio = self.read_wav(wav_bytes)
        if len(audio) < 1600:                                            # shorter than 0.1 s
            return ""
        self.load()
        result = self.asr({"raw": audio, "sampling_rate": 16000},
                          generate_kwargs={"language": "english", "task": "transcribe"})
        return result["text"].strip()


class ImageGenerator(LazyModel):
    def __init__(self, model_id=IMAGE_MODEL, steps=2, size=512):
        super().__init__(model_id)
        self.steps, self.size = steps, size

    def _load(self):
        import torch
        from diffusers import AutoPipelineForText2Image
        # the half-precision files were downloaded; on a CPU they are used as float32
        self.pipe = AutoPipelineForText2Image.from_pretrained(self.model_id, variant="fp16",
                                                              torch_dtype=torch.float32)
        self.pipe.set_progress_bar_config(disable=True)

    def generate(self, prompt):
        """Prompt -> PNG image as a data URL the browser can show directly."""
        self.load()
        # sd-turbo is trained for 1-4 steps and no guidance (guidance_scale=0)
        image = self.pipe(prompt=prompt, num_inference_steps=self.steps, guidance_scale=0.0,
                          height=self.size, width=self.size).images[0]
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
