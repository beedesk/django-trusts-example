from django import forms
from django.contrib.auth.models import Group, User
from django.utils.translation import ugettext_lazy as _

from trusts.models import Trust

from models import Project

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = 'trust', 'title'
        labels = {
            'trust': _('Owner'),
        }

    def __init__(self, user=None, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)

        default_trust = Trust.objects.get_or_create_settlor_default(user)
        print 'default_trust: ', default_trust
        self.fields['trust'].queryset = Trust.objects.filter_by_user_content_perm(
            user, Project, 'add_project', exclude_root=True
        )

        print 'qs: ', self.fields['trust'].queryset.all()
        print self.fields['trust'].queryset


class AddCollaboratorForm(forms.Form):
    user = forms.ModelChoiceField(User.objects.all())


class SelectGroupForm(forms.Form):
    group = forms.ModelChoiceField(Group.objects.all())


class PermissionForm(forms.Form):
    entity = forms.CharField(widget=forms.HiddenInput())  # team or user id
    permission = forms.ChoiceField([
        ('read_project', 'Read'),
        ('change_project', 'Write'),
    ])
