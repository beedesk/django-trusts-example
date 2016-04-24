from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect, render
from django.views.generic import CreateView, DetailView

from models import Project
from trusts.decorators import permission_required


class ProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        exclude = 'trust',


class SelectUserForm(forms.Form):
    user = forms.ModelChoiceField(User.objects.all())


class SelectGroupForm(forms.Form):
    group = forms.ModelChoiceField(Group.objects.all())


@login_required
def home(request):
    'List projects shared with user'
    projects = Project.objects.filter(trust__trustees__entity=request.user)
    projects |= Project.objects.filter(trust__groups__user=request.user)
    return render(request, 'home.html', dict(projects=projects))


class NewProjectView(CreateView):
    'Create new project'
    model = Project
    fields = 'name',

    def form_valid(self, form):
        r = super(NewProjectView, self).form_valid(form)
        self.object.add_collaborator(self.request.user)
        return r
newproject = NewProjectView.as_view()


class ProjectView(DetailView):
    'View project, add collaborators, teams'
    model = Project

    def dispatch(self, request, pk):
        self.adduserform = SelectUserForm(request.POST or None)
        if self.adduserform.is_valid():
            # add project collaborator
            self.get_object().add_collaborator(
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

project = permission_required('app.change_project', fieldlookups_kwargs=dict(
    pk='pk'))(ProjectView.as_view())
