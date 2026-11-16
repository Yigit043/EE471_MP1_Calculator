"""Decision Maker: answer structured questions about a text, with probabilities
(EmbeddingGemma 2). Three question types: choice, yes/no and score."""
import mediapipe as mp

from common import model

D = mp.tasks.decision
options = D.DecisionMakerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model("embedding_gemma")),
    max_num_tokens=512,
)
messages = [
    "I was charged twice for my subscription this month.",
    "The app crashes every time I try to log in.",
    "Can you add a dark mode to the settings page?",
]
topic = D.ChoiceQuestion(criteria={
    "billing": "Payments, charges, invoices or refunds.",
    "bug": "Something is broken, crashes or shows an error.",
    "feature": "A request for a new feature or improvement.",
}, normalize_prior=True)
urgent = D.BooleanQuestion(condition="The user cannot use the product right now.")
mood = D.ScoreQuestion(rubric=["very calm", "calm", "annoyed", "angry", "furious"])

with D.DecisionMaker.create_from_options(options) as maker:
    maker.prewarm(topic)
    for text in messages:
        c = maker.evaluate_choice(text, topic)
        b = maker.evaluate_boolean(text, urgent)
        s = maker.evaluate_score(text, mood)
        print(f"\n{text}")
        print(f"  topic : {c.selected_key} (confidence {c.confidence:.2f})")
        print(f"  urgent: {b.value} (p = {b.probability_true:.2f})")
        level = mood.rubric[min(round(s.expected_score), len(mood.rubric) - 1)]
        print(f"  mood  : {level} (score {s.expected_score:.2f} on a 0-4 scale)")
