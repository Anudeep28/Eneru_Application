// $(document).ready(function() {
//   $('#send-button').click(function() {
//     //event.preventDefault();
    
//     var userInput = $('#chat-input').val().trim();
    
//     //
//     if (userInput) {
//       addMessage(userInput, true);
//       // console.log("response 2")
//       $('#chat-input').val('');
      
//       $.ajax({
//         type: 'POST',
//         url: '/chatbot/geminiChat/',
//         data: { message: userInput, csrfmiddlewaretoken: $('[name="csrfmiddlewaretoken"]').val() },
//         success: function(data) {
//           if (data.status === 'success') {
//             //addMessage(userInput, True);
//             //$('#chat-input').val('');
//             var response = data.response;
//             addMessage(response, false); // Add only the chatbot's response
//           }
//         },
//         error: function(xhr, status, error) {
//           console.error('Error:', error);
//           addMessage('Sorry, there was an error processing your request.', false);
//         }
//       });
      
//     }
    
//     return false;
//   });
// });

// function addMessage(text, isUser) {
//   var messageElement = $('<div>').addClass('chat-message').addClass(isUser ? 'user' : 'bot').text(text);
//   $('.chat-messages').append(messageElement);
//   $('.chat-messages').scrollTop($('.chat-messages')[0].scrollHeight);
// }

$(document).ready(function() {
  $('#send-button-gemini').click(function() {
    var userInput = $('#chat-input-gemini').val().trim();
    
    if (userInput) {
      addMessage(userInput, true);
      $('#chat-input-gemini').val('');
      
      $.ajax({
        type: 'POST',
        url: '/chatbot/geminiChat/',
        data: { message: userInput, csrfmiddlewaretoken: $('[name="csrfmiddlewaretoken"]').val() },
        success: function(data) {
          if (data.status === 'success') {
            var response = data.response;
            addMessage(response, false);
          }
        },
        error: function(xhr, status, error) {
          console.error('Error:', error);
          addMessage('Sorry, there was an error processing your request.', false);
        }
      });
    }
    
    return false;
  });
});

function addMessage(text, isUser) {
  var messageElement = $('<div>').addClass('chat-message-gemini').addClass(isUser ? 'user' : 'bot').text(text);
  $('.chat-messages-gemini').append(messageElement);
  $('.chat-messages-gemini').scrollTop($('.chat-messages-gemini')[0].scrollHeight);
}