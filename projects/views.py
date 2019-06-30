from django.views import generic
from .models import Project
from .forms import ProjectForm
from django.shortcuts import render, redirect


class IndexView(generic.ListView):
    template_name = 'projects/project_list.html'
    context_object_name = 'all_projects'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Project.objects.filter(user=self.request.user)
        else:
            return Project.objects.none()


class ShowProjectView(generic.DetailView):
    model = Project
    template_name = 'projects/project_detail.html'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Project.objects.filter(user=self.request.user)
        else:
            return Project.objects.none()


class ProjectCreate(generic.View):
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            project = form.save(commit=False)

            # clean data
            project_name = form.cleaned_data['project_name']

            # finally create new project
            project.project_name = project_name

            user = request.user
            project.user = user

            if user.is_authenticated:
                project.save()
                return redirect(project)
            else:
                return render(request, 'login_warning.html')
