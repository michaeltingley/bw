"""Views related to chat-specific functionality."""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render

from . import pusher_integration
from .models import Conversation, Message

@login_required(login_url='/chat/login/')
def index(request):
    """Renders the basic chat template."""
    return render(request, 'chat/index.html')

@login_required(login_url='/chat/login/')
def get_conversations(request):
    """REST endpoint to get a user's conversations.

    Request should be an empty POST request.

    Returns:
        JsonResponse. Contains a single key, 'conversations', listing the
        conversations for which the user is a participant. Conversations are
        listed from most recent to least recent interaction. Each element of the
        list is formatted according to Conversation.as_dict.
    """
    return JsonResponse({
        'conversations': [
            conversation.as_dict()
            for conversation in request
                .user
                .participant
                .conversation_set
                .prefetch_related('participants', 'message_set')
                .annotate(last_message_timestamp=Max('message__timestamp'))
                .order_by('-last_message_timestamp')
            # Only return conversations with at least a single message
            if conversation.last_message_timestamp
        ]
    })

def find_users(request):
    """REST endpoint to list users in the database.

    Args:
        POST['email_prefix'] (str): The email prefix to search for.

    Returns:
        JsonResponse. Contains a single key, emails, which contains an array of
        emails with the specified prefix.
    """
    prefix = request.POST['email_prefix']
    if not prefix:
        return JsonResponse({'emails': []})
    return JsonResponse({
        'emails': [
            user.username
            for user in User.objects.filter(username__startswith=prefix)
        ]
    })

@login_required(login_url='/chat/login/')
def get_messages(request):
    """REST endpoint to list messages within one of the user's conversations.

    If the conversation between the current user and the specified email does
    not yet exist, this method will create it.

    Args:
        POST['email'] (str): The email for which to get one-on-one
            conversations with the current user.

    Returns:
        JsonResponse. Contains a single key, messages, which contains an array
        of messages in the conversations. Messages are formatted according to
        Messages.as_dict.
    """
    remote_email = request.POST['email']
    shared_conversation = get_conversation(request.user, remote_email)

    if not shared_conversation:
        # Create the new conversation
        shared_conversation = Conversation.objects.create()
        shared_conversation.participants.add(request.user.participant)
        shared_conversation.participants.add(
            User.objects.get(username=remote_email).participant
        )
        shared_conversation.save()

    return JsonResponse({
        'messages': [
            message.as_dict()
            for message in shared_conversation.message_set.all()
        ],
    })

@login_required(login_url='/chat/login/')
def post_message(request):
    """REST endpoint to post a message to a conversation.

    Via Pusher, notifies participants that a new message has been posted.

    Args:
        POST['email'] (str): The email to send the message to. Specifically, the
            new message will be posted to the one-on-one conversation between
            the current user and the user whose email equals this argument.
        POST['message_text'] (str): The text that the posted message should
            contain.

    Returns:
        JsonResponse. Empty.
    """
    shared_conversation = get_conversation(request.user, request.POST['email'])

    if not shared_conversation:
        return HttpResponseBadRequest(
            "Conversation not specified or does not exist"
        )

    message_text = request.POST['message_text']

    if not message_text:
        return HttpResponseBadRequest("Must specify message")

    Message.objects.create(
        conversation=shared_conversation,
        participant=request.user.participant,
        text=message_text,
    )

    for participant in shared_conversation.participants.all():
        pusher_integration.notify_conversation_updated(
            participant.user,
            shared_conversation
        )
    return JsonResponse({})

def get_conversation(user, remote_email):
    """Looks up and returns the conversation between the user and remote email.

    Args:
        user (User): The current user.
        remote_email (str): Email of the other participant.

    Returns:
        Conversation. The one-on-one conversation between user and the
        participant that is identified by the specified remote email; or None if
        no such conversation exists.
    """
    shared_conversations = [
        user_conversation
        for user_conversation in user
            .participant
            .conversation_set
            .all()
            .prefetch_related('participants')
        if set(
                participant.user.username
                for participant in user_conversation.participants.all()
            ) == set([user.username, remote_email])
    ]
    if len(shared_conversations) > 0:
        # There will be at most one found conversation, so return it
        return shared_conversations[0]
    return None
