from django.contrib import admin
from .models import TypeSchema, GraphSession, TabId

admin.site.register(TypeSchema)
admin.site.register(GraphSession)
admin.site.register(TabId)