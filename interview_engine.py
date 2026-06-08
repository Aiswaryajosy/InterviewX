import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3-flash",
    "gemini-3-flash-live",
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
            print(f"Model failed {model}: {e}")
    return None


def generate_questions(resume_text):
    prompt = f"""You are an expert interviewer. Based on the following resume, generate exactly 10 thoughtful and relevant interview questions.

Resume:
{resume_text}

Rules:
- Mix behavioral questions (STAR-method) with technical questions
- Questions should be specific to the candidate's experience and skills mentioned
- Number each question 1-10
- Return ONLY the questions, one per line, numbered
- No introductory text, no explanations
"""
    result = call_gemini(prompt)

    if not result:
        return fallback_questions()

    lines = [line.strip() for line in result.split("\n") if line.strip()]
    questions = []
    for line in lines:
        # Remove numbering like "1.", "1)", "Q1:", etc.
        clean = line.lstrip("0123456789.)Q: \t")
        if clean and len(clean) > 10:
            questions.append(clean)

    questions = questions[:10]

    if len(questions) < 5:
        return fallback_questions()

    # Pad to 10 if needed
    while len(questions) < 10:
        questions.extend(fallback_questions()[:10 - len(questions)])

    return questions[:10]


def fallback_questions():
    return [
        "Tell me about yourself and your professional background.",
        "Walk me through a project you're most proud of and your specific contributions.",
        "What are your core technical strengths, and how have you applied them recently?",
        "Describe a situation where you had to solve a complex problem under pressure.",
        "How do you approach learning new technologies or frameworks?",
        "Tell me about a time you collaborated with a difficult team member.",
        "What is your experience with machine learning or AI systems?",
        "How do you ensure the quality and reliability of your code?",
        "Where do you see yourself professionally in the next 3 years?",
        "Why are you interested in this opportunity, and what can you bring to the team?"
    ]


def get_next_question(questions, index):
    if index < len(questions):
        return questions[index]
    return None
