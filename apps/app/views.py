from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect, render
from django.views.generic import CreateView, DetailView

from models import Project
from trusts.decorators import P, K, permission_required
from trusts.models import Trust


class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        exclude = 'trust',


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


@login_required
def home(request):
    'List projects shared with user'

    projects = Project.objects.all().permitted('read_project', request.user).distinct()
    trust, created = Trust.objects.get_or_create_settlor_default(request.user)
    return render(request, 'base.html', dict(projects=projects, trust=trust))


class NewProjectView(CreateView):
    'Create new project'
    model = Project
    fields = 'name',

    def form_valid(self, form):
        r = super(NewProjectView, self).form_valid(form)
        self.entity = self.request.user
        self.trust, created = Trust.objects.get_or_create_settlor_default(self.request.user)
        print 'trust: ', self.trust, ' settlor: ', self.trust.settlor
        self.object.grant('read_project', self.request.user)
        self.object.grant('change_project', self.request.user)
        return r
newproject = login_required(NewProjectView.as_view())


class ProjectView(DetailView):
    'View project, add collaborators, teams'
    model = Project

    def dispatch(self, request, alias, pk):
        rmuser = request.POST.get('rmuser')
        if rmuser:
            self.get_object().trust.trustees.filter(pk=rmuser).delete()
            return redirect('.')
        rmgroup = request.POST.get('rmgroup')
        if rmgroup:
            self.get_object().trust.groups.remove(rmgroup)
            return redirect('.')
        self.adduserform = AddCollaboratorForm(request.POST or None)
        if self.adduserform.is_valid():
            # add project collaborator
            user = self.adduserform.cleaned_data['user']
            obj = self.get_object()
            if not obj.trust.trustees.filter(entity=user).exists():
                obj.add_collaborator('read_project', user)
            return redirect('.')
        self.addgroupform = SelectGroupForm(request.POST or None)
        if self.addgroupform.is_valid():
            # give permission on this project to selected team
            group = self.addgroupform.cleaned_data['group']
            group.permissions.add(Project.change_permission())
            group.trusts.add(self.get_object().trust)
            return redirect('.')
        # build formset for changing teams' permissions
        self.teams = self.get_object().trust.groups.all()
        self.teamformset = forms.formset_factory(PermissionForm, extra=0)(
            request.POST or None, prefix='teams', initial=[dict(
                entity=t.pk, permission='change_project'
                if Project.change_permission() in t.permissions.all()
                else 'read_project'
            ) for t in self.teams]
        )
        if self.teamformset.is_valid():
            # adjust teams permissions
            for data in self.teamformset.cleaned_data:
                team = self.teams.get(pk=data['entity'])
                if data['permission'] == 'change_project':
                    team.permissions.add(Project.change_permission())
                else:
                    team.permissions.remove(Project.change_permission())
            return redirect('.')
        for team, form in zip(self.teams, self.teamformset):
            team.form = form
        # build formset for changing user permissions
        self.trustees = self.get_object().trust.trustees.all()
        self.userformset = forms.formset_factory(PermissionForm, extra=0)(
            request.POST or None, prefix='users', initial=[dict(
                entity=t.pk, permission=t.permission.codename
            ) for t in self.trustees]
        )
        if self.userformset.is_valid():
            # adjust collaborator permissions
            for data in self.userformset.cleaned_data:
                trustee = self.trustees.get(pk=data['entity'])
                if trustee.permission.codename != data['permission']:
                    trustee.delete()
                    self.get_object().add_collaborator(
                        data['permission'], trustee.entity)
            return redirect('.')
        for trustee, form in zip(self.trustees, self.userformset):
            trustee.form = form
        return super(ProjectView, self).dispatch(request, pk)

project = permission_required(P('app.read_project', pk=K('pk')) | P('app.change_project', pk=K('pk')))(
    ProjectView.as_view())
