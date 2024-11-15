
---

# AutoMCQ: Automatic Multi-Choice Question Generation Using GPT-4o Mini

Welcome to the repository for **AutoMCQ**, a research internship project that leverages OpenAI's GPT-4o Mini model to generate multiple-choice questions based on student code submissions, specific question counts, and contextual understanding of the code.

## Overview

The goal of this project is to enhance educational tools by automating the creation of multiple-choice questions (MCQs) tailored to students' programming submissions. These questions can help assess understanding, provide feedback, and encourage critical thinking about their code.

This tool is specifically designed for integration with **Moodle**, a popular Learning Management System (LMS), and the **CodeRunner** Moodle plugin. **AutoMCQ** is programming language-agnostic, making it adaptable to various coding environments.

For more details, view the [academic poster](https://robbiebooth.com/portfolio/ai-question-generation/academic_poster.pdf).

---

## How It Works: Question Generation Process

The question generation is handled by an API endpoint that processes student code, Moodle metadata, and contextual information to produce MCQs. Below is the structure and explanation of the API request:

### API Endpoint

**Route**: `/generate_questions`  
**Method**: `POST`

### API Request Body

```
The API body should look like:
{
"crui_username": Students unique username,
"crui_student_email": studuents email address,
"crui_student_myplace_id": the students moodle id,
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
```

---

### Example Request

```json
{
  "crui_username": "johnDoe@strath.ac.uk",
  "crui_student_email": "john.doe.2024@uni.strath.ac.uk",
  "crui_student_myplace_id": 200102,
  "crui_question_id": 3032891,
  "crui_previous_question_id": 5,
  "code_snippet": "",
  "question_topics": "fields, constructors, accessors, mutators, print, equals and if statements",
  "code_context": "",
  "question_count": 4,
  "generation_mode": ""
}

```

In the example above the code would have been submitted through the code runner question before and the generation is being completed now.

### Example Response

```json
{
  "answered": false,
  "attempt_id": 39,
  "questions": [
    {
      "ID": 10,
      "answer": "private",
      "options": [
        "static",
        "protected",
        "public",
        "private",
        "This question doesn't seem right?"
      ],
      "question": "What keyword is used to denote that the fields in the Book class are private?",
      "studentAnswer": null
    },
    {
      "ID": 11,
      "answer": "The constructor will not compile due to a missing parameter.",
      "options": [
        "The constructor will not compile due to a missing parameter.",
        "It will default to 0.",
        "The pages field will be set to null.",
        "The class will use the previous pages value.",
        "This question doesn't seem right?"
      ],
      "question": "In the constructor for the Book class, what happens if the parameter `bookPages` is not provided?",
      "studentAnswer": null
    },
    {
      "ID": 12,
      "answer": "To ensure the reference number is valid and meets minimum length requirements.",
      "options": [
        "To automatically format the reference number.",
        "To ensure the reference number is valid and meets minimum length requirements.",
        "To prevent users from setting any reference number at all.",
        "To log every reference number update.",
        "This question doesn't seem right?"
      ],
      "question": "Why is there a conditional check for the length of the reference number in the `setRefNumber` method?",
      "studentAnswer": null
    },
    {
      "ID": 13,
      "answer": "It prints &quot;Ref Number: zzz&quot;",
      "options": [
        "It will throw an error.",
        "It prints &quot;Ref Number: zzz&quot;",
        "It prints &quot;Ref Number: null&quot;",
        "It prints &quot;Ref Number: &quot; without any value.",
        "This question doesn't seem right?"
      ],
      "question": "In the `printDetails` method, how is the output displayed if `refNumber` is an empty string?",
      "studentAnswer": null
    }
  ]
}

```

---

## Key Features

- **Dynamic Question Generation**: Automatically generate MCQs based on the provided student code.
- **Customizable Context**: Incorporates the context of the code to ensure questions are relevant and meaningful.
- **Flexible Question Count**: Allows users to specify the number of questions to be generated per session.
- **Programming Language Agnostic**: Supports code written in Python, Java, C++, and more.
- **Moodle Integration**: Designed to work seamlessly with the **CodeRunner Moodle Plugin**.
- **AI-Powered Insights**: Utilizes OpenAI’s GPT-4o Mini for accurate and creative question creation.

---

## Project Funding & Supervision

This project was funded by the **Research Interns at Strathclyde** program and was completed at **Strathclyde University**.

Supervised by:
- **Dr. Martin Goodfellow**
- **Mr. Andrew Fagan**
- **Mr. Alasdair Lambert**

---

For more information about the research, view the [academic poster](https://robbiebooth.com/portfolio/ai-question-generation/academic_poster.pdf).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Citation

If you use **AutoMCQ** in your research or paper, please cite it as follows in your LaTeX document:

```latex
@misc{booth2024automcq,
  author = {Booth, Robbie and Goodfellow, Martin and Fagan, Andrew and Lambert, Alasdair},
  title = {AutoMCQ: Automatic Multi-Choice Question Generation Using GPT-4o Mini},
  year = {2024},
  howpublished = {\url{https://github.com/RobbieBooth/AI-Question-Generator}},
  note = {Unpublished work, accessed: 2024-11-15},
  keywords = {auto-grading, AI, GPT-4o-mini, Moodle, CodeRunner, education},
}

```

---
