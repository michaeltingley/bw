"""Database models for the chat application."""

from datetime import datetime

from django.contrib.auth.models import User
from django.db import models


class Participant(models.Model):
    """A user of the chat application.

    This has a one-to-one association with a User, and may be used to augment
    the User model with properties specific to the chat application, although
    no such augmentations exist yet.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __repr__(self):
        return "Participant(" + str(self.user) + ")"


class Conversation(models.Model):
    """Represents a conversation between two or more participants.

    A conversation may have many participants, and a participant may partake in
    many conversations.
    """
    participants = models.ManyToManyField(Participant)

    def as_dict(self):
        """Converts to dict with info about the latest message.

        Returns:
            dict. Contains two keys. participant_emails lists the emails of each
            participant. last_message contains the dict representation of the
            last message in this conversation.
        """
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
    """Represents a message within a conversation.

    A message belongs to exactly one conversation, and was posted by exactly
    one participant. It has text and a time of posting, which is set to be the
    time that it was inserted into the database.
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    participant = models.ForeignKey(Participant)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def as_dict(self):
        """Converts to dict representation.

        Returns:
            dict. Contains the following keys. email contains the email of the
            participant that posted this message. body contains the text of the
            message. timestamp contains the timestamp of the message, formatted
            as a string with format_instant.
        """

        def format_instant(instant):
            """Formats a datetime for display.

            Args:
                instant (datetime): The datetime for display.

            Returns:
                str. The string to display for this timestamp. If the instant's
                year is different than the current year, uses the time and full
                date. Otherwise, if it is a different month or day, uses the
                time and abbreviated month with day. Otherwise, uses the time.
            """
            now = datetime.now()
            if instant.year != now.year:
                return instant.strftime('%-I:%M%P, %b %d, %Y')
            if instant.month != now.month or instant.day != now.day:
                return instant.strftime('%-I:%M%P, %b %d')
            return instant.strftime('%-I:%M%P')

        return {
            'email': self.participant.user.username,
            'body': self.text,
            'timestamp': format_instant(self.timestamp),
        }

    def __repr__(self):
        return (
            "Message("
            + "text=" + self.text + ", "
            + "timestamp=" + str(self.timestamp) + ")"
        )
