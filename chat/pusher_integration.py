"""Contains functionality for interfacing with the Pusher module."""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from pusher import Pusher

PUSHER = Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET
)

def notify_conversation_updated(user, conversation):
    """Notifies provided user's channel that the conversation was updated

    Args:
        user (User): The user that should be notified.
        conversation (Conversation): The conversation that has been updated.
    """
    PUSHER.trigger(
        'private-participant-' + user.username,
        'conversation updated',
        conversation.as_dict()
    )

@login_required(login_url='/chat/login/')
@csrf_exempt
def authenticate(request):
    """Authenticates using Pusher.

    Args:
        POST['channel_name'] (str): The channel the user is trying to subscribe
            to.
        POST['socket_id'] (str): The socket the subscription is being made to.
    """
    (_, resource, resource_id) = request.POST['channel_name'].split('-')

    if (resource == 'participant'
            and not request.user.username == resource_id):
        return HttpResponseBadRequest(
            'User not permitted to subscribe to participant updates'
        )

    return JsonResponse(PUSHER.authenticate(
        channel=request.POST['channel_name'],
        socket_id=request.POST['socket_id']
    ))
