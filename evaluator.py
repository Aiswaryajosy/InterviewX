import os
import json
import time
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# SDK automatically skips models that are unavailable
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3-flash",
    "gemini-3-flash-live",
]

def call_gemini_json(prompt):
    last_error = "Unknown Error"
    for model in MODELS:
        try:
            res = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0, 
                    response_mime_type="application/json" 
                )
            )
            if res and res.text:
                return res.text
        except Exception as e:
            last_error = str(e)
            print(f"Eval model failed [{model}]: {e}")
            time.sleep(2) # Pausing for 2 seconds to let the rate limit cool down
            
    # If all models fail, return the exact text of the last error
    return f"SYSTEM_ERROR: {last_error}"

def evaluate_answer(question, answer):
    prompt = f"""You are a ruthless, objective technical interview grader. 
You must evaluate the candidate's answer strictly on accuracy, technical depth, and relevance.

Question: {question}
Candidate Answer: {answer}

CRITICAL SCORING RULES:
- If the answer is random letters (e.g., "asdf"), "I don't know", empty, or completely unrelated: YOU MUST SCORE 0.0.
- If the answer is completely technically incorrect: YOU MUST SCORE 0.0.
- DO NOT give points for effort. DO NOT be polite.

Return ONLY a valid JSON object matching this exact schema:
{{
  "score": <float between 0.0 and 10.0>,
  "strengths": "<string: what they did well, or 'None' if score is 0>",
  "improvements": "<string: what is missing, or 'Answer was unintelligible' if score is 0>",
  "model_answer": "<string: a short example of a perfect answer>"
}}
"""
    result = call_gemini_json(prompt)

    # If our system caught an error, display it directly on the frontend
    if result and result.startswith("SYSTEM_ERROR:"):
        return {
            "score": 0.0,
            "feedback": f"🚨 DIAGNOSTIC ERROR:\n\n{result.replace('SYSTEM_ERROR: ', '')}\n\nCheck your terminal for more details.",
            "raw": ""
        }

    try:
        parsed = json.loads(result.strip())
        score = float(parsed.get("score", 0.0))
        
        feedback_formatted = (
            f"Strengths:\n{parsed.get('strengths', 'None.')}\n\n"
            f"Areas for Improvement:\n{parsed.get('improvements', 'Provide a clear, on-topic answer.')}\n\n"
            f"Model Answer Hint:\n{parsed.get('model_answer', 'Review the core concepts of the question.')}"
        )
        
        return {
            "score": min(10.0, max(0.0, score)),
            "feedback": feedback_formatted,
            "raw": result
        }
    except Exception as e:
        print("JSON Parse Error:", e)
        return {
            "score": 0.0,
            "feedback": f"🚨 DIAGNOSTIC ERROR:\n\nJSON Parsing failed. The AI returned:\n{result}",
            "raw": result
        }

def generate_overall_feedback(history):
    if not history:
        return "No data to evaluate."
        
    total_score = sum(float(h.get('score', 0)) for h in history)
    avg_score = total_score / len(history) if len(history) > 0 else 0
    
    prompt = f"""You are an expert technical recruiter. Review this interview session.
The candidate achieved an overall average score of {avg_score:.1f} out of 10.
    
Interview History:
"""
    for i, h in enumerate(history):
        prompt += f"Q{i+1}: {h['question']}\nScore: {h['score']}/10\n\n"

    prompt += f"""Based on their actual average score of {avg_score:.1f}/10, provide a comprehensive summary (3 short paragraphs) covering:
1. Overall Impression (You MUST acknowledge their final score of {avg_score:.1f}/10 explicitly)
2. Key Strengths observed across the questions
3. Final Recommendation for their job hunt
"""
    # For text feedback, we don't force JSON, so we use a standard text call
    for model in MODELS:
        try:
            res = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.4)
            )
            if res and res.text:
                return res.text
        except Exception as e:
            time.sleep(1)
            
    return f"Final Average Score: {avg_score:.1f}/10.\n\nGreat job completing the interview. Unfortunately, API rate limits prevented the generation of the final written summary."