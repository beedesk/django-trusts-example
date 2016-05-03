from django.core.urlresolvers import reverse
from django.test import TestCase

from models import Project
import views
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group


class MainTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('a', 'b', 'c')
        self.client.login(username='a', password='c')

    def test_home(self):
        r = self.client.get('/')
        self.assertContains(r, 'html')

    def test_project(self):
        p = Project.objects.create()
        p.add_collaborator('change_project', self.user)
        r = self.client.get(p.get_absolute_url())
        self.assertContains(r, 'html')
        # add collaborator
        u = get_user_model().objects.create(username='b')
        self.assertFalse(u.has_perm('app.change_project', p))
        r = self.client.post(p.get_absolute_url(), dict(
            user=u.pk, permission='change_project'))
        self.assertRedirects(r, p.get_absolute_url())
        u = get_user_model().objects.get(pk=u.pk)
        self.assertTrue(u.has_perm('app.change_project', p))
        # add team
        u = get_user_model().objects.create(username='c')
        g = Group.objects.create()
        u.groups.add(g)
        self.assertFalse(u.has_perm('app.change_project', p))
        r = self.client.post(p.get_absolute_url(), dict(group=g.pk))
        self.assertRedirects(r, p.get_absolute_url())
        u = get_user_model().objects.get(pk=u.pk)
        self.assertTrue(u.has_perm('app.change_project', p))

    def test_newproject(self):
        url = '/projects/x/new/'
        r = self.client.get(url)
        self.assertContains(r, 'html')
        r = self.client.post(url, dict(name='Test'))
        p = Project.objects.get()
        self.assertRedirects(r, p.get_absolute_url())
        self.assertTrue(self.user.has_perm('app.change_project', p))
