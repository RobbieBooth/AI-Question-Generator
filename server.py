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
from sqlalchemy import text, PrimaryKeyConstraint, ForeignKeyConstraint

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


# Assuming only one student code would be stored per student per question
class StudentSubmittedCode(db.Model):
    __tablename__ = 'student_submitted_code'
    codeSubmitted = db.Column(db.Text, nullable=False)
    codeRunnerQuestionID = db.Column(db.Integer, nullable=False)
    codeRunnerStudentID = db.Column(db.Integer, nullable=False)
    studentUsername = db.Column(db.String(30), nullable=False)
    studentEmail = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('codeRunnerQuestionID', 'studentUsername'),
    )


class StudentTaskAttempt(db.Model):
    __tablename__ = 'student_task_attempt'
    ID = db.Column(db.Integer, primary_key=True)
    questionsCorrect = db.Column(db.Integer, nullable=True)
    CodeUsedToGenerate = db.Column(db.Text, nullable=False)
    Timestamp = db.Column(db.DateTime(timezone=True),
                          server_default=func.now())

    # Columns that will form the composite foreign key
    codeRunnerQuestionID = db.Column(db.Integer, nullable=False)
    studentUsername = db.Column(db.String(30), nullable=False)

    # # Defining the composite foreign key constraint
    # __table_args__ = (
    #     ForeignKeyConstraint(
    #         ['codeRunnerQuestionID', 'studentUsername'],
    #         ['student_submitted_code.codeRunnerQuestionID', 'student_submitted_code.studentUsername']
    #     ),
    # )

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


def save_student_attempt(studentID, codeRunnerQuesionID, code):
    student_attempt = StudentTaskAttempt(studentUsername=studentID, codeRunnerQuestionID=codeRunnerQuesionID,
                                         CodeUsedToGenerate=code)
    db.session.add(student_attempt)
    db.session.commit()
    return student_attempt


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


def get_code_from_previous_submission(student_username, code_runner_previous_question_id) -> str | None:
    '''
    Searches the database for the code that was last submitted for the student_username and code_runner_previous_question_id
    :param student_username: string representing the student unique username e.g: xcc21164
    :param code_runner_previous_question_id: the code runner question id for the previous question which submitted the code
    :return: a string representing the code that was submitted or none if the row was not found in database
    '''
    result = StudentSubmittedCode.query.filter_by(
        studentUsername=student_username,
        codeRunnerQuestionID=code_runner_previous_question_id
    ).first()
    if result:
        return result.codeSubmitted
    else:
        return None


@app.route('/generate_questions', methods=['POST'])
def generate_questions_route():
    code_snippet = request.form.get('code_snippet')
    code_runner_question_id = request.form.get('crui_question_id')
    code_runner_student_id = request.form.get('crui_student_myplace_id')
    student_username = request.form.get('crui_username')
    student_email = request.form.get('crui_student_email')

    code_runner_previous_question_id = request.form.get('crui_previous_question_id')

    if code_snippet is None:
        code_snippet = get_code_from_previous_submission(student_username, code_runner_previous_question_id)

    student_attempt = save_student_attempt(student_username, code_runner_question_id, code_snippet)

    #TODO if student username and questionid exist in generated then ignore and return results

    questions = generate_ai_questions(code_snippet)
    for question in questions.questions:
        new_question = add_question(student_attempt.ID, question.question, question.answer_option,
                                    question.wrong_options)
        question.update_ID(new_question.ID)
    student_questions = questions.to_student_dict()
    return jsonify(questions=student_questions, attempt_id=student_attempt.ID)


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
        if (answer['studentAnswer'] == "This question doesn't seem right?"):
            db.session.execute(text(query_for_not_right), {'question_id': answer['question']['ID']})
        db.session.execute(text(query),
                           {'question_id': answer['question']['ID'], 'answerText': answer['studentAnswer']})

    query_questions_correct = """
    UPDATE `student_task_attempt` SET questionsCorrect = (SELECT COUNT(*) as correct FROM `question` WHERE StudentAnswer = Answer AND attemptID = :attempt_id) WHERE ID = :attempt_id; 
    """
    db.session.execute(text(query_questions_correct), {'attempt_id': id});
    # Commit the transaction
    db.session.commit()

    return {'status': 'success'}


def insert_or_update_code(code_runner_question_id, code_runner_student_id, student_username, code_submitted,
                          student_email=None):
    query = text("""
        INSERT INTO student_submitted_code (codeRunnerQuestionID, codeRunnerStudentID, studentUsername, codeSubmitted, studentEmail)
        VALUES (:code_runner_question_id, :code_runner_student_id, :student_username, :code_submitted, :student_email)
        ON DUPLICATE KEY UPDATE
            codeSubmitted = VALUES(codeSubmitted),
            studentEmail = VALUES(studentEmail)
    """)

    db.session.execute(query, {
        'code_runner_question_id': code_runner_question_id,
        'code_runner_student_id': code_runner_student_id,
        'student_username': student_username,
        'code_submitted': code_submitted,
        'student_email': student_email
    })
    db.session.commit()


@app.route('/savecode', methods=['POST'])
def saveCode():
    code_snippet = request.form.get('code_snippet')
    code_runner_question_id = request.form.get('crui_question_id')
    code_runner_student_id = request.form.get('crui_student_myplace_id')
    student_username = request.form.get('crui_username')
    student_email = request.form.get('crui_student_email')

    insert_or_update_code(code_runner_question_id, code_runner_student_id, student_username, code_snippet,
                          student_email)
    return {'status': 'success'}
