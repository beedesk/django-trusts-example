from django.contrib.auth.models import Permission
from django.db import models

from trusts.models import Content


class Project(Content, models.Model):
    name = models.CharField(max_length=255)

    @staticmethod
    def change_permission():
        return Permission.objects.get_by_natural_key(
            'change_project', 'app', 'project')

    def get_absolute_url(self):
        return '/projects/%s/%i/' % (self.trust.settlor.username, self.pk)

    def __unicode__(self):
        return self.name

    def add_collaborator(self, permission, user):
        self.grant(permission, user)
