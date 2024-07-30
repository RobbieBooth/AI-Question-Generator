import os
import random
import site

from sqlalchemy.orm import aliased

vendor_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "vendor")
site.addsitedir(vendor_path)

import json

from functools import wraps
from QuestionGeneration import generate_ai_questions
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.sql import func
from sqlalchemy import text

from flask_cors import CORS

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# env.get(
#         "DATABASE_HOST")

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = \
    "mysql+pymysql://" + env.get("DATABASE_USERNAME") + ":" + env.get("DATABASE_PASSWORD") + "@" + env.get(
        "DATABASE_HOST") + ":" + env.get("DATABASE_PORT") + "/" + env.get("DATABASE_NAME")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Allow all origins
CORS(app)

db = SQLAlchemy(app)


class StudentTaskAttempt(db.Model):
    __tablename__ = 'student_task_attempt'
    ID = db.Column(db.Integer, primary_key=True)
    questionsCorrect = db.Column(db.Integer, nullable=True)
    CodeSubmitted = db.Column(db.Text, nullable=False)
    Timestamp = db.Column(db.DateTime(timezone=True),
                          server_default=func.now())
    studentID = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Student {self.firstname}>'


class OptionTable(db.Model):
    __tablename__ = 'optionTable'
    ID = db.Column(db.Integer, primary_key=True)
    optionText = db.Column(db.Text, nullable=False)


class Question(db.Model):
    __tablename__ = 'question'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attemptID = db.Column(db.Integer, db.ForeignKey('student_task_attempt.ID'), nullable=False)
    Question = db.Column(db.Text, nullable=False)
    StudentAnswer = db.Column(db.Integer, db.ForeignKey('optionTable.ID'), nullable=True)
    Answer = db.Column(db.Integer, db.ForeignKey('optionTable.ID'), nullable=False)
    this_doesnt_seem_right = db.Column(db.Boolean, nullable=False, default=False)

    # Define relationships
    attempt_id = db.relationship('StudentTaskAttempt', foreign_keys=[attemptID])
    student_answer_option = db.relationship('OptionTable', foreign_keys=[StudentAnswer])
    correct_answer_option = db.relationship('OptionTable', foreign_keys=[Answer])


# Define the association table
question_options = db.Table('questionOptions',
                            db.Column('question_id', db.Integer, db.ForeignKey('question.ID'), primary_key=True),
                            db.Column('option_id', db.Integer, db.ForeignKey('optionTable.ID'), primary_key=True)
                            )


# Establish relationship (optional, if you need to use backref)
class QuestionOption(db.Model):
    __tablename__ = 'questionOption'
    question_id = db.Column(db.Integer, db.ForeignKey('question.ID'), primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('optionTable.ID'), primary_key=True)
    question = db.relationship(Question, backref=db.backref("question_option", cascade="all, delete-orphan"))
    option = db.relationship(OptionTable, backref=db.backref("question_option", cascade="all, delete-orphan"))


with app.app_context():
    db.drop_all()
    db.create_all()

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
        # redirect_uri="https://devweb2023.cis.strath.ac.uk/xbb21163-python/callback"
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    # return redirect("https://devweb2023.cis.strath.ac.uk/xbb21163-python/")
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                # "returnTo": "https://devweb2023.cis.strath.ac.uk/xbb21163-python/",
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


