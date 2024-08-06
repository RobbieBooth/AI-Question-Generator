import os
import site

vendor_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "vendor")
site.addsitedir(vendor_path)

import json

from QuestionGeneration import generate_ai_questions
from os import environ as env

from dotenv import find_dotenv, load_dotenv
from flask import Flask, render_template, session, jsonify, request
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.sql import func
from sqlalchemy import text, PrimaryKeyConstraint

from flask_cors import CORS
import QuestionGeneration

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    "mysql+pymysql://" + env.get("DATABASE_USERNAME") + ":" + env.get("DATABASE_PASSWORD") + "@" + env.get(
        "DATABASE_HOST") + ":" + env.get("DATABASE_PORT") + "/" + env.get("DATABASE_NAME")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# increase max payload size
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Allow all origins
CORS(app)

db = SQLAlchemy(app)

# Default types used when generating questions
default_question_count = 8
default_context = None
default_question_topics = """
    Some type of potential questions topics could be:
    -Parameter Names
    -Variable Names
    -Loop End
    -Variable Declaration
    -Variable role – i.e: Which of the following best describes the role of variable <Variable>
    -Line Purpose
    -Loop Count
    -Variable Trace"""
default_code_template = None
default_code_language = "Java"
default_generation_mode = False


class CodeQuestion(db.Model):
    """
    The question that the AI should generate questions based on
    """
    __tablename__ = 'code_question'
    id = db.Column(db.Integer, primary_key=True)
    template = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50), nullable=False)


class StudentSubmittedCode(db.Model):
    """
    The code that the student has submitted for that task. Assuming only one student code would be stored per student
    per question
    """

    __tablename__ = 'student_submitted_code'
    codeSubmitted = db.Column(db.Text, nullable=False)
    # linkedCodeQuestionID = db.Column(db.Integer, nullable=False)
    codeRunnerStudentID = db.Column(db.Integer, nullable=False)
    studentUsername = db.Column(db.String(30), nullable=False)
    studentEmail = db.Column(db.String(255), nullable=True)
    linkedCodeQuestionID = db.Column(db.Integer, db.ForeignKey('code_question.id'), nullable=False)

    # Define relationships
    code_question_id = db.relationship('CodeQuestion', foreign_keys=[linkedCodeQuestionID])

    __table_args__ = (
        PrimaryKeyConstraint('linkedCodeQuestionID', 'studentUsername'),
    )


class StudentTaskAttempt(db.Model):
    """
    Table for every time a student wants to generate questions
    """
    __tablename__ = 'student_task_attempt'
    ID = db.Column(db.Integer, primary_key=True)
    questionsCorrect = db.Column(db.Integer, nullable=True)
    CodeUsedToGenerate = db.Column(db.Text, nullable=False)
    Timestamp = db.Column(db.DateTime(timezone=True),
                          server_default=func.now())

    attempted = db.Column(db.Boolean, nullable=False, default=False)
    # Columns that will form the composite foreign key
    codeRunnerQuestionID = db.Column(db.Integer, nullable=False)
    studentUsername = db.Column(db.String(30), nullable=False)


class OptionTable(db.Model):
    """
    An option that is used in a question
    """
    __tablename__ = 'optionTable'
    ID = db.Column(db.Integer, primary_key=True)
    optionText = db.Column(db.Text, nullable=False)


class Question(db.Model):
    """
    A question that has been generated by Artificial Intelligence
    """
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


class QuestionOption(db.Model):
    """
    Relationship between question and its options
    """
    __tablename__ = 'questionOption'
    question_id = db.Column(db.Integer, db.ForeignKey('question.ID'), primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('optionTable.ID'), primary_key=True)
    question = db.relationship(Question, backref=db.backref("question_option", cascade="all, delete-orphan"))
    option = db.relationship(OptionTable, backref=db.backref("question_option", cascade="all, delete-orphan"))


# with app.app_context():
#     db.drop_all()
#     db.create_all()


def save_student_attempt(studentID, codeRunnerQuestionID, code):
    """
    Saves the students attempt to the database
    :param studentID: the id of the student
    :param codeRunnerQuestionID: the id of the question they are attempting
    :param code: the code that was used to generate the Artificial Intelligence questions
    :return: The studentTaskAttempt object
    """
    student_attempt = StudentTaskAttempt(studentUsername=studentID, codeRunnerQuestionID=codeRunnerQuestionID,
                                         CodeUsedToGenerate=code)
    db.session.add(student_attempt)
    db.session.commit()
    return student_attempt


