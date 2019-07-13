from django.views import generic
from .models import Project, PredictionModel
from .forms import ProjectForm, PredictionModelForm
from django.shortcuts import render, redirect
from subprocess import Popen
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.contrib import messages
from rest_framework.views import APIView
from .serializer import ProjectGetSerializer, ProjectPostSerializer, PredictionModelGetSerializer,\
    PredictionModelPostSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import FileUploadParser, JSONParser


class ProjectListView(generic.View):
    model = Project
    template_name = 'projects/project_list.html'

    def get(self, request):
        if self.request.user.is_authenticated:
            projects = Project.objects.filter(user=self.request.user)
            return render(request, self.template_name, {'all_projects': projects})
        else:
            return render(request, 'login_warning.html', {})


class ProjectListAPIView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            projects = Project.objects.filter(user=self.request.user)
            serializer = ProjectGetSerializer(projects, many=True)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


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
                return render(request, self.template_name, {'all_models': models, 'project_id': project_id})
            else:
                return render(request, 'error404.html', {})
        else:
            return render(request, 'login_warning.html', {})


class ShowProjectAPIView(APIView):
    def get(self, request, **kwargs):
        if self.request.user.is_authenticated:
            project_id = kwargs.get('project_id')
            projects = Project.objects.filter(pk=project_id, user=request.user)
            if projects:
                project = projects[0]
                models = PredictionModel.objects.filter(project=project)
                serializer = PredictionModelGetSerializer(models, many=True)
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


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
                if model_id == 'cp':
                    model_name = 'CRISPRpred'
                    return render(request, self.template_name, {'model': model_name})
                elif model_id == 'cpp':
                    model_name = 'CRISPRpred++'
                    return render(request, self.template_name, {'model': model_name})
                elif model_id == 'cps':
                    model_name = 'CRISPRpred(SEQ)'
                    return render(request, self.template_name, {'model': model_name})
                else:
                    models = PredictionModel.objects.filter(project=project, pk=model_id)
                    if models:
                        model = models[0]
                        model_name = model.model_name
                        try:
                            open('media/project_' + project_id + '/' + model_name + '.pkl', 'rb')
                        except FileNotFoundError:
                            models = PredictionModel.objects.filter(project=project)
                            return render(request, 'projects/project_detail.html',
                                          {'all_models': models,
                                           'project_id': project_id,
                                           'error': "Training haven't finished yet",
                                           'error_model': model})
                        return render(request, self.template_name, {'model': model_name})
            return render(request, 'error404.html', {})
        else:
            return render(request, 'login_warning.html', {})

    @staticmethod
    def post(request, **kwargs):
        prediction_file = request.FILES.get('prediction_file')

        project_id = kwargs.get('project_id')
        model_id = kwargs.get('model_id')
        project = Project.objects.filter(pk=project_id)[0]
        if model_id == 'cp':
            model_type = 1
            model_name = "CRISPRpred"
        elif model_id == 'cpp':
            model_type = 2
            model_name = "CRISPRpred++"
        elif model_id == 'cps':
            model_type = 3
            model_name = "CRISPRpred(SEQ)"
        else:
            prediction_model = PredictionModel.objects.filter(project=project, pk=model_id)[0]
            model_type = prediction_model.model_type
            model_name = prediction_model.model_name

        fs = FileSystemStorage()
        filename = fs.save('project_' + str(project_id) + '/' + prediction_file.name, prediction_file)

        log = open('Logs/log_' + str(project_id) + '_' + str(model_id) + '_prediction.txt', 'w')
        Popen(['python', 'CRISPR_Methods/predict.py', str(project.pk),
               project.project_name, str(model_id), str(model_type), model_name,
               str(filename), project.user.email], stdout=log, stderr=log)

        return redirect(project)


