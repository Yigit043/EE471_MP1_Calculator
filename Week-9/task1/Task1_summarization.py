"""Task 1 - Summarization: shorten a paragraph."""
from transformers import pipeline

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
text = ("The 2008 Global Financial Crisis stands as the most severe economic collapse of the 21st "
        "century, often compared to the Great Depression of the 1930s. Triggered by the bursting of "
        "the United States housing bubble, its effects rippled across the globe, leading to the "
        "collapse of major financial institutions and a deep international recession. The crisis "
        "began with the subprime mortgage market. In the early 2000s, low interest rates and a push "
        "for homeownership led banks to issue high-risk loans to borrowers with poor credit.")
summary = summarizer(text, max_length=60, min_length=20, do_sample=False)[0]["summary_text"]
print(f"Original: {len(text.split())} words\nSummary ({len(summary.split())} words):\n  {summary}")
