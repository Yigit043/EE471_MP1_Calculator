"""Task 3: Gradio front end - one tab per task, all using the HuggingFaceTasks class.

    python app.py      -> open http://127.0.0.1:7860
"""
from pathlib import Path

import gradio as gr

from hf_tasks import HuggingFaceTasks

hf = HuggingFaceTasks()
HERE = Path(__file__).parent
IMAGES = HERE.parents[1] / "Week-8" / "images"
AUDIO = HERE.parent / "samples" / "speech.wav"
NATE = ("I am Nate, a research assistant at Izmir Institute of Technology, and currently living "
        "and working in the beautiful city İzmir in Türkiye.")
CRISIS = ("The 2008 Global Financial Crisis stands as the most severe economic collapse of the 21st "
          "century, often compared to the Great Depression of the 1930s. Triggered by the bursting of "
          "the United States housing bubble, its effects rippled across the globe, leading to the "
          "collapse of major financial institutions and a deep international recession. The crisis "
          "began with the subprime mortgage market. In the early 2000s, low interest rates and a push "
          "for homeownership led banks to issue high-risk loans to borrowers with poor credit.")


def zero_shot(text, labels):
    return hf.zero_shot(text, [l.strip() for l in labels.split(",") if l.strip()])


def generate(prompt, max_words, alternatives):
    return "\n\n".join(f"{i}. {t}" for i, t in enumerate(hf.generate(prompt, int(max_words), int(alternatives)), 1))


def ner(text):
    return [[t, w, s] for t, w, s in hf.ner(text)]


def answer(question, context):
    text, score = hf.answer(question, context)
    return f"{text}   (score {score:.2f})"


def transcribe(audio):
    if audio is None:
        return "Record or upload some audio first."
    rate, samples = audio                       # gr.Audio(type="numpy") gives (rate, samples)
    return hf.transcribe(samples, rate)


with gr.Blocks(title="EE471 Week 9 - Hugging Face Tasks") as demo:
    gr.Markdown("# 🤗 Hugging Face Tasks\nEE471 Week 9 - ten tasks with transformers pipelines")

    with gr.Tab("Sentiment analysis"):
        t = gr.Textbox(label="Text", value="I've been waiting for a modern software practices course my whole life.")
        gr.Button("Analyze").click(hf.sentiment, t, gr.Label(label="Sentiment"))

    with gr.Tab("Zero-shot classification"):
        t = gr.Textbox(label="Text", value="Berkshire keeps their cash reserves at an extremely high level.")
        l = gr.Textbox(label="Candidate labels (comma separated)", value="finance, politics, sports, technology, education")
        gr.Button("Classify").click(zero_shot, [t, l], gr.Label(label="Scores"))

    with gr.Tab("Text generation"):
        t = gr.Textbox(label="Start of the sentence",
                       value="If I continue to complete all in-class exercises in this modern software practices course,")
        w = gr.Slider(10, 60, value=35, step=1, label="Maximum words")
        n = gr.Slider(1, 3, value=2, step=1, label="Alternatives")
        gr.Button("Generate").click(generate, [t, w, n], gr.Textbox(label="Completions", lines=8))

    with gr.Tab("Mask filling"):
        t = gr.Textbox(label="Sentence with [MASK]", value="To understand generative AI, one must study [MASK] well.")
        gr.Button("Fill").click(hf.fill_mask, t, gr.Label(label="Best words"))

    with gr.Tab("Named entity recognition"):
        t = gr.Textbox(label="Text", value=NATE, lines=3)
        gr.Button("Find entities").click(ner, t, gr.Dataframe(headers=["Type", "Words", "Score"]))

    with gr.Tab("Question answering"):
        c = gr.Textbox(label="Context", value=NATE, lines=3)
        q = gr.Textbox(label="Question", value="Where do I work?")
        gr.Button("Answer").click(answer, [q, c], gr.Textbox(label="Answer"))

    with gr.Tab("Summarization"):
        t = gr.Textbox(label="Text", value=CRISIS, lines=7)
        gr.Button("Summarize").click(hf.summarize, t, gr.Textbox(label="Summary", lines=4))

    with gr.Tab("Translation"):
        t = gr.Textbox(label="French text", value="Ce cours est produit par Hugging Face.", lines=3)
        gr.Button("Translate to English").click(hf.translate, t, gr.Textbox(label="English", lines=3))

    with gr.Tab("Image classification"):
        img = gr.Image(type="pil", label="Image",
                       value=str(IMAGES / "pose-2.jpg") if (IMAGES / "pose-2.jpg").exists() else None)
        gr.Button("Classify").click(hf.classify_image, img, gr.Label(label="ImageNet classes"))

    with gr.Tab("Speech recognition"):
        a = gr.Audio(sources=["microphone", "upload"], type="numpy", label="Speak or upload a WAV file",
                     value=str(AUDIO) if AUDIO.exists() else None)
        gr.Button("Transcribe").click(transcribe, a, gr.Textbox(label="Text", lines=3))

if __name__ == "__main__":
    demo.launch()