class PredictAPIView(APIView):
    parser_classes = (FileUploadParser,)

    @staticmethod
    def post(request, **kwargs):
        prediction_file = request.FILES.get('prediction_file')

        project_id = kwargs.get('project_id')
        model_id = kwargs.get('model_id')
        project = Project.objects.filter(pk=project_id)[0]
        if model_id == 'cp':
            model_type = 1
            model_name = "CRISPRpred"
        elif model_id == 'cpp':
            model_type = 2
            model_name = "CRISPRpred++"
        elif model_id == 'cps':
            model_type = 3
            model_name = "CRISPRpred(SEQ)"
        else:
            prediction_model = PredictionModel.objects.filter(project=project, pk=model_id)[0]
            model_type = prediction_model.model_type
            model_name = prediction_model.model_name

        fs = FileSystemStorage()
        filename = fs.save('project_' + str(project_id) + '/' + prediction_file.name, prediction_file)

        log = open('Logs/log_' + str(project_id) + '_' + str(model_id) + '_prediction.txt', 'w')
        Popen(['python', 'CRISPR_Methods/predict.py', str(project.pk),
               project.project_name, str(model_id), str(model_type), model_name,
               str(filename), project.user.email], stdout=log, stderr=log)

        return Response(status=status.HTTP_202_ACCEPTED)


class ProjectCreateView(generic.View):
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


class ProjectCreateAPIView(APIView):
    def post(self, request):
        serializer = ProjectPostSerializer(data=request.data)
        if serializer.is_valid():
            project_name = serializer.validated_data['project_name']
            user = self.request.user

            if user.is_authenticated:
                project = Project(project_name=project_name, user=user)
                project.save()
                return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_403_FORBIDDEN)


class PredictionModelCreateView(generic.View):
    form_class = PredictionModelForm
    template_name = 'projects/predictionModel_form.html'

    def get(self, request, **kwargs):
        form = self.form_class(None)
        project_id = kwargs.get('project_id')
        projects = Project.objects.filter(pk=project_id, user=request.user)
        if not projects:
            return render(request, 'error404.html')
        project = projects[0]
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
            projects = Project.objects.filter(pk=project_id, user=request.user)
            if not projects:
                return render(request, 'error404.html')
            project = projects[0]
            models = PredictionModel.objects.filter(model_name=model_name)
            if models:
                messages.warning(request, "A model with this name already exists")
                return render(request, self.template_name, {'form': form, 'project_name': project.project_name})

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


class PredictionModelCreateAPIView(APIView):
    parser_classes = (FileUploadParser, JSONParser)

    def post(self, request, **kwargs):
        serializer = PredictionModelPostSerializer(data=request.data, files=request.files)

        model_name = serializer.validated_data['model_name']
        model_type = serializer.validated_data['model_type']
        training_file = serializer.validated_data['training_file']
        consent_for_file = serializer.validated_data['consent_for_file']

        project_id = kwargs.get('project_id')
        projects = Project.objects.filter(pk=project_id, user=self.request.user)[0]

        if not projects:
            return Response(status=status.HTTP_404_NOT_FOUND)
        project = projects[0]

        models = PredictionModel.objects.filter(model_name=model_name)
        if models:
            return Response(status=status.HTTP_403_FORBIDDEN)
        prediction_model = PredictionModel(model_name=model_name, model_type=model_type,
                                           training_file=training_file, consent_for_file=consent_for_file,
                                           project=project)
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
        return Response(status=status.HTTP_201_CREATED)


