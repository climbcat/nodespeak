"""genproj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from graphs import views

urlpatterns = [
    url(r'graph_session/(?P<gs_id>[\w0-9]+)/?$', views.graph_session),
    url(r'ajax_load/(?P<gs_id>[\w0-9]+)/?$', views.ajax_load),
    url(r'ajax_commit/?$', views.ajax_commit),
]
