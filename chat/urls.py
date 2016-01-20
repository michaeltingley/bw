from django.conf.urls import url

from . import auth_views, chat_views, pusher_integration

app_name = 'chat'
urlpatterns = [
    url(r'^$', chat_views.index, name='index'),
    url(r'^find_users/$', chat_views.find_users, name='find_users'),
    url(r'^get_conversations/$', chat_views.get_conversations, name='get_conversations'),
    url(r'^get_messages/$', chat_views.get_messages, name='get_messages'),
    url(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^post_message/$', chat_views.post_message, name='post_message'),
    url(r'^pusher_auth/', pusher_integration.authenticate, name='pusher_auth'),
]
