from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///vidhyapath.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    options = db.Column(db.PickleType, nullable=False)
    answer = db.Column(db.String(255), nullable=False)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.String(50), nullable=False)
    quizId = db.Column(db.Integer, nullable=False)
    selectedAnswer = db.Column(db.String(255), nullable=False)
    correct = db.Column(db.Boolean, nullable=False)

with app.app_context():
    db.create_all()
    if Quiz.query.count() == 0:
        quiz1 = Quiz(
            question="What is 2 + 2?",
            options=[2, 3, 4, 5],
            answer="4"
        )
        db.session.add(quiz1)
        db.session.commit()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # can be plain for now

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "User already exists"}), 400
    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": f"Welcome {username}"})


@app.route("/quiz/<int:quiz_id>", methods=["GET"])
def get_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404
    return jsonify({
        "id": quiz.id,
        "question": quiz.question,
        "options": quiz.options
    })

@app.route("/quiz/<int:quiz_id>/submit", methods=["POST"])
def submit_answer(quiz_id):
    data = request.json
    user = data.get("userId")
    answer = str(data.get("selectedAnswer"))

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    is_correct = (quiz.answer == answer)
    result = Result(userId=user, quizId=quiz_id, selectedAnswer=answer, correct=is_correct)
    db.session.add(result)
    db.session.commit()

    return jsonify({"correct": is_correct})

@app.route("/analytics", methods=["GET"])
def analytics():
    results = Result.query.all()
    return jsonify([{
        "userId": r.userId,
        "quizId": r.quizId,
        "selectedAnswer": r.selectedAnswer,
        "correct": r.correct
    } for r in results])

if __name__ == "__main__":
    app.run(debug=True)