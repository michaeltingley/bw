from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

from uuid import uuid4

class Participant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __repr__(self):
        return "Participant(" + str(self.user) + ")"

class Conversation(models.Model):
    participants = models.ManyToManyField(Participant)

    def as_dict(self):
        '''Converts to dict with info about the latest message'''
        return {
            'participant_emails': [
                participant.user.username
                for participant in self.participants.all()
            ],
            'last_message': (
                self.message_set.order_by('-timestamp')[0].as_dict()
            )
        }

    def __repr__(self):
        return "Conversation(" + str(self.participants) + ")"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def as_dict(self):
        '''Converts to dict representation'''
        return {
            'email': self.participant.user.username,
            'body': self.text,
            'timestamp': format_instant(self.timestamp),
        }

    def __repr__(self):
        return "Message(text=" + self.text + ", timestamp=" + str(self.timestamp) + ")"

def format_instant(instant):
    now = datetime.now()
    if instant.year != now.year:
        return instant.strftime('%-I:%M%P, %b %d, %Y')
    if instant.month != now.month or instant.day != now.day:
        return instant.strftime('%-I:%M%P, %b %d')
    return instant.strftime('%-I:%M%P')