class DownloadView(generic.View):
    def get(self, request, **kwargs):
        project_id = kwargs.get('project_id')
        model_id = kwargs.get('model_id')
        if self.request.user.is_authenticated:
            projects = Project.objects.filter(pk=project_id, user=request.user)
            if projects:
                project = projects[0]
                if model_id == 'cp':
                    try:
                        file = open('media/project_' + project_id + '/crisprpred_prediction.csv', 'r')
                    except FileNotFoundError:
                        models = PredictionModel.objects.filter(project=project)
                        return render(request, 'projects/project_detail.html',
                                      {'all_models': models,
                                       'project_id': project_id,
                                       'cp_error': 'No prediction available'})
                    response = HttpResponse(file, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=crisprpred_prediction.csv'
                    return response
                elif model_id == 'cpp':
                    try:
                        file = open('media/project_' + project_id + '/crisprpred_plus_prediction.csv', 'r')
                    except FileNotFoundError:
                        models = PredictionModel.objects.filter(project=project)
                        return render(request, 'projects/project_detail.html',
                                      {'all_models': models,
                                       'project_id': project_id,
                                       'cpp_error': 'No prediction available'})
                    response = HttpResponse(file, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=crisprpred_plus_prediction.csv'
                    return response
                elif model_id == 'cps':
                    try:
                        file = open('media/project_' + project_id + '/crisprpred_seq_prediction.csv', 'r')
                    except FileNotFoundError:
                        models = PredictionModel.objects.filter(project=project)
                        return render(request, 'projects/project_detail.html',
                                      {'all_models': models,
                                       'project_id': project_id,
                                       'cps_error': 'No prediction available'})
                    response = HttpResponse(file, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=crisprpred_seq_prediction.csv'
                    return response
                else:
                    models = PredictionModel.objects.filter(project=project, pk=model_id)
                    if models:
                        model = models[0]
                        try:
                            file = open('media/project_' + project_id + '/' + model.model_name + '_prediction.csv', 'r')
                        except FileNotFoundError:
                            models = PredictionModel.objects.filter(project=project)
                            return render(request, 'projects/project_detail.html',
                                          {'all_models': models,
                                           'project_id': project_id,
                                           'error': 'No prediction available',
                                           'error_model': model})

                        response = HttpResponse(file, content_type='text/csv')
                        response['Content-Disposition'] = 'attachment; filename=' + model.model_name + '_prediction.csv'
                        return response
            return render(request, 'error404.html', {})
        else:
            return render(request, 'login_warning.html', {})


class DownloadAPIView(APIView):
    def get(self, request, **kwargs):
        project_id = kwargs.get('project_id')
        model_id = kwargs.get('model_id')
        if self.request.user.is_authenticated:
            projects = Project.objects.filter(pk=project_id, user=request.user)
            if projects:
                project = projects[0]
                if model_id == 'cp':
                    try:
                        file = open('media/project_' + project_id + '/crisprpred_prediction.csv', 'r')
                    except FileNotFoundError:
                        return Response(status=status.HTTP_404_NOT_FOUND)
                    response = HttpResponse(file, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=crisprpred_prediction.csv'
                    return response
                elif model_id == 'cpp':
                    try:
                        file = open('media/project_' + project_id + '/crisprpred_plus_prediction.csv', 'r')
                    except FileNotFoundError:
                        return Response(status=status.HTTP_404_NOT_FOUND)
                    response = HttpResponse(file, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=crisprpred_plus_prediction.csv'
                    return response
                elif model_id == 'cps':
                    try:
                        file = open('media/project_' + project_id + '/crisprpred_seq_prediction.csv', 'r')
                    except FileNotFoundError:
                        return Response(status=status.HTTP_404_NOT_FOUND)
                    response = HttpResponse(file, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=crisprpred_seq_prediction.csv'
                    return response
                else:
                    models = PredictionModel.objects.filter(project=project, pk=model_id)
                    if models:
                        model = models[0]
                        try:
                            file = open('media/project_' + project_id + '/' + model.model_name + '_prediction.csv', 'r')
                        except FileNotFoundError:
                            return Response(status=status.HTTP_404_NOT_FOUND)

                        response = HttpResponse(file, content_type='text/csv')
                        response['Content-Disposition'] = 'attachment; filename=' + model.model_name + '_prediction.csv'
                        return response
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class InstructionView(generic.View):
    @staticmethod
    def get(request):
        return render(request, 'projects/instructions.html', {})
