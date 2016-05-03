from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect, render
from django.views.generic import CreateView, DetailView

from models import Project
from trusts.decorators import K, permission_required
from trusts.models import Trust


class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        exclude = 'trust',


class AddCollaboratorForm(forms.Form):
    user = forms.ModelChoiceField(User.objects.all())
    permission = forms.ChoiceField([
        ('read_project', 'Read-only'),
        ('change_project', 'Read/Write'),
    ])


class SelectGroupForm(forms.Form):
    group = forms.ModelChoiceField(Group.objects.all())


@login_required
def home(request):
    'List projects shared with user'

    projects = Project.objects.all().permitted('read_project', request.user)
    trust = Trust.objects.get_or_create_settlor_default(request.user)
    return render(request, 'base.html', dict(projects=projects, trust=trust))


class NewProjectView(CreateView):
    'Create new project'
    model = Project
    fields = 'name',

    def form_valid(self, form):
        r = super(NewProjectView, self).form_valid(form)
        self.entity = self.request.user
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
            self.get_object().add_collaborator(
                self.adduserform.cleaned_data['permission'],
                self.adduserform.cleaned_data['user'])
            return redirect('.')
        self.addgroupform = SelectGroupForm(request.POST or None)
        if self.addgroupform.is_valid():
            # give permission on this project to selected team
            group = self.addgroupform.cleaned_data['group']
            group.permissions.add(Project.change_permission())
            group.trusts.add(self.get_object().trust)
            return redirect('.')
        return super(ProjectView, self).dispatch(request, pk)

project = permission_required('app.change_project', pk=K('pk'))(
    ProjectView.as_view())
