import {Question} from "./formTypes";
import {Option} from "./databaseTypes";

// document.getElementById('#code-form').addEventListener("submit", function(event){
//   event.preventDefault()
//     $.ajax({
//                     type: 'POST',
//                     url: '/generate_questions',
//                     data: $(this).serialize(),
//                     success: function(response) {
//                         $('#questions').empty();
//                         response.questions.forEach(generate_question);
//                     }
//                 });
// });
$(document).ready(function() {
            $('#code-form').submit(function(event) {
                event.preventDefault();
$.ajax({
                    type: 'POST',
                    url: 'https://devweb2023.cis.strath.ac.uk/xbb21163-python/generate_questions',
                    data: $(this).serialize(),
                    success: function(response) {
                        $('#questions').empty();
                        // console.log();
                        const parsedObject = JSON.parse(response.questions)  as Question[];
                        console.log(parsedObject);
                        parsedObject.forEach((question, index)=>generate_question(question, index+1));
                    }
                });
            });
        });

function generate_question(question:Question, questionNumber:number){
    $(`#crui_Q${questionNumber}_answer`).val(question.answer)
    $('#questions').append(`<div class="m-3">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">${question.question}</h5>
            <p class="card-text">
        ${generate_options(question.options, questionNumber)}
            </p>
          </div>
        </div>
      </div>`);
}

function runFunction(value, questionNumber) {
    // Construct the ID using the question number
    const selector = `#crui_Q${questionNumber}_student_answer`;
    console.log("Selector:", selector);

    // Check if the element exists
    if ($(selector).length > 0) {
        // Update the value of the input field
        $(selector).val(value);
        console.log("Updated value:", value, "for Question Number:", questionNumber);
    } else {
        console.warn("Element not found with selector:", selector);
    }
}


//TODO may be errors due to replace for backticks and double quotes etc
function generate_options(options: Option[], questionNumber):string{
    return options.map((option, index) => {
         return `
                <div class="form-check">
                    <input class="form-check-input" type="radio" name="crui_Q${option.questionID}" id="crui_Q${option.questionID}_Option${option.ID}" onchange="runFunction('${option.option.replace(/'/g, "\\'")}',${questionNumber})">
                    <label class="form-check-label" for="crui_Q${option.questionID}_Option${option.ID}">
                        ${option.option}
                    </label>
                </div>
            `;
     }).join('');
}