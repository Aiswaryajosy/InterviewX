from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import os

from pdf_parser import extract_text_from_pdf
from interview_engine import generate_questions, get_next_question
from evaluator import evaluate_answer

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "interviewx-secret-2024")
CORS(app, supports_credentials=True, origins=["http://127.0.0.1:8000", "http://localhost:8000", "null", "*"])


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

    questions = generate_questions(text)

    session["questions"] = questions
    session["index"] = 0
    session["history"] = []

    return jsonify({
        "question": questions[0],
        "total": len(questions)
    })


@app.route("/api/answer", methods=["POST"])
def answer():
    data = request.json
    if not data or "answer" not in data:
        return jsonify({"error": "No answer provided"}), 400

    answer_text = data["answer"]

    index = session.get("index", 0)
    questions = session.get("questions", [])

    if not questions or index >= len(questions):
        return jsonify({"error": "No active session"}), 400

    question = questions[index]
    result = evaluate_answer(question, answer_text)

    history = session.get("history", [])
    history.append({
        "question": question,
        "answer": answer_text,
        "score": result["score"],
        "feedback": result["feedback"]
    })

    index += 1
    session["index"] = index
    session["history"] = history

    if index >= len(questions):
        total = sum(h["score"] for h in history) / len(history)
        return jsonify({
            "finished": True,
            "total_score": round(total, 1),
            "history": history
        })

    next_q = get_next_question(questions, index)

    return jsonify({
        "finished": False,
        "next_question": next_q,
        "question_index": index,
        "score": result["score"],
        "feedback": result["feedback"]
    })


@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({"status": "ok", "message": "InterviewX API is running"})


if __name__ == "__main__":
    print("🚀 InterviewX running at http://127.0.0.1:8000")
    app.run(debug=True, port=8000)
