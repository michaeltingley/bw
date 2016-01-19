var pusher = new Pusher('f4e32bbd2ddcdaa5e41f', { authEndpoint: '/chat/pusher_auth/' });
var USER_META_REFERENCE = "You"

var currentConversationEmail;

function messageToHtml(message) {
  var isUserMe = message.email == USER_EMAIL;
  return $('<li />', {
    class: (isUserMe ? "message-outgoing" : "message-incoming"),
    html: [
      $('<span />', {
        class: 'bubble panel '
          + (isUserMe ? "bubble-outgoing" : "bubble-incoming"),
        html: message.body
      }),
      $('<br>'),
      $('<span />', {
        class: 'bubble-details',
        html: (isUserMe ? USER_META_REFERENCE : message.email)
          + " &#8226; " + message.timestamp
      })
    ]
  });
}

function createSetActiveConversationFunction(email) {
  return function() {
    $.ajax({
      type: 'POST',
      url: '/chat/get_messages/',
      data: {
        'csrfmiddlewaretoken': CSRF_TOKEN,
        'email': email,
      },
      success: function(response) {
        location.hash = email
        $('.conversation-selected').removeClass('conversation-selected');

        currentConversationEmail = email;

        $('#' + getConversationId(currentConversationEmail)).addClass('conversation-selected');
        $('#page_header').text(currentConversationEmail);
        $('#chat_messages').empty().append($.map(response.messages, messageToHtml));
        $('#email_prefix').val('');
        $('#found_users').empty();
        $('#chat_pane').show();
        $('#chat_title').text('Chat with ' + email);
        $('#post_message')
            .unbind()
            .submit(function(event) {
                event.preventDefault();
                $.ajax({
                    type: 'POST',
                    url: '/chat/post_message/',
                    data: {
                      'csrfmiddlewaretoken': CSRF_TOKEN,
                      'email': email,
                      'message_text': $('#message_text').val(),
                    },
                });
                $('#message_text').val('');
            });
        window.scrollTo(0,document.body.scrollHeight);
      }
    });
  };
}

function getRecipientEmailFromConversation(conversation) {
  participant_email = conversation.participant_emails.find(function(email) {
    return email != USER_EMAIL;
  });
  return participant_email ? participant_email : USER_EMAIL;
}

function getConversationId(participantEmail) {
  return 'conversation-' + participantEmail.replace(/\W+/g, "_");
}

function renderConversation(conversation) {
  participantEmail = getRecipientEmailFromConversation(conversation);
  return $('<tr />', {
    id: getConversationId(participantEmail),
    click: createSetActiveConversationFunction(participantEmail),
    class: currentConversationEmail == participantEmail ? 'conversation-selected' : '',
    html: $('<div />', {
        class: 'conversation-entry',
        html: [
            $('<span />', {
                class: 'conversation-email',
                html: participantEmail,
            }),
            $('<span />', {
                class: 'conversation-timestamp',
                html: conversation.last_message.timestamp,
            }),
            $('<br />'),
            $('<span />', {
                class: 'conversation-snippet',
                html: (conversation.last_message.email == USER_EMAIL ? USER_META_REFERENCE + ": " : "")
                    + conversation.last_message.body,
            }),
        ],
    }),
  });
}

$(function() {
  $('#email_prefix').typeahead({
    source: function(query, process) {
      $.ajax({
        type: 'POST',
        url: '/chat/find_users/',
        data: {
          'csrfmiddlewaretoken': CSRF_TOKEN,
          'email_prefix': query,
        },
        success: function(response) {
          process(response.emails);
        }
      });
    },
    afterSelect: function(email) {
      createSetActiveConversationFunction(email)();
    },
  });
  $.ajax({
    type: 'POST',
    url: '/chat/get_conversations/',
    data: {
      'csrfmiddlewaretoken': CSRF_TOKEN,
    },
    success: function(response) {
      $('#conversations').html($.map(response.conversations, renderConversation));
    }
  });
  pusher
      .subscribe('private-participant-' + USER_EMAIL)
      .bind('conversation updated', function(conversation) {
        participantEmail = getRecipientEmailFromConversation(conversation);
        $('#' + getConversationId(participantEmail)).remove();
        $('#conversations').prepend(renderConversation(conversation));
        if (participantEmail == currentConversationEmail) {
          $('#chat_messages').append(messageToHtml(conversation.last_message));
          window.scrollTo(0, document.body.scrollHeight);
        }
      });
  if (location.hash) {
    createSetActiveConversationFunction(location.hash.substring(1))();
  }
});
