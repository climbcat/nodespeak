from django.db import models
from django.db.models import TextField, CharField, DateTimeField, BooleanField, IntegerField
from django.utils import timezone

class TabId(models.Model):
    created = DateTimeField('created', default=timezone.now)
    gs_id = CharField(max_length=200)

class GraphSession(models.Model):
    created = DateTimeField('created', default=timezone.now)

    title = CharField(max_length=200, default="", blank=True, null=True)
    description = TextField(blank=True, null=True)

    quicksaved = DateTimeField('quicksaved', blank=True, null=True)
    stashed = DateTimeField('stashed', blank=True, null=True)

    graphdef = TextField(blank=True)

    def __str__(self):
       return 'session %s, %s' % (self.id, self.title)
