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
from ns import views

urlpatterns = [
    url(r'login/?$', views.login),
    url(r'login_submit/?$', views.login_submit),
    url(r'edit/(?P<gs_id>[0-9]+)/?$', views.edit),
    url(r'edit_submit/(?P<gs_id>[0-9]+)/?$', views.edit_submit),
    url(r'logout/?$', views.logout),

    url(r'session/(?P<gs_id>[0-9]+)/?$', views.graphui),

    url(r'latest/?$', views.latest_gs),
    url(r'last/?$', views.latest_gs),
    url(r'duplicate/(?P<gs_id>[0-9]+)/?$', views.duplicate_gs),
    url(r'delete/(?P<gs_id>[0-9]+)/?$', views.delete_gs),
    url(r'new/(?P<ts_id>[0-9]+)/?$', views.new_gs),
    url(r'new/?$', views.new_gs),
    url(r'dashboard/?$', views.dashboard),
    
    url(r'ajax_load/(?P<gs_id>[\w0-9]+)/?$', views.ajax_load),
    url(r'ajax_commit/?$', views.ajax_commit),
    url(r'ajax_cogen/?$', views.ajax_cogen),

    url(r'test/?$', views.test),

    url(r'', views.index),
]
