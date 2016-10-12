from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User, Permission
from django.shortcuts import redirect, render
from django.views.generic import CreateView, DetailView
from django.views.generic.edit import FormView
from django.utils.translation import ugettext_lazy as _

from models import Project
from forms import ProjectForm, AddCollaboratorForm, SelectGroupForm, PermissionForm
from trusts.decorators import P, K, permission_required
from trusts.models import Trust, TrustGroup


@login_required
def home(request):
    'List projects shared with user'

    projects = Project.objects.all().permitted('read_project', request.user).distinct()
    trust, created = Trust.objects.get_or_create_settlor_default(request.user)
    return render(request, 'base.html', dict(projects=projects, trust=trust))


class NewProjectView(FormView):
    'Create new project'

    form_class = ProjectForm
    template_name = 'app/project_form.html'
    fields = 'trust', 'name'
    success_url = '/'

    def get_form_kwargs(self):
        kwargs = super(NewProjectView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})

        return kwargs

    def form_valid(self, form):

        self.object = form.save(commit=False)
        self.entity = self.request.user
        self.object.grant('read_project', self.request.user)
        self.object.grant('change_project', self.request.user)

        form.save()
        return super(NewProjectView, self).form_valid(form)


class ProjectView(DetailView):
    'View project, add collaborators, teams'
    model = Project

    @staticmethod
    def higest_permission(trustpermissions):
        for o in [u'change_project', u'read_project']:
            for tuple in trustpermissions:
                if tuple.permission.codename == o:
                    return tuple
        return None

    @staticmethod
    def higest_permission_code(trustpermissions):
        tuple = ProjectView.higest_permission(trustpermissions)
        if tuple is not None:
            return tuple.permission.codename

    @staticmethod
    def higest_team_permission_code(permissions):
        for o in [u'change_project', u'read_project']:
            for tuple in permissions:
                if tuple.codename == o:
                    return tuple.codename
        return None

    def dispatch(self, request, alias, pk):
        rmuser = request.POST.get('rmuser')
        if rmuser:
            self.get_object().trust.trustees.filter(pk=rmuser).delete()
            return redirect('.')
        rmgroup = request.POST.get('rmgroup')
        if rmgroup:
            self.get_object().trust.trustgroups.filter(pk=rmgroup).delete()
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
            tg = TrustGroup(group=group, trust=self.get_object().trust)
            tg.save()
            return redirect('.')

        # build formsets for changing user permissions
        trust = self.get_object().trust

        # formset for changing teams' permissions
        self.teams = trust.groups.filter(user=request.user)
        self.teamformset = forms.formset_factory(PermissionForm, extra=0)(
            request.POST or None, prefix='teams', initial=[dict(
                entity=t.pk, permission=self.higest_team_permission_code(t.permissions.all())
            ) for t in self.teams]
        )
        for team, form in zip(self.teams, self.teamformset):
            team.form = form
        if self.teamformset.is_valid():
            # adjust teams permissions if changed
            for data in self.teamformset.cleaned_data:
                team = Group.objects.get(pk=data['entity'])
                perms = team.permissions.all()
                if data['permission'] != self.higest_team_permission_code(perms):
                    if perms.count() == 0:
                        perm = Permission.objects.get_by_natural_key('read_project', 'app', 'project')
                        team.permissions.add(perm)

                        if data['permission'] == data['permission']:
                            perm = Permission.objects.get_by_natural_key('change_project', 'app', 'project')
                            team.permissions.add(perm)
                    elif data['permission'] is None:
                        team.permissions.remove()
                    elif data['permission'] == u'change_project':
                        perm = Permission.objects.get_by_natural_key('change_project', 'app', 'project')
                        team.permissions.add(perm)
                    else:
                        team.permissions.remove(*team.permissions.filter(codename='change_project'))
                    return redirect('.')

        # formset for changing user' permissions
        self.users = User.objects.filter(trustpermissions__trust=trust).distinct().all()
        self.userformset = forms.formset_factory(PermissionForm, extra=0)(
            request.POST or None, prefix='users', initial=[dict(
                entity=u.pk, permission=self.higest_permission_code(u.trustpermissions.filter(trust=trust))
            ) for u in self.users]
        )
        for user, form in zip(self.users, self.userformset):
            user.form = form
        if self.userformset.is_valid():
            # adjust collaborator permissions if changed
            for data in self.userformset.cleaned_data:
                user = User.objects.get(pk=data['entity'])
                perms = user.trustpermissions.filter(trust=trust)
                if data['permission'] != self.higest_permission_code(perms):
                    if perms.count() == 0:
                        self.get_object().add_collaborator(u'read_project', user)
                        if data['permission'] == u'change_project':
                            self.get_object().add_collaborator(u'change_project', user)
                    elif data['permission'] is None:
                        perms.delete()
                    elif data['permission'] == u'change_project':
                        self.get_object().add_collaborator(data['permission'], user)
                    else:
                        perms.filter(permission__codename='change_project').delete()
                    return redirect('.')

        return super(ProjectView, self).dispatch(request, pk)

project = permission_required(P('app.read_project', pk=K('pk')) | P('app.change_project', pk=K('pk')))(
    ProjectView.as_view())
