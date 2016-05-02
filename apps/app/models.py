from django.contrib.auth.models import Permission
from django.db import models

from trusts import ENTITY_MODEL_NAME, PERMISSION_MODEL_NAME, GROUP_MODEL_NAME, \
                    DEFAULT_SETTLOR, ALLOW_NULL_SETTLOR, ROOT_PK, utils
from trusts.models import Content, TrustUserPermission


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

    def add_collaborator(self, user):
        self.grant('change_project', user)