def requires_auth(f):
    """Sends user to home page if they are not logged in else they will continue on page they are on"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect('/')
        return f(*args, **kwargs)

    return decorated


@app.route('/protected')
@requires_auth
def protected():
    user = session.get('user')
    userinfo = user["userinfo"]
    return f'Hello, {userinfo["name"]}! Your user ID is {userinfo["sub"]}.'


@app.route('/task')
# @requires_auth
def code_task():
    return render_template("codeTask.html", task_name="Task 1", lecturer_message="This task is not too hard!",
                           programming_language="Java")


def get_ID(session):
    user = session.get('user')
    userinfo = user["userinfo"]
    return userinfo["sub"]


def save_student_attempt(studentID, code):
    student_attempt = StudentTaskAttempt(studentID=studentID, CodeSubmitted=code)
    db.session.add(student_attempt)
    db.session.commit()
    return student_attempt
    # otherOptions = []
    # otherOptions.append("1")
    # otherOptions.append("2")
    # otherOptions.append("3")
    # otherOptions.append("4")
    # add_question(student_attempt.ID, "hello", "yes, hello", otherOptions)


def add_question(attemptID, question, answer: str, wrong_options: list[str]):
    options = []

    answer = OptionTable(optionText=answer)
    db.session.add(answer)
    options.append(answer)

    for option_text in wrong_options:
        new_option = OptionTable(optionText=option_text)
        db.session.add(new_option)
        options.append(new_option)

    db.session.commit()
    # data = request.json
    # attemptID = data.get('attemptID')
    # question_text = data.get('Question')
    # student_answer_id = data.get('StudentAnswer')
    # answer_id = data.get('Answer')

    # Validate and create the question
    new_question = Question(
        attemptID=attemptID,
        Question=question,
        Answer=answer.ID
    )

    db.session.add(new_question)
    db.session.commit()

    for option in options:
        questionOption = QuestionOption(question_id=new_question.ID, option_id=option.ID)
        db.session.add(questionOption)
    db.session.commit()

    return new_question


@app.route('/generate_questions', methods=['POST'])
def generate_questions_route():
    code_snippet = request.form.get('code_snippet')
    student_attempt = save_student_attempt(request.form.get('crui_username'), code_snippet)
    # questions = generate_questions(code_snippet)
    questions = generate_ai_questions(code_snippet)
    for question in questions.questions:
        new_question = add_question(student_attempt.ID, question.question, question.answer_option,
                                    question.wrong_options)
        question.update_ID(new_question.ID)
    student_questions = questions.to_student_dict()
    return jsonify(questions=student_questions, attempt_id=student_attempt.ID)


def generate_questions(code_snippet):
    # Placeholder for question generation logic
    questions = '''[
    {
    "ID": 1,
    "question": "Which of the following is a programming language?",
    "answer": "Python",
    "options": [
        { "questionID": 1, "ID": 1, "option": "Python" },
        { "questionID": 1, "ID": 2, "option": "HTML" },
        { "questionID": 1, "ID": 3, "option": "CSS" },
        { "questionID": 1, "ID": 4, "option": "SQL" }
    ]
},
    {
    "ID": 2,
    "question": "Which company developed the Java programming language?",
    "answer": "Sun Microsystems",
    "options": [
        { "questionID": 2, "ID": 1, "option": "Sun Microsystems" },
        { "questionID": 2, "ID": 2, "option": "Microsoft" },
        { "questionID": 2, "ID": 3, "option": "IBM" },
        { "questionID": 2, "ID": 4, "option": "Oracle" }
    ]
},
    {
    "ID": 3,
    "question": "What does 'HTML' stand for?",
    "answer": "HyperText Markup Language",
    "options": [
        { "questionID": 3, "ID": 1, "option": "HyperText Markup Language" },
        { "questionID": 3, "ID": 2, "option": "HighText Machine Language" },
        { "questionID": 3, "ID": 3, "option": "HyperText Media Language" },
        { "questionID": 3, "ID": 4, "option": "Hyperlink and Text Markup Language" }
    ]
},
    {
    "ID": 4,
    "question": "What does CSS stand for?",
    "answer": "Cascading Style Sheets",
    "options": [
        { "questionID": 4, "ID": 1, "option": "Cascading Style Sheets" },
        { "questionID": 4, "ID": 2, "option": "Computer Style Sheets" },
        { "questionID": 4, "ID": 3, "option": "Creative Style Sheets" },
        { "questionID": 4, "ID": 4, "option": "Cascading Script Sheets" }
    ]
},
    {
    "ID": 5,
    "question": "Which data structure uses LIFO (Last In, First Out) order?",
    "answer": "Stack",
    "options": [
        { "questionID": 5, "ID": 1, "option": "Stack" },
        { "questionID": 5, "ID": 2, "option": "Queue" },
        { "questionID": 5, "ID": 3, "option": "Array" },
        { "questionID": 5, "ID": 4, "option": "Linked List" }
    ]
}
]
'''
    return questions


@app.route("/")
def home():
    return render_template("home.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))


# Save the students answer to the attempt based on the attemptID
#
@app.route('/saveanswers/<int:id>', methods=['POST'])
def saveanswers(id):
    # Get JSON data from the request
    studentAnswers = request.get_json()

    query = """
    UPDATE `question` AS q
    SET q.studentanswer = (
        SELECT ID FROM `optionTable` as OT
        LEFT JOIN `questionOption` as QO ON OT.ID = QO.option_id
        WHERE QO.question_id = :question_id AND OT.optionText = :answerText
        LIMIT 1
    )
    WHERE q.ID = :question_id;
    """

    query_for_not_right = """
    UPDATE `question` as q
    SET q.this_doesnt_seem_right = true
    WHERE q.ID = :question_id;
    """

    # Execute the raw SQL query
    for answer in studentAnswers:
        if(answer['studentAnswer'] == "This question doesn't seem right?"):
            db.session.execute(text(query_for_not_right),{'question_id': answer['question']['ID']})
        db.session.execute(text(query),
                           {'question_id': answer['question']['ID'], 'answerText': answer['studentAnswer']})

    query_questions_correct = """
    UPDATE `student_task_attempt` SET questionsCorrect = (SELECT COUNT(*) as correct FROM `question` WHERE StudentAnswer = Answer AND attemptID = :attempt_id) WHERE ID = :attempt_id; 
    """
    db.session.execute(text(query_questions_correct), {'attempt_id': id});
    # Commit the transaction
    db.session.commit()

    return {'status': 'success'}

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=env.get("PORT", 3000))
