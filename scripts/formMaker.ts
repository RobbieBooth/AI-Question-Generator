import {Question, StudentAnswer} from "./formTypes";
import {Option} from "./databaseTypes";

const url = '/generate_questions';
let currentAttemptID:number | null = null;

$(document).ready(function() {
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

