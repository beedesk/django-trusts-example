from django.contrib import admin
from django.contrib.auth.models import Permission

from .models import Project

admin.site.register(Project, admin.ModelAdmin)
admin.site.register(Permission, admin.ModelAdmin)

