from django.views import generic
from .models import Project, PredictionModel
from .forms import ProjectForm, PredictionModelForm
from django.shortcuts import render, redirect
from subprocess import Popen
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse


class ProjectListView(generic.View):
    model = Project
    template_name = 'projects/project_list.html'

    def get(self, request):
        if self.request.user.is_authenticated:
            projects = Project.objects.filter(user=self.request.user)
            return render(request, self.template_name, {'all_projects': projects})
        else:
            return render(request, 'login_warning.html', {})


class ShowProjectView(generic.View):
    model = PredictionModel
    template_name = 'projects/project_detail.html'

    def get(self, request, **kwargs):
        if self.request.user.is_authenticated:
            project_id = kwargs.get('project_id')
            projects = Project.objects.filter(pk=project_id, user=self.request.user)
            if projects:
                project = projects[0]
                models = PredictionModel.objects.filter(project=project)
                return render(request, self.template_name, {'all_models': models})
            else:
                return render(request, 'error404.html', {})
        else:
            return render(request, 'login_warning.html', {})


class ShowPredictionModelView(generic.View):
    model = PredictionModel
    template_name = 'projects/model_detail.html'

    def get(self, request, **kwargs):
        if self.request.user.is_authenticated:
            project_id = kwargs.get('project_id')
            model_id = kwargs.get('model_id')
            projects = Project.objects.filter(pk=project_id, user=self.request.user)
            if projects:
                project = projects[0]
                models = PredictionModel.objects.filter(project=project, pk=model_id)
                if models:
                    model = models[0]
                    return render(request, self.template_name, {'model': model})
            return render(request, 'error404.html', {})
        else:
            return render(request, 'login_warning.html', {})


class PredictView(generic.View):
    model = PredictionModel
    template_name = 'projects/prediction.html'

    def get(self, request, **kwargs):
        if self.request.user.is_authenticated:
            project_id = kwargs.get('project_id')
            model_id = kwargs.get('model_id')
            projects = Project.objects.filter(pk=project_id, user=self.request.user)
            if projects:
                project = projects[0]
                models = PredictionModel.objects.filter(project=project, pk=model_id)
                if models:
                    model = models[0]

                    try:
                        f = open('media/project_' + project_id + '/' + model.model_name + '.pkl', 'rb')
                    except FileNotFoundError:
                        return render(request, 'training_not_finished.html', {})

                    return render(request, self.template_name, {'model': model})
            return render(request, 'error404.html', {})
        else:
            return render(request, 'login_warning.html', {})

    @staticmethod
    def post(request, **kwargs):
        file = request.FILES.get('file')

        project_id = kwargs.get('project_id')
        model_id = kwargs.get('model_id')
        project = Project.objects.filter(pk=project_id)[0]
        prediction_model = PredictionModel.objects.filter(project=project, pk=model_id)[0]

        fs = FileSystemStorage()
        filename = fs.save('project_' + str(project_id) + '/' + file.name, file)

        log = open('Logs/log_' + str(project_id) + '_' + str(prediction_model.pk) + '_prediction.txt', 'w')
        Popen(['python', 'CRISPR_Methods/predict.py', str(project.pk),
               project.project_name, str(prediction_model.model_type), prediction_model.model_name,
               str(filename), project.user.email], stdout=log, stderr=log)

        return redirect(project)


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
        return render(request, self.template_name, {'form': form})


class PredictionModelCreate(generic.View):
    form_class = PredictionModelForm
    template_name = 'projects/predictionModel_form.html'

    def get(self, request, **kwargs):
        form = self.form_class(None)
        project_id = kwargs.get('project_id')
        project = Project.objects.filter(pk=project_id)[0]
        project_name = project.project_name
        return render(request, self.template_name, {'form': form, 'project_name': project_name})

    def post(self, request, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            prediction_model = form.save(commit=False)

            # clean data
            model_name = form.cleaned_data['model_name']
            model_type = form.cleaned_data['model_type']
            training_file = form.cleaned_data['training_file']
            consent_for_file = form.cleaned_data['consent_for_file']

            # finally create new project
            prediction_model.model_name = model_name
            prediction_model.model_type = model_type
            prediction_model.training_file = training_file
            prediction_model.consent_for_file = consent_for_file

            project_id = kwargs.get('project_id')
            project = Project.objects.filter(pk=project_id)[0]

            models = PredictionModel.objects.filter(model_name=model_name)
            if models:
                return render(request, self.template_name, {'form': form, 'project_name': project.project_name,
                                                            'error': 'A model with this name already exists'})

            prediction_model.project = project
            prediction_model.save()
            log = open('Logs/log_' + str(project_id) + '_' + str(prediction_model.pk) + '.txt', 'w')
            if prediction_model.model_type == 1:
                Popen(['python', 'CRISPR_Methods/train_crisprpred.py', str(project.pk),
                       project.project_name, prediction_model.model_name,
                       str(prediction_model.training_file), project.user.email], stdout=log, stderr=log)
            elif prediction_model.model_type == 2:
                Popen(['python', 'CRISPR_Methods/train_crisprpred_plus.py', str(project.pk),
                       project.project_name, prediction_model.model_name,
                       str(prediction_model.training_file), project.user.email], stdout=log, stderr=log)
            else:
                Popen(['python', 'CRISPR_Methods/train_crisprpred_seq.py', str(project.pk),
                       project.project_name, prediction_model.model_name,
                       str(prediction_model.training_file), project.user.email], stdout=log, stderr=log)
            return redirect(project)
        return render(request, self.template_name, {'form': form})


def download_prediction_file(request, project_id, model_id):
    if request.user.is_authenticated:
        projects = Project.objects.filter(pk=project_id, user=request.user)
        if projects:
            project = projects[0]
            models = PredictionModel.objects.filter(project=project, pk=model_id)
            if models:
                model = models[0]
                try:
                    file = open('media/project_' + project_id + '/' + model.model_name + '_prediction.csv', 'r')
                except FileNotFoundError:
                    return render(request, 'prediction_not_finished.html', {})

                response = HttpResponse(file, content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename=' + model.model_name + '_prediction.csv'
                return response
        return render(request, 'error404.html', {})
    else:
        return render(request, 'login_warning.html', {})
