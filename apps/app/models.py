from django.contrib.auth.models import Permission
from django.db import models

from trusts.models import Content, TrustUserPermission


class Project(Content, models.Model):
    name = models.CharField(max_length=255)

    @staticmethod
    def change_permission():
        return Permission.objects.get_by_natural_key(
            'change_project', 'app', 'project')

    def get_absolute_url(self):
        return '/projects/%i/' % self.pk

    def __unicode__(self):
        return self.name

    def add_collaborator(self, user):
        return TrustUserPermission.objects.get_or_create(
            trust=self.trust, entity=user,
            permission=Project.change_permission())
