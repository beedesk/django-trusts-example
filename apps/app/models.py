from django.contrib.auth.models import Permission
from django.db import models
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from trusts.models import Content


class Project(Content, models.Model):
    title = models.CharField(max_length=40, null=False, blank=False, unique=True, verbose_name=_('name'))
    slug = models.CharField(max_length=40, null=False, blank=False, unique=True, verbose_name=_('name'))

    class Meta:
        default_permissions = ('add', 'read', 'change', 'delete')
        roles = (
            ('creator', ('add', 'read', 'change', 'delete')),
        )

    @staticmethod
    def change_permission():
        return Permission.objects.get_by_natural_key(
            'change_project', 'app', 'project')

    def get_absolute_url(self):
        return '/projects/%s/%i/' % (self.trust.settlor.username, self.pk)

    def __unicode__(self):
        return self.title

    def add_collaborator(self, permission, user):
        self.grant(permission, user)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        print 'slug: ', self

        return super(Project, self).save(*args, **kwargs)
