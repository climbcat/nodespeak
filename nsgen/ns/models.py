from django.db import models
from django.db.models import TextField, CharField, DateTimeField, BooleanField, IntegerField
from django.utils import timezone

class SignUp(models.Model):
    email = CharField(max_length=200, default="", blank=True, null=True)
    token = CharField(max_length=200, default="", blank=True, null=True)

class TabId(models.Model):
    created = DateTimeField('created', default=timezone.now)
    gs_id = CharField(max_length=200)

class GraphSession(models.Model):
    # TODO: make user-specific
    created = DateTimeField('created', default=timezone.now)
    modified = DateTimeField('modified', default=timezone.now)

    org_version = CharField(max_length=200, default="", blank=True, null=True)
    title = CharField(max_length=200, default="", blank=True, null=True)
    description = TextField(blank=True, null=True)

    data_str = TextField(blank=True)
    def __str__(self):
        return 'session %s, %s' % (self.id, self.title)

class TypeSchema(models.Model):
    created = DateTimeField('created', default=timezone.now)
    modified = DateTimeField('modified', default=timezone.now)

    version = CharField(max_length=200, default="", blank=True, null=True)
    title = CharField(max_length=200, default="", blank=True, null=True)
    description = TextField(blank=True, null=True)

    data_str = TextField(blank=True)
    def __str__(self):
        return 'typetree %s' % (self.id)
