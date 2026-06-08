from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os

from pdf_parser import extract_text_from_pdf
from interview_engine import generate_questions
from evaluator import evaluate_answer, generate_overall_feedback

app = Flask(__name__, template_folder="templates")
CORS(app, supports_credentials=True, origins=["*"])

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/upload", methods=["POST"])
def upload():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    text = extract_text_from_pdf(file)

    if not text:
        return jsonify({"error": "Could not extract text from PDF"}), 422

    # Generate all 10 questions from Gemini
    questions = generate_questions(text)

    # Return ALL questions in an array called "questions" (Plural)
    return jsonify({
        "questions": questions,
        "total": len(questions)
    })

@app.route("/api/answer", methods=["POST"])
def answer():
    data = request.json
    question = data.get("question")
    answer_text = data.get("answer")

    if not question or not answer_text:
        return jsonify({"error": "Missing data"}), 400

    # Evaluate the single answer
    result = evaluate_answer(question, answer_text)

    return jsonify({
        "score": result["score"],
        "feedback": result["feedback"]
    })

@app.route("/api/overall", methods=["POST"])
def overall():
    data = request.json
    history = data.get("history", [])
    
    # Generate the final performance report
    overall_feedback = generate_overall_feedback(history)
    return jsonify({"overall_feedback": overall_feedback})

if __name__ == "__main__":
    print("🚀 InterviewX running at http://127.0.0.1:8000")
    app.run(debug=True, port=8000)
