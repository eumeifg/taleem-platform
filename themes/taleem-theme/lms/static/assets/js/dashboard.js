$(document).ready(function () {

    
        $("#resend_activation_email").bind("click",function() {
           $("div#container").toggle();
           return false; // prevent propagation
       })
    

    $('#resend_activation_email').click(function(e){

        
       

        $('.loading-block.login-screen-loader').css('display', 'flex')
        var settings = {
            "url": "/api/taleem/re-send-activation-email/",
            "method": "POST",
            "headers": {
              "Content-Type": "application/json"
            },
            "data": JSON.stringify({
                "email": $('#user_email').val()
              }),
          };

          $.ajax(settings).done(function (response) {
            if (response['success'] == true)
            {   var msg = gettext("We have sent activation email again")
                $('#dashboard_activation_email_send_msg').text(msg)
                $('#re_send_activation_email_failure').css('display', 'none')
                $('.loading-block.login-screen-loader').css('display', 'none')
            }
            else
            {
                $('#re_send_activation_email_failure').css('display', '')
                $('.loading-block.login-screen-loader').css('display', 'none')
            }
          })
          .fail(function(response)
            {   if (response.status == 429)
                {   var msg = gettext("Too many retries. Please try after sometime")
                    $('#dashboard_activation_email_send_msg').text(msg)
                }

                else
                {   var msg = gettext("An error occurred. Please try again.")
                    $('#dashboard_activation_email_send_msg').text(msg)
                }

                $('.loading-block.login-screen-loader').css('display', 'none')
    
            }
          )

});


});