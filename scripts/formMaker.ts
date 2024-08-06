import {Question, StudentAnswer} from "./formTypes";
import {Option} from "./databaseTypes";

const url = '/generate_questions';
let currentAttemptID:number | null = null;

$(document).ready(function() {
            $('#crui_check_answers').on("click", function () {
                evaluate_answers();
            });

            $('#crui_generated_question_holder').removeClass("visually-hidden");
            $('#code-form').submit(function(event) {
                event.preventDefault();
                $('#crui_generate_button').prop("disabled", true);
                $('#crui_generated_question_holder').removeClass("visually-hidden");

                const data = {
                    crui_username: $('#crui_username').text(),
                    crui_student_email: $('#crui_student_email').text(),
                    crui_student_myplace_id: $('#crui_student_myplace_id').text(),
                    crui_question_id: $('#crui_question_id').text(),
                    crui_previous_question_id: $('#crui_previous_question_id').text(),
                    code_snippet: $('#codeTextArea').val()
                };
                $.ajax({
                    type: 'POST',
                    url: url,
                    data: data,
                    success: function(response) {
                        $('#crui_generate_button').prop("disabled", true);
                        $('#crui_generated_question_holder').removeClass("visually-hidden");
                        $('#questions').empty();
                        // console.log();
                        const parsedObject = response.questions as Question[];
                        currentAttemptID = response.attempt_id;
                        const answered:boolean = response.answered ?? false;
                        $('#crui_answered').val(answered.toString());
                        $('#crui_attemptID').val(response.attempt_id);
                        if(answered){
                            const studentAnswers:StudentAnswer[] = parsedObject.map(function (question){
                                return {"studentAnswer": question.studentAnswer, "question": question}
                            });
                            studentAnswers.forEach((question, index)=>generate_answer(question, index+1));
                        }else{
                            parsedObject.forEach((question, index)=>generate_question(question, index+1));
                        }
                        //save questions
                        sessionStorage.setItem("crui_questions", JSON.stringify(parsedObject));
                        sessionStorage.setItem("crui_answers", JSON.stringify([]));

                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        $('#questions').empty();
                        $('#crui_generated_question_holder').removeClass("visually-hidden");
                        $('questions').append(
                            `<div class="alert alert-danger d-flex align-items-center" role="alert">

      <div>
        Error Occurred: ${textStatus}
        <br>
        Error Thrown: ${errorThrown}
      </div>
    </div>`
                        )
                    }
                });
            });
        });

export function generate_answer(studentAnswer: StudentAnswer, questionNumber:number){
    const isCorrect = studentAnswer.studentAnswer != null ? studentAnswer.studentAnswer === studentAnswer.question.answer : false;
    $(`#crui_Q${questionNumber}_answer`).val(studentAnswer.question.answer ?? "");
    $(`#crui_Q${questionNumber}_student_answer`).val(studentAnswer.studentAnswer ?? "");
    $(`#crui_Q${questionNumber}_id`).val(studentAnswer.question.ID ?? "")
    $('#questions').append(`<div class="m-3">
        <div class="card ${(isCorrect ? "border-success" : "border-danger")}">
          <div class="card-body">
            <h5 class="card-title">${studentAnswer.question.question}</h5>
            <p class="card-text">
        ${generate_options(studentAnswer.question.options, questionNumber, studentAnswer.question.ID, true, studentAnswer.studentAnswer, true, studentAnswer.question.answer)}
            </p>
                <p class="card-text"><small class="text-body-secondary">
                ${studentAnswer.studentAnswer == "This question doesn't seem right?" ? `You answered: This question doesn\'t seem right? Speak to a lecturer to have them review it.`:
                studentAnswer.studentAnswer != null ? `Your Answer: ${studentAnswer.studentAnswer}` : "You did not answer question!"}
                <br>
                The Answer: ${studentAnswer.question.answer}
                </small></p>
                    <p class="card-text"><small class="text-body-secondary"></small></p>
          </div>
        </div>
      </div>`);
}

export function generate_question(question:Question, questionNumber:number){
    $(`#crui_Q${questionNumber}_answer`).val(question.answer ?? "");
    $(`#crui_Q${questionNumber}_id`).val(question.ID);
    $('#questions').append(`<div class="m-3">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">${question.question}</h5>
            <p class="card-text">
        ${generate_options(question.options, questionNumber, question.ID)}
            </p>
          </div>
        </div>
      </div>`);
    //Have to add later as they have to be created
    //For radio buttons on form
    question.options.forEach(function(option, index){
        $(`#crui_Q${question.ID}_Option${index}`).on("change", function (){runFunction(option, questionNumber, question.ID)});
    })
}

function runFunction(studentAnswerValue:string, questionNumber:number, questionID:number) {
    // Construct the ID using the question number
    const selector = `#crui_Q${questionNumber}_student_answer`;

    // Check if the element exists
    if ($(selector).length > 0) {
        // Update the studentAnswerValue of the input field
        $(selector).val(studentAnswerValue);
        console.log("Updated studentAnswerValue:", studentAnswerValue, "for Question Number:", questionNumber);
    } else {
        console.warn("Element not found with selector:", selector);
    }

}


function generate_options(options: string[], questionNumber:number, questionID:number, disabled=false, selectedOption:null | string = null, correctorwrongSymbol: boolean = false, questionAnswer: string | null = null):string{
    return options.map((option, index) => {
        const checked = selectedOption != null ? (selectedOption == option) : false;
         return `
                <div class="form-check">
                    <input class="form-check-input" type="radio" name="crui_Q${questionID}" id="crui_Q${questionID}_Option${index}" ${disabled ? "disabled" : ""} ${checked ? "checked" : ""}>
                    <label class="form-check-label" for="crui_Q${questionID}_Option${index}">
                        ${option}
                    </label>
                    ${!correctorwrongSymbol ? "" : (checked ? (option == questionAnswer) ? correct_symbol() : wrong_symbol(): "")}
                </div>
            `;
     }).join('');
}

function wrong_symbol(){
    return `<span class="material-symbols-outlined text-danger">
close
</span>`;
}

function correct_symbol(){
    return `<span class="material-symbols-outlined text-success">
check
</span>`;
}

function saveAnswer(studentAnswer:string, questionID:number): void {
    // Retrieve current answers from session storage
    const answers: StudentAnswer[] = JSON.parse(sessionStorage.getItem('crui_answers') || '[]');
    const stupidArray: any = answers;
    // Check if the answer already exists
    let existingAnswerIndex = stupidArray.findIndex((answer:StudentAnswer) => answer.question.ID === questionID)

    if (existingAnswerIndex !== -1) {
        // Update existing answer
        answers[existingAnswerIndex].studentAnswer = studentAnswer;
    } else {
        // Add new answer
        const questions = JSON.parse(sessionStorage.getItem('crui_questions') || '[]');
        const questionIndex = questions.findIndex((question:Question) => question.ID === questionID);

         if(questionIndex !== -1){
             const studentAnswerObject:StudentAnswer = {question: questions[questionIndex], studentAnswer: studentAnswer};
              answers.push(studentAnswerObject);
         }else{
             console.log("No Question found of id:"+questionID);
         }

    }

    // Save back to session storage
    sessionStorage.setItem('crui_answers', JSON.stringify(answers));
}


function evaluate_answers() {
    let answers: StudentAnswer[] = JSON.parse(sessionStorage.getItem('crui_answers') || '[]');
    const questions:Question[] = JSON.parse(sessionStorage.getItem('crui_questions') || '[]');
    //get questions student didnt answer

    const answerIDs = new Set(answers.map(answer => answer.question.ID))
    const nonAnsweredQuestions = questions.filter(question => !answerIDs.has(question.ID));

    const unansweredStudentAnswers:StudentAnswer[] = nonAnsweredQuestions.map(question => {return {question: question, studentAnswer: null}})

    answers.push(...unansweredStudentAnswers);

    //Sort answers by id
    answers = answers.sort((a, b) => a.question.ID - b.question.ID);

    //show results of answers
    $('#questions').empty();
    answers.forEach((studentAnswer, index)=>generate_answer(studentAnswer, index+1));
    console.log(JSON.stringify(answers));
    if(currentAttemptID != null){
            saveStudentAnswersToDB(answers, currentAttemptID);
    }

}

async function saveStudentAnswersToDB(data:StudentAnswer[], attemptID:number) {
  const url = baseURL+'/saveanswers/'+attemptID; // Replace with your URL

  // Define the payload

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    // Check if the response is okay
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const result = await response.json();
    console.log('Response:', result);
  } catch (error) {
    console.error('Error:', error);
  }
  return Promise.resolve();
}