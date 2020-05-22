from django.contrib import admin
from .models import UserTypes, GraphSession, TabId

admin.site.register(UserTypes)
admin.site.register(GraphSession)
admin.site.register(TabId)