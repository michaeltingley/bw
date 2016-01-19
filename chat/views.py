from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View

from pusher import Pusher

from .models import Conversation, Message, Participant

# TODO: Move this
pusher = Pusher(
    app_id=u'165329',
    key=u'f4e32bbd2ddcdaa5e41f',
    secret=u'6f6744195b7b081c20c0'
)

class AboutView(TemplateView):
    template_name = "chat/about.html"

@login_required(login_url='/chat/login/')
def index(request):
    return render(request, 'chat/index.html')

@login_required(login_url='/chat/login/')
def get_conversations(request):
    return JsonResponse({
        'conversations': get_ordered_conversation_data(request.user)
    })

def get_ordered_conversation_data(user):
    return [
        conversation.as_dict()
        for conversation
        in user
            .participant
            .conversation_set
            .prefetch_related('participants', 'message_set')
            .annotate(last_message_timestamp=Max('message__timestamp'))
            .order_by('-last_message_timestamp')
        if conversation.last_message_timestamp
    ]

def login(request):
    print request.GET
    return render(request, 'chat/login.html')

class LoginView(View):

    def get(self, request, *args, **kwargs):
        return render(request, 'chat/login.html')

    def post(self, request, *args, **kwargs):
        email = request.POST['email']
        if not email:
            return login_failed(request, 'Email must not be blank.')

        password = request.POST['password']
        if not email:
            return login_failed(request, 'Password must not be blank.')

        if 'sign_up' in request.POST:
            if User.objects.filter(username=email).exists():
                return login_failed(
                    request,
                    "The provided email already exists. Try logging in."
                )
            created_user = User.objects.create_user(
                username=email,
                password=password
            )
            Participant.objects.create(user=created_user)
        user = auth.authenticate(username=email, password=password)
        if user is None:
            return login_failed(
                request,
                "Your email and password didn't match. Please try again."
            )
        auth.login(request, user)
        return HttpResponseRedirect(reverse('chat:index'))

def login_failed(request, error):
    return render(request, 'chat/login.html', {'error': error})

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('chat:index'))

def find_users(request):
    prefix = request.POST['email_prefix']
    if not prefix:
       return JsonResponse({'emails': []})
    return JsonResponse({
        'emails': [user.username for user in User.objects.filter(username__startswith=prefix)]
    })

@login_required(login_url='/chat/login/')
def get_messages(request):
    remote_email = request.POST['email']
    shared_conversation = get_conversation_with_remote_email(request.user, remote_email)
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
    remote_email = request.POST['email']
    shared_conversation = get_conversation_with_remote_email(
        request.user,
        remote_email
    )

    if not shared_conversation:
        return HttpResponseBadRequest(
            "Conversation not specified or does not exist"
        )

    message_text = request.POST['message_text']

    if not message_text:
        return HttpResponseBadRequest("Must specify message")

    message = Message.objects.create(
        conversation=shared_conversation,
        participant=request.user.participant,
        text=message_text,
    )

    for participant in shared_conversation.participants.all():
        pusher.trigger(
            'private-participant-' + participant.user.username,
            'conversation updated',
            shared_conversation.as_dict()
        )
    return JsonResponse({})

@login_required(login_url='/chat/login/')
@csrf_exempt
def pusher_auth(request):
    (_, resource, resource_id) = request.POST['channel_name'].split('-')

    if (resource == 'participant'
            and not request.user.username == resource_id):
        return HttpResponseBadRequest(
            'User not permitted to subscribe to participant updates'
        )

    return JsonResponse(pusher.authenticate(
        channel=request.POST['channel_name'],
        socket_id=request.POST['socket_id'],
    ))

def get_conversation_with_remote_email(user, remote_email):
    shared_conversations = [
        user_conversation
        for user_conversation in user.participant.conversation_set.all().prefetch_related('participants')
        if (set([participant.user.username for participant in user_conversation.participants.all()]) ==
            set([user.username, remote_email]))
    ]
    if len(shared_conversations) > 0:
        # TODO: This should never happen; once I've finalized the project, I should enforce this
        return shared_conversations[0]
    return None
