"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView

import trusts.views
import views

urlpatterns = [
    url(r'^$', views.home),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^projects/(?P<alias>\w+)/(?P<pk>\d+)/$', views.project, name='project_view'),
    url(r'^projects/new/$', login_required(views.NewProjectView.as_view()), name='project_create'),
    url(r'^entities/(?P<alias>\w+)/$', TemplateView.as_view(template_name='app/entity.html'), name='entities_view'),
    url(r'^teams/(?P<pk>\d+)/$', trusts.views.team),
    url(r'^teams/new/$', trusts.views.newteam),
]

urlpatterns += staticfiles_urlpatterns()
admin.autodiscover()
