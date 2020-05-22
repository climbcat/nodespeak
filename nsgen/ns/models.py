from django.db import models
from django.db.models import TextField, CharField, DateTimeField, BooleanField, IntegerField
from django.utils import timezone

class TabId(models.Model):
    created = DateTimeField('created', default=timezone.now)
    gs_id = CharField(max_length=200)

class GraphSession(models.Model):
    # TODO: make user-specific
    created = DateTimeField('created', default=timezone.now)
    modified = DateTimeField('modified', default=timezone.now)
    title = CharField(max_length=200, default="", blank=True, null=True)
    description = TextField(blank=True, null=True)
    graphdef = TextField(blank=True)
    def __str__(self):
        return 'session %s, %s' % (self.id, self.title)

class UserTypes(models.Model):
    # TODO: make user-specific (and unique for now, but later on, a selection)
    created = DateTimeField('created', default=timezone.now)
    modified = DateTimeField('modified', default=timezone.now)
    typetree = TextField(blank=True)
    def __str__(self):
        return 'typetree %s' % (self.id)
