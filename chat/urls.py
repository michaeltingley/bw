from django.conf.urls import url

from . import views

app_name = 'chat'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^about/', views.AboutView.as_view(), name='about'),
    url(r'^pusher_auth/', views.pusher_auth, name='pusher_auth'),
    url(r'^find_users/$', views.find_users, name='find_users'),
    url(r'^get_conversations/$', views.get_conversations, name='get_conversations'),
    url(r'^get_messages/$', views.get_messages, name='get_messages'),
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^post_message/$', views.post_message, name='post_message'),
]
