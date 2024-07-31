import {Question, StudentAnswer} from "./formTypes";
import {generate_answer, generate_question} from "./formMaker.js";


// const baseURL = "http://127.0.0.1:5000";
const url = 'https://devweb2023.cis.strath.ac.uk/xbb21163-python/generate_questions';
let currentAttemptID:number | null = null;
$(document).ready(function() {
    const data = {
                    crui_username: $('#crui_username').text(),
                    crui_student_email: $('#crui_student_email').text(),
                    crui_student_myplace_id: $('#crui_student_myplace_id').text(),
                    crui_question_id: $('#crui_question_id').text(),
                    crui_previous_question_id: $('#crui_previous_question_id').text(),
                    code_snippet: null
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
                        $('#crui_attemptID').val(response.attempt_id);
                        const answered:boolean = response.answered ?? false;
                        $('#crui_answered').val(answered.toString());

                        if(answered){
                            const studentAnswers:StudentAnswer[] = parsedObject.map(function (question){
                                return {"studentAnswer": question.studentAnswer, "question": question}
                            });
                            studentAnswers.forEach((question, index)=>{
                                generate_answer(question, index+1);

                            });
                        }else{
                            parsedObject.forEach((question, index)=>generate_question(question, index+1));
                        }
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        $('#crui_generated_question_holder').removeClass("visually-hidden");
                        $('#questions').empty();
                        if (jqXHR.status === 404 && jqXHR.responseJSON && jqXHR.responseJSON.description === "NO CODE FOUND") {

                            $('#questions').append(
                            `<div class="alert alert-danger d-flex align-items-center" role="alert">

      <div>
        An Error Occurred: It seems that no code has been submitted for the previous task. 
        <br>
        If you have, please speak to your lecturer! You may also want to mention these values:
        <br>
        Previous Question Code: ${$('#crui_previous_question_id').text()}
        <br>
        Current Question Code: ${$('#crui_question_id').text()}
      </div>
    </div>`
                        );
                        }else{

                        $('#questions').append(
                            `<div class="alert alert-danger d-flex align-items-center" role="alert">

      <div>
        Error Occurred: ${textStatus}
        <br>
        Error Thrown: ${errorThrown}
      </div>
    </div>`);
                        }
                    }
                });
});