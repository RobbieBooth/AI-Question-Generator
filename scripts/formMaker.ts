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
                    url: '/generate_questions',
                    data: $(this).serialize(),
                    success: function(response) {
                        $('#questions').empty();
                        // console.log();
                        const parsedObject = JSON.parse(response.questions)  as Question[];
                        console.log(parsedObject);
                        parsedObject.forEach(generate_question);
                    }
                });
            });
        });

function generate_question(question:Question){
    $('#questions').append(`<div class="m-3">
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">${question.question}</h5>
            <p class="card-text">
        ${generate_options(question.options)}
            </p>
          </div>
        </div>
      </div>`);
}

function generate_options(options: Option[]):string{
    return options.map(option => {
         return `
                <div class="form-check">
                    <input class="form-check-input" type="radio" name="${option.questionID}" id="${option.ID}">
                    <label class="form-check-label" for="${option.ID}">
                        ${option.option}
                    </label>
                </div>
            `;
     }).join('');
}