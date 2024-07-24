import os
import random
import site
from functools import wraps

# from flaskTables import StudentTaskAttempt

vendor_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "vendor")
site.addsitedir(vendor_path)

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.sql import func

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = \
    "mysql+pymysql://" + env.get("DATABASE_USERNAME") + ":" + env.get("DATABASE_PASSWORD") + "@" + env.get(
        "DATABASE_HOST") + ":" + env.get("DATABASE_PORT") + "/" + env.get("DATABASE_NAME")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class StudentTaskAttempt(db.Model):
    __tablename__ = 'student_task_attempt'
    ID = db.Column(db.Integer, primary_key=True)
    questionsCorrect = db.Column(db.Integer, nullable=True)
    CodeSubmitted = db.Column(db.Text, nullable=False)
    Timestamp = db.Column(db.DateTime(timezone=True),
                          server_default=func.now())
    studentID = db.Column(db.String(255), nullable=False)

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

    # Define relationships
    attempt_id = db.relationship('StudentTaskAttempt', foreign_keys=[attemptID])
    student_answer_option = db.relationship('OptionTable', foreign_keys=[StudentAnswer])
    correct_answer_option = db.relationship('OptionTable', foreign_keys=[Answer])

# # Define the association table
# question_options = db.Table('questionOptions',
#     db.Column('question_id', db.Integer, db.ForeignKey('question.ID'), primary_key=True),
#     db.Column('option_id', db.Integer, db.ForeignKey('optionTable.ID'), primary_key=True)
# )

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
    otherOptions = []
    otherOptions.append("1")
    otherOptions.append("2")
    otherOptions.append("3")
    otherOptions.append("4")
    add_question(student_attempt.ID, "hello", "yes, hello", otherOptions)


def add_question(attemptID, question, answer: str, otherOptions: list[str]):
    options = []

    answer = OptionTable(optionText=answer)
    db.session.add(answer)
    options.append(answer)

    for option_text in otherOptions:
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



@app.route('/generate_questions', methods=['POST'])
def generate_questions_route():
    code_snippet = request.form.get('code_snippet')
    save_student_attempt(1234, code_snippet)
    questions = generate_questions(code_snippet)
    return jsonify(questions=questions)


def generate_questions(code_snippet):
    # Placeholder for question generation logic
    questions = '''[
    {
        "ID": 1,
        "question": "What is the capital of France?",
        "options": [
            { "questionID": 1, "ID": 1, "option": "Paris" },
            { "questionID": 1, "ID": 2, "option": "London" },
            { "questionID": 1, "ID": 3, "option": "Berlin" },
            { "questionID": 1, "ID": 4, "option": "Madrid" }
        ]
    },
    {
        "ID": 2,
        "question": "Which planet is known as the Red Planet?",
        "options": [
            { "questionID": 2, "ID": 1, "option": "Earth" },
            { "questionID": 2, "ID": 2, "option": "Mars" },
            { "questionID": 2, "ID": 3, "option": "Jupiter" },
            { "questionID": 2, "ID": 4, "option": "Saturn" }
        ]
    },
    {
        "ID": 3,
        "question": "What is the largest mammal?",
        "options": [
            { "questionID": 3, "ID": 1, "option": "Elephant" },
            { "questionID": 3, "ID": 2, "option": "Blue Whale" },
            { "questionID": 3, "ID": 3, "option": "Great White Shark" },
            { "questionID": 3, "ID": 4, "option": "Giraffe" }
        ]
    },
    {
        "ID": 4,
        "question": "What is the chemical symbol for gold?",
        "options": [
            { "questionID": 4, "ID": 1, "option": "Au" },
            { "questionID": 4, "ID": 2, "option": "Ag" },
            { "questionID": 4, "ID": 3, "option": "Pb" },
            { "questionID": 4, "ID": 4, "option": "Fe" }
        ]
    },
    {
        "ID": 5,
        "question": "Who wrote 'Romeo and Juliet'?",
        "options": [
            { "questionID": 5, "ID": 1, "option": "William Shakespeare" },
            { "questionID": 5, "ID": 2, "option": "Charles Dickens" },
            { "questionID": 5, "ID": 3, "option": "Jane Austen" },
            { "questionID": 5, "ID": 4, "option": "Mark Twain" }
        ]
    }
]
'''
    return questions


@app.route("/")
def home():
    return render_template("home.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=env.get("PORT", 3000))
