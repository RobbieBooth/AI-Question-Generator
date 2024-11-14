import json
import re

from openai import OpenAI
from dotenv import find_dotenv, load_dotenv
from os import environ as env
import random

from answerEncryption import encrypt_data

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

client = OpenAI(
    api_key=env.get("OPENAI_API_KEY")
)


class Question:
    def __init__(self, question: str, answer_option: str, wrong_options:list[str], ID=None, student_answer=None):
        self.question = question
        self.answer_option = answer_option
        self.wrong_options = wrong_options
        self.ID = ID
        self.student_answer = student_answer

    def __repr__(self):
        return f"Question(question={self.question}, answer_option={self.answer_option}, wrong_options={self.wrong_options})"

    def to_dict(self):
        return {
            "question": self.question,
            "answerOption": self.answer_option,
            "wrongOptions": self.wrong_options
        }

    def update_ID(self, ID):
        self.ID = ID

    def get_ID(self):
        return self.ID

    def to_student_dict(self, encrypt_answer: bool = False):
        """
        Converts the question to JSON object and randomises the order of the options.
        :param encrypt_answer: a bool whether to encrypt the answer
        :return: a JSON object of the question
        """
        # randomise option order
        # options = self.wrong_options
        # options.append(self.answer_option)
        options = [sanitize(opt) for opt in self.wrong_options]  # Sanitize wrong options
        options.append(sanitize(self.answer_option))  # Sanitize and add answer option

        random.shuffle(options)
        options.append("This question doesn't seem right?")

        if not encrypt_answer:
            answer = sanitize(self.answer_option)
        else:
            answer = encrypt_data(sanitize(self.answer_option))

        # Student Answer
        if self.student_answer is None:
            student_answer = None
        else:
            student_answer = sanitize(self.student_answer)

        return {
            "ID": self.ID,
            "question": sanitize(self.question),
            "options": options,
            "answer": answer,
            "studentAnswer": student_answer
        }

    def to_student_dict_unsanitised(self, encrypt_answer: bool = False):
        """
        Converts the question to JSON object and randomises the order of the options.
        THIS IS ONLY FOR SUMMARY PAGE TO FIX SANITISED DISPLAY ERROR
        :param encrypt_answer: a bool whether to encrypt the answer
        :return: a JSON object of the question
        """
        # randomise option order
        # options = self.wrong_options
        # options.append(self.answer_option)
        options = [desanitize(opt) for opt in self.wrong_options]
        options.append(desanitize(self.answer_option))  # Sanitize and add answer option

        random.shuffle(options)
        options.append("This question doesn't seem right?")

        if not encrypt_answer:
            answer = desanitize(self.answer_option)
        else:
            answer = encrypt_data(desanitize(self.answer_option))

        # Student Answer
        if self.student_answer is None:
            student_answer = None
        else:
            student_answer = desanitize(self.student_answer)

        return {
            "ID": self.ID,
            "question": desanitize(self.question),
            "options": options,
            "answer": answer,
            "studentAnswer": student_answer
        }


class Question_Bank:
    def __init__(self, questions: list[Question]):
        self.questions = questions

    def __repr__(self):
        return f"Quiz(questions={self.questions})"

    def to_dict(self):
        return {
            "questions": [question.to_dict() for question in self.questions]
        }

    def to_student_dict(self, encrypt_answers: bool = False):
        """
        Sorts the questions by ID and converts them into JSON data
        :param encrypt_answers: bool to determine whether to encrypt the answers of the JSON
        :return: A JSON array containing all the questions
        """
        self.questions.sort(key=lambda question: question.get_ID())
        student_questions = [question.to_student_dict(encrypt_answers) for question in self.questions]
        return student_questions

    def to_student_dict_unsanitised(self, encrypt_answers: bool = False):
        """
        Sorts the questions by ID and converts them into JSON data
        THIS IS ONLY FOR SUMMARY PAGE TO FIX SANITISED DISPLAY ERROR
        :param encrypt_answers: bool to determine whether to encrypt the answers of the JSON
        :return: A JSON array containing all the questions
        """
        self.questions.sort(key=lambda question: question.get_ID())
        student_questions = [question.to_student_dict_unsanitised(encrypt_answers) for question in self.questions]
        return student_questions


def from_dict(data):
    questions = [Question(q['question'], q['answerOption'], q['wrongOptions']) for q in data['questions']]
    return Question_Bank(questions)


def from_dict_with_id(data):
    questions = [Question(q['question'], q['answerOption'], q['wrongOptions'], q['id']) for q in data['questions']]
    return Question_Bank(questions)


def sanitize(string: str) -> str:
    char_map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;',
        '/': '&#x2F;',
    }

    pattern = re.compile(r'[&<>"\'/]')

    return pattern.sub(lambda match: char_map[match.group(0)], string)

import re

def desanitize(string: str) -> str:
    reverse_char_map = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#x27;': "'",
        '&#x2F;': '/',
    }

    pattern = re.compile(r'&amp;|&lt;|&gt;|&quot;|&#x27;|&#x2F;')

    return pattern.sub(lambda match: reverse_char_map[match.group(0)], string)


def generate_ai_questions(user_data) -> Question_Bank:
    """
    Uses Artificial Intelligence (AI) to generate questions
    :param user_data: A JSON object containing information that can influence the way questions are generated:
    {
        "question_count": int - the number of questions that should be generated,
        "code_context": str | None - context to the task or student_code,
        "question_topics": Comma seperated str | None - the topics for the AI to generate questions on,
        "code_template": str | None - the initial code that the student was provided,
        "code_langauge": str - the programming langauge that has been used,
        "student_code": str - the student's final code.
    }
    :return: A bank of the questions that were generated by the AI
    """
    # Convert data to a JSON string
    user_prompt = json.dumps(user_data, indent=2)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system",
             "content": '''You are an educational assistant specializing in computer science. Your task is to analyse 
             students' code for the beginner programmer class and generate thoughtful multiple-choice questions that 
             can help them understand and improve their coding skills. You should try and make good distractor 
             options to really test students understanding.

    The student will provide a json with the following:
    How many questions they want under "question_count",
    Which topics they want to be assessed on by "question_topics",
    "code_context" telling you details about their code,
    You should only assess students on code that has been modified from "code_template",
    "student_code" is the students code that has been modified,
    "code_language" is the language that the student has used
    
    The questions should have 4 options.

    You should create questions using the topics that you believe are appropriate for the students’ code given.

    The questions should be in a json format like:
    [
    {
    	“question”: string,
    	“answerOption”: string,
    	“wrongOptions”: string[],
    },
    ...
    ]
    '''},
            {"role": "user", "content": user_prompt
             }
        ]
    )

    data = json.loads(completion.choices[0].message.content)

    quiz = from_dict(data)  # load returned json questions to python objects

    return quiz
