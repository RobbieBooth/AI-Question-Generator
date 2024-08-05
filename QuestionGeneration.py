import json

from openai import OpenAI
from dotenv import find_dotenv, load_dotenv
from os import environ as env
import random

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

client = OpenAI(
    api_key=env.get("OPENAI_API_KEY")
)


# completion = client.chat.completions.create(
#     model="gpt-4o-mini",
#     response_format={"type": "json_object"},
#     messages=[
#         {"role": "system",
#          "content": '''You are an educational assistant specializing in computer science. Your task is to analyse students' code for the beginner programmer class and generate thoughtful multiple-choice questions that can help them understand and improve their coding skills. You should try and make good distractor options to really test students understanding.
#
# You should create 8 questions, the language the user used is Java and they may tell you what methods or parts they want to assess.
#
# Some type of potential questions topics could be:
# -Parameter Names
# -Variable Names
# -Loop End
# -Variable Declaration
# -Variable role – i.e: Which of the following best describes the role of variable <Variable>
# -Line Purpose
# -Loop Count
# -Variable Trace
#
# You should create questions using the topics that you believe are appropriate for the students’ code given.
#
# The questions should be in a json format like:
# [
# {
# 	“question”: string,
# 	“answerOption”: string,
# 	“wrongOptions”: string[],
# },
# ...
# ]
# '''},
#         {"role": "user", "content":
#          '''
#          private BasicAccount findAcc(int n) {
# 		for (BasicAccount acc : accounts) {
# 			if (acc.getAccNumber() == n)
# 				return acc;
# 		}
# 		return null;
# 	}
#
#          '''
#          }
#     ]
# )

class Question:
    def __init__(self, question: str, answer_option: str, wrong_options, ID=None, student_answer=None):
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

    def to_student_dict(self):
        # randomise option order
        options = self.wrong_options
        options.append(self.answer_option)
        random.shuffle(options)
        options.append("This question doesn't seem right?")
        return {
            "ID": self.ID,
            "question": self.question,
            "options": options,
            "answer": self.answer_option,
            "studentAnswer": self.student_answer
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

    def to_student_dict(self):
        self.questions.sort(key=lambda question: question.get_ID())
        student_questions = [question.to_student_dict() for question in self.questions]
        return student_questions


def from_dict(data):
    questions = [Question(q['question'], q['answerOption'], q['wrongOptions']) for q in data['questions']]
    return Question_Bank(questions)


def from_dict_with_id(data):
    questions = [Question(q['question'], q['answerOption'], q['wrongOptions'], q['id']) for q in data['questions']]
    return Question_Bank(questions)


sample = '''{
	"questions": [
		{
			"question": "What is the role of the variable 'sum' in the provided code?",
			"answerOption": "It stores the result of adding 'first' and 'second'.",
			"wrongOptions": [
				"It holds the first number to be added.",
				"It is used to iterate through a loop.",
				"It keeps track of the number of additions performed."
			]
		},
		{
			"question": "What will be printed when the provided code is executed?",
			"answerOption": "10 + 20 = 30",
			"wrongOptions": [
				"10 + 20 = 20",
				"First number: 10, Second number: 20",
				"The sum is: 30"
			]
		},
		{
			"question": "In the line 'int sum = first + second;', which operation is being performed?",
			"answerOption": "Addition of two integers.",
			"wrongOptions": [
				"Subtraction of two integers.",
				"Multiplication of two integers.",
				"Division of two integers."
			]
		},
		{
			"question": "What is the purpose of the line 'int second = 20;'?",
			"answerOption": "To declare and initialize the variable 'second' with the value 20.",
			"wrongOptions": [
				"To change the value of 'first' to 20.",
				"To initialize 'second' with the value of 'first'.",
				"To declare a loop variable with an initial value of 20."
			]
		},
		{
			"question": "What does the 'System.out.println' statement do in this code?",
			"answerOption": "It prints the sum of first and second to the console.",
			"wrongOptions": [
				"It adds the two numbers together in the console.",
				"It declares a new variable in the program.",
				"It evaluates an expression without displaying any output."
			]
		},
		{
			"question": "How many variables are declared in this code snippet?",
			"answerOption": "Three variables.",
			"wrongOptions": [
				"Two variables.",
				"Four variables.",
				"One variable."
			]
		},
		{
			"question": "Which of the following is a valid name for a variable in Java?",
			"answerOption": "totalSum",
			"wrongOptions": [
				"2ndNumber",
				"first-name",
				"sum total"
			]
		},
		{
			"question": "What will be the value of 'first' after the execution of the code?",
			"answerOption": "10",
			"wrongOptions": [
				"20",
				"30",
				"0"
			]
		}
	]
}'''


def generate_ai_questions(user_data):
    # Convert data to a JSON string
    user_prompt = json.dumps(user_data, indent=2)
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system",
             "content": '''
             You are an educational assistant specializing in computer science. Your task is to analyse students' code for the beginner programmer class and 
             generate thoughtful multiple-choice questions that can help them understand and improve their coding skills. 
             You should try and make good distractor options to really test students understanding.

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
    # print(completion.choices[0].message.content)

    data = json.loads(completion.choices[0].message.content)
    # data = json.loads(sample)
    quiz = from_dict(data)

    return quiz

# print(completion.choices[0].message)
#
# print(completion.choices[0].message.content)