def add_question(attemptID, question: str, answer: str, wrong_options: list[str]):
    """
    Adds a question to the database
    :param attemptID: The StudentTaskAttempt id
    :param question: The question that was generated
    :param answer: The answer to the question
    :param wrong_options: a list of wrong options for the question
    :return: The Question object
    """
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
        linkedCodeQuestionID=code_runner_previous_question_id
    ).first()
    if result:
        return result.codeSubmitted
    else:
        return None


def get_questions_from_database(attempt_id) -> QuestionGeneration.Question_Bank:
    """
    Retrieves the questions from the database from the StudentTaskAttempt of id `attempt_id`
    :param attempt_id: The StudentTaskAttempt id
    :return: The questions that were generated for that `attempt_id`
    """
    sqlQuery = """
    SELECT 
    q.ID AS question_id,
    q.Question as question,
    q.this_doesnt_seem_right as this_doesnt_seem_right,
    GROUP_CONCAT(o.optionText ORDER BY o.id ASC SEPARATOR '<MY_SEPARATOR>') AS options,
    ao.optionText AS answer_text,
    CASE
        WHEN sao.optionText IS NULL AND q.this_doesnt_seem_right = 1 THEN :defaultNotRightValue
        ELSE sao.optionText
    END AS student_answer
FROM 
    question q
JOIN 
    questionOption qo
ON 
    q.id = qo.question_id
JOIN 
    optionTable o
ON 
    qo.option_id = o.id
LEFT JOIN 
    optionTable ao
ON 
    q.answer = ao.id  -- Join to get the answer text
LEFT JOIN 
    optionTable sao
ON 
    q.StudentAnswer = sao.id  -- Join to get the student answer text
WHERE 
    q.attemptID = :attemptID 
GROUP BY 
    q.id, q.Question;
    """

    result = db.session.execute(text(sqlQuery),
                                {'attemptID': attempt_id, 'defaultNotRightValue': "This question doesn't seem right?"})
    if not result:
        return QuestionGeneration.Question_Bank([])

    questions = []
    for row in result:
        question_id = row[0]
        question_text = row[1]
        this_doesnt_seem_right = row[2]
        options_list: list[str] = row[3].split('<MY_SEPARATOR>')
        answer = row[4]
        student_answer = row[5]
        options_list.remove(answer)

        question = QuestionGeneration.Question(question=question_text, answer_option=answer, wrong_options=options_list,
                                               ID=question_id, student_answer=student_answer)
        questions.append(question)

    return QuestionGeneration.Question_Bank(questions)


@app.route('/generate_questions', methods=['POST'])
def generate_questions_route():
    """
    Generate questions using Artificial Intelligence (AI). If `generation_mode` is `false` then it will generate
    questions, if it hasn't already for that `crui_question_id` and `crui_username`. If it has already generated for
    that `crui_question_id` and `crui_username` it will get the generation from the database or if the student has
    answered the questions then it will return those answers.

    The API body should look like:
    {
    "crui_username": Students unique username,
    "crui_student_email": studuents email address,
    "crui_student_myplace_id": the studnents moodle id,
    "crui_question_id": moodles unique question id,
    "crui_previous_question_id": the CodeQuestion database id for the code submitted to for this question,
    "code_snippet": str | None - the students code snippet - if we are using the previous question submission then this
    should be null,
    "question_topics": str | None - Comma seperated values of question topics. Have None if we are wanting to use default,
    "code_context": str | None - the conext of the "code_snippet" or the code stored in the `crui_previous_question_id`,
    "question_count": str | None - the number of questions for the AI to generate. None will use default,
    "generation_mode": boolean | None - generation mode will ignore all previous saved questions generated and will
    always generate questions when set to `True`. This is recommended for testing only. Default is False.
    }


    """
    code_snippet: str | None = request.form.get('code_snippet')
    code_runner_question_id = request.form.get('crui_question_id')
    code_runner_student_id = request.form.get('crui_student_myplace_id')
    student_username = request.form.get('crui_username')
    student_email = request.form.get('crui_student_email')
    code_runner_previous_question_id = request.form.get('crui_previous_question_id')

    # does not get previous questions from database if true - just generates more
    generation_mode: bool = request.form.get('generation_mode', default_generation_mode)

    try:
        question_count = int(request.form.get('question_count', default_question_count))
    except ValueError:
        question_count = default_question_count

    code_context = request.form.get('code_context', default_context)
    code_template = request.form.get('code_template', default_code_template)

    # Custom question topics or default ones
    question_topics = request.form.get('question_topics')
    if is_empty(question_topics):
        question_topics = default_question_topics
    else:
        question_topics = "The Questions should be on these topics: {0}".format(question_topics)

    code_language = request.form.get('code_language')
    if is_empty(code_language):
        code_language = default_code_language

    # If question template exists override one given same for language
    existing_code_question: CodeQuestion | None = CodeQuestion.query.get(code_runner_previous_question_id)
    if existing_code_question is not None:
        code_template = existing_code_question.template
        code_language = existing_code_question.language

    # Only check database if we are wanting old generations or answers
    if not generation_mode:
        # Query to find the ID
        result = db.session.query(StudentTaskAttempt.ID, StudentTaskAttempt.attempted).filter(
            StudentTaskAttempt.codeRunnerQuestionID == code_runner_question_id,
            StudentTaskAttempt.studentUsername == student_username
        ).first()

        # If questions have already been generated get them
        if result is not None:
            attempt_id = result[0]
            attempted = result[1]  # bool
            if not attempted:
                student_questions = get_questions_from_database(attempt_id).to_student_dict(encrypt_answers=True)
            else:
                student_questions = get_questions_from_database(attempt_id).to_student_dict(encrypt_answers=False)
            return jsonify(questions=student_questions, attempt_id=attempt_id, answered=attempted)

    if code_snippet is None or len(code_snippet) == 0:
        code_snippet = get_code_from_previous_submission(student_username, code_runner_previous_question_id)

    # Code is still null so must not have been completed yet
    if code_snippet is None or len(code_snippet) == 0:
        response = jsonify({"description": "NO CODE FOUND"})
        response.status_code = 404
        return response

    student_attempt = save_student_attempt(student_username, code_runner_question_id, code_snippet)
    attempt_id = student_attempt.ID

    data = {
        "question_count": question_count,
        "code_context": code_context,
        "question_topics": question_topics,
        "code_template": code_template,
        "code_langauge": code_language,
        "student_code": code_snippet
    }

    questions = generate_ai_questions(data)
    for question in questions.questions:
        new_question = add_question(student_attempt.ID, question.question, question.answer_option,
                                    question.wrong_options)
        question.update_ID(new_question.ID)
    student_questions = questions.to_student_dict(encrypt_answers=True)
    return jsonify(questions=student_questions, attempt_id=attempt_id, answered=False)


def is_empty(value: str | None) -> bool:
    '''
    checks if the value is None or empty
    :param value: value to check
    :return: boolean of true if empty
    '''
    return value is None or len(value.strip()) == 0


@app.route("/")
def home():
    return render_template("home.html")


@app.route('/saveanswers/<int:id>', methods=['POST'])
def saveanswers(id):
    """
    API to saves the answers to the database. Calculates the answers correct for the questions of that attemptID and stores
    the result in StudentTaskAttempt and updates attempted to `trye`.

    The API body must be:
    `
    [
    {
        "question": {
            "ID": int - ID of the question being answered
        },
        "studentAnswer": str - Answer student has given
    },
    ]
    `
    :param id: The StudentTaskAttempt attemptID of the questions
    :return:
    """

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
    UPDATE `student_task_attempt` SET questionsCorrect = (SELECT COUNT(*) as correct FROM `question` WHERE StudentAnswer = Answer AND attemptID = :attempt_id), attempted = TRUE WHERE ID = :attempt_id; 
    """
    db.session.execute(text(query_questions_correct), {'attempt_id': id});
    # Commit the transaction
    db.session.commit()

    return {'status': 'success'}


def insert_or_update_code(code_runner_question_id, code_runner_student_id, student_username, code_submitted,
                          student_email=None):
    """
    Inserts the code into given by `code_submitted` in the database. Where if the question by
    `code_runner_question_id` and `student_username` already exists then it will be updated
    :param code_runner_question_id: the id of the question from moodle
    :param code_runner_student_id: the id of the student from moodle
    :param student_username: the username of the student
    :param code_submitted: the code that the student has submitted
    :param student_email: the email of the student - not required
    """
    query = text("""
        INSERT INTO student_submitted_code (linkedCodeQuestionID, codeRunnerStudentID, studentUsername, codeSubmitted, studentEmail)
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
    """
    An API to save a students code. The body of the request must contain:
    {
    "crui_username": str - username of the student
    "crui_student_email": str - email of the student
    "crui_student_myplace_id": int - the moodle id of the student
    "crui_question_id": int - the unique id of the question
    "code_snippet": TEXT - The code that is to be saved
    }

    :return:
    """
    data = request.get_json()

    # Extract data from JSON
    student_username = data.get('crui_username')
    student_email = data.get('crui_student_email')
    code_runner_student_id = data.get('crui_student_myplace_id')
    code_runner_question_id = data.get('crui_question_id')
    code_snippet = data.get('code_snippet')

    insert_or_update_code(code_runner_question_id, code_runner_student_id, student_username, code_snippet,
                          student_email)
    return {'status': 'success'}
