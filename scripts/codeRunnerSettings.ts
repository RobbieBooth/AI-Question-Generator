import {Question, StudentAnswer} from "./formTypes";
import {generate_answer, generate_question} from "./formMaker.js";


//request questions to be generated on page load
let url:string;
let currentAttemptID:number | null = null;
$(document).ready(function() {
    url = $('#crui_server_host_url').text()+'generate_questions';
    const data = {
                    crui_username: $('#crui_username').text(),
                    crui_student_email: $('#crui_student_email').text(),
                    crui_student_myplace_id: $('#crui_student_myplace_id').text(),
                    crui_question_id: $('#crui_question_id').text(),
                    crui_previous_question_id: $('#crui_previous_question_id').text(),
                    code_snippet: null,
                    question_topics: $('#crui_question_topics').text(),
                    code_context: $('#crui_code_context').text(),
                    question_count: $('#crui_question_count').text(),
                    generation_mode: $('#crui_generation_mode').text(),
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