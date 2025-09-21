from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vidhyapath.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app) 

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    options = db.Column(db.Text, nullable=False)  # store JSON string
    answer = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "options": json.loads(self.options)
        }

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    quiz_id = db.Column(db.Integer, nullable=False)
    selected_answer = db.Column(db.String(255), nullable=False)
    correct = db.Column(db.Boolean, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

with app.app_context():
    db.create_all()
    if Quiz.query.count() == 0:
        quiz1 = Quiz(
            question="What is 2 + 2?",
            options=json.dumps([2, 3, 4, 5]),
            answer="4"
        )
        db.session.add(quiz1)
        db.session.commit()

@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Invalid input"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "User already exists"}), 400
    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Invalid input"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"message": f"Welcome {username}"})

@app.route("/quiz/<int:quiz_id>", methods=["GET"])
def get_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404
    return jsonify(quiz.to_dict())

@app.route("/quiz/<int:quiz_id>/submit", methods=["POST"])
def submit_answer(quiz_id):
    data = request.json or {}
    user = data.get("userId")
    answer = str(data.get("selectedAnswer"))
    if not user or not answer:
        return jsonify({"error": "Invalid input"}), 400

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    is_correct = (quiz.answer == answer)
    result = Result(user_id=user, quiz_id=quiz_id, selected_answer=answer, correct=is_correct)
    db.session.add(result)
    db.session.commit()
    return jsonify({"correct": is_correct})

@app.route("/analytics", methods=["GET"])
def analytics():
    results = Result.query.all()
    return jsonify([{
        "userId": r.user_id,
        "quizId": r.quiz_id,
        "selectedAnswer": r.selected_answer,
        "correct": r.correct
    } for r in results])

if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)
