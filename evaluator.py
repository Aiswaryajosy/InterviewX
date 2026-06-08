import os
import re
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]


def call_gemini(prompt):
    for model in MODELS:
        try:
            res = client.models.generate_content(
                model=model,
                contents=prompt
            )
            return res.text
        except Exception as e:
            print(f"Eval model failed {model}: {e}")
    return None


def parse_score(text):
    """Extract numeric score from text like 'Score: 7' or '7/10'"""
    patterns = [
        r"Score:\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*/\s*10",
        r"score\s+of\s+(\d+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            return min(10.0, max(0.0, score))
    return None


def evaluate_answer(question, answer):
    prompt = f"""You are an expert technical interview evaluator. Evaluate the following interview answer.

Question: {question}

Answer: {answer}

Provide your evaluation in EXACTLY this format:

Score: [number from 0-10]

Strengths:
[2-3 key strengths of the answer]

Areas for Improvement:
[2-3 specific ways to improve]

Model Answer Hint:
[A 2-3 sentence example of a stronger answer]
"""

    result = call_gemini(prompt)

    if not result:
        return {
            "score": 5,
            "feedback": "Good effort. Focus on providing specific examples and technical depth in your answers.",
            "raw": ""
        }

    # Parse the score from the response
    parsed_score = parse_score(result)
    score = parsed_score if parsed_score is not None else 6

    return {
        "score": score,
        "feedback": result,
        "raw": result
    }
