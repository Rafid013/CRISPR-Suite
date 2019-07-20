from django.views import generic
from .models import Project, PredictionModel
from .forms import ProjectForm, PredictionModelForm
from django.shortcuts import render, redirect
from subprocess import Popen
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from rest_framework.views import APIView
from .serializer import ProjectGetSerializer, ProjectPostSerializer, PredictionModelGetSerializer, \
    PredictionModelPostSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import FileUploadParser, MultiPartParser


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
    @staticmethod
    def get(request):
        projects = Project.objects.filter(user=request.user)
        serializer = ProjectGetSerializer(projects, many=True)
        return Response(serializer.data)


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
                return render(request, 'error.html', {'status_code': 403})
        else:
            return render(request, 'login_warning.html', {})


class ShowProjectAPIView(APIView):
    @staticmethod
    def get(request, **kwargs):
        project_id = kwargs.get('project_id')
        projects = Project.objects.filter(pk=project_id, user=request.user)
        if projects:
            project = projects[0]
            models = PredictionModel.objects.filter(project=project)
            serializer = PredictionModelGetSerializer(models, many=True)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


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
                            open('saved_models/project_' + project_id + '/' + model_name + '.pkl', 'rb')
                        except FileNotFoundError:
                            models = PredictionModel.objects.filter(project=project)
                            messages.warning(request, "Training haven\'t finished yet")
                            return render(request, 'projects/project_detail.html',
                                          {'all_models': models,
                                           'project_id': project_id})
                        return render(request, self.template_name, {'model': model_name})
            return render(request, 'error.html', {'status_code': 403})
        else:
            return render(request, 'login_warning.html', {})

    def post(self, request, **kwargs):
        if self.request.user.is_authenticated:
            prediction_file = request.FILES.get('prediction_file')

            project_id = kwargs.get('project_id')
            model_id = kwargs.get('model_id')
            projects = Project.objects.filter(pk=project_id, user=self.request.user)
            if projects:
                project = projects[0]
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
                    prediction_models = PredictionModel.objects.filter(project=project, pk=model_id)
                    if prediction_models:
                        prediction_model = prediction_models[0]
                        model_type = prediction_model.model_type
                        model_name = prediction_model.model_name
                    else:
                        return render(request, 'error.html', {'status_code': 404})

                fs = FileSystemStorage()
                filename = fs.save('project_' + str(project_id) + '/' + prediction_file.name, prediction_file)

                log = open('Logs/log_' + str(project_id) + '_' + str(model_id) + '_prediction.txt', 'w')
                Popen(['python', 'CRISPR_Methods/predict.py', str(project.pk),
                       project.project_name, str(model_id), str(model_type), model_name,
                       str(filename), project.user.email], stdout=log, stderr=log)

                return redirect(project)
            return render(request, 'error.html', {'status_code': 403})
        else:
            return render(request, 'login_warning.html', {})


class PredictAPIView(APIView):
    parser_classes = (FileUploadParser,)

    @staticmethod
    def post(request, **kwargs):
        prediction_file = request.FILES.get('prediction_file')

        project_id = kwargs.get('project_id')
        model_id = kwargs.get('model_id')
        projects = Project.objects.filter(pk=project_id, user=request.user)
        if projects:
            project = projects[0]
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
                prediction_models = PredictionModel.objects.filter(project=project, pk=model_id)
                if prediction_models:
                    prediction_model = prediction_models[0]
                    model_type = prediction_model.model_type
                    model_name = prediction_model.model_name
                else:
                    return Response(status=status.HTTP_404_NOT_FOUND)

            fs = FileSystemStorage()
            filename = fs.save('project_' + str(project_id) + '/' + prediction_file.name, prediction_file)

            log = open('Logs/log_' + str(project_id) + '_' + str(model_id) + '_prediction.txt', 'w')
            Popen(['python', 'CRISPR_Methods/predict.py', str(project.pk),
                   project.project_name, str(model_id), str(model_type), model_name,
                   str(filename), project.user.email], stdout=log, stderr=log)

            return Response(status=status.HTTP_202_ACCEPTED)
        return Response(status=status.HTTP_403_FORBIDDEN)


class ProjectCreateView(generic.View):
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def get(self, request):
        if request.user.is_authenticated:
            form = self.form_class(None)
            return render(request, self.template_name, {'form': form})
        else:
            return render(request, 'login_warning.html', {})

    def post(self, request):
        if request.user.is_authenticated:
            form = self.form_class(request.POST)
            if form.is_valid():
                project = form.save(commit=False)

                # clean data
                project_name = form.cleaned_data['project_name']

                # finally create new project
                project.project_name = project_name

                user = request.user
                project.user = user
                project.save()
                return redirect(project)
            return render(request, self.template_name, {'form': form})
        else:
            return render(request, 'login_warning.html')


class ProjectCreateAPIView(APIView):
    def post(self, request):
        serializer = ProjectPostSerializer(data=request.data)
        if serializer.is_valid():
            project_name = serializer.validated_data['project_name']
            user = self.request.user
            project = Project(project_name=project_name, user=user)
            project.save()
            return Response(status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_406_NOT_ACCEPTABLE)


class PredictionModelCreateView(generic.View):
    form_class = PredictionModelForm
    template_name = 'projects/predictionModel_form.html'

    def get(self, request, **kwargs):
        if self.request.user.is_authenticated:
            form = self.form_class(None)
            project_id = kwargs.get('project_id')
            projects = Project.objects.filter(pk=project_id, user=request.user)
            if projects:
                project = projects[0]
                project_name = project.project_name
                return render(request, self.template_name, {'form': form, 'project_name': project_name})
            return render(request, 'error.html', {'status_code': 403})
        else:
            return render(request, 'login_warning.html', {})

    def post(self, request, **kwargs):
        if self.request.user.is_authenticated:
            form = self.form_class(request.POST, request.FILES)
            if form.is_valid():
                prediction_model = form.save(commit=False)

                # clean data
                model_name = form.cleaned_data['model_name']
                model_type = form.cleaned_data['model_type']
                training_file = form.cleaned_data['training_file']
                consent_for_file = form.cleaned_data['consent_for_file']
                is_public = form.cleaned_data['is_public']

                # finally create new project
                prediction_model.model_name = model_name
                prediction_model.model_type = model_type
                prediction_model.training_file = training_file
                prediction_model.consent_for_file = consent_for_file
                prediction_model.is_public = is_public

                project_id = kwargs.get('project_id')
                projects = Project.objects.filter(pk=project_id, user=request.user)
                if projects:
                    project = projects[0]
                    models = PredictionModel.objects.filter(project=project, model_name=model_name)
                    if models:
                        messages.warning(request, "A model with this name already exists in this project")
                        return render(request, self.template_name, {'form': form, 'project_name': project.project_name})

                    prediction_model.project = project
                    prediction_model.save()
                else:
                    return render(request, 'error.html', {'status_code': 403})

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
        else:
            return render(request, 'login_warning.html', {})


class PredictionModelCreateAPIView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, **kwargs):
        serializer = PredictionModelPostSerializer(data=request.data)
        if serializer.is_valid():
            model_name = serializer.validated_data['model_name']
            model_type = serializer.validated_data['model_type']
            training_file = request.FILES.get('training_file')
            consent_for_file = serializer.validated_data['consent_for_file']
            is_public = serializer.validated_data['is_public']

            project_id = kwargs.get('project_id')
            projects = Project.objects.filter(pk=project_id, user=self.request.user)

            if projects:
                project = projects[0]

                models = PredictionModel.objects.filter(project=project, model_name=model_name)
                if models:
                    return Response(status=status.HTTP_406_NOT_ACCEPTABLE)
                prediction_model = PredictionModel(model_name=model_name, model_type=model_type,
                                                   training_file=training_file, consent_for_file=consent_for_file,
                                                   is_public=is_public, project=project)
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
            return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)


class DownloadView(generic.View):
    def get(self, request, **kwargs):
        project_id = kwargs.get('project_id')
        model_id = kwargs.get('model_id')
        if self.request.user.is_authenticated:
            projects = Project.objects.filter(pk=project_id, user=request.user)
            if projects:
                project = projects[0]
                prediction_directory = 'predictions/project_' + project_id + '/'
                if model_id == 'cp':
                    try:
                        file = open(prediction_directory + 'crisprpred_prediction.csv', 'r')
                    except FileNotFoundError:
                        models = PredictionModel.objects.filter(project=project)
                        messages.warning(request, "No prediction is available for this model")
                        return render(request, 'projects/project_detail.html',
                                      {'all_models': models,
                                       'project_id': project_id})
                    response = HttpResponse(file, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=crisprpred_prediction.csv'
                    return response
                elif model_id == 'cpp':
                    try:
                        file = open(prediction_directory + 'crisprpred_plus_prediction.csv', 'r')
                    except FileNotFoundError:
                        models = PredictionModel.objects.filter(project=project)
                        messages.warning(request, "No prediction is available for this model")
                        return render(request, 'projects/project_detail.html',
                                      {'all_models': models,
                                       'project_id': project_id})
                    response = HttpResponse(file, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=crisprpred_plus_prediction.csv'
                    return response
                elif model_id == 'cps':
                    try:
                        file = open(prediction_directory + 'crisprpred_seq_prediction.csv', 'r')
                    except FileNotFoundError:
                        models = PredictionModel.objects.filter(project=project)
                        messages.warning(request, "No prediction is available for this model")
                        return render(request, 'projects/project_detail.html',
                                      {'all_models': models,
                                       'project_id': project_id})
                    response = HttpResponse(file, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=crisprpred_seq_prediction.csv'
                    return response
                else:
                    models = PredictionModel.objects.filter(project=project, pk=model_id)
                    if models:
                        model = models[0]
                        try:
                            file = open(prediction_directory + model.model_name +
                                        '_prediction.csv', 'r')
                        except FileNotFoundError:
                            models = PredictionModel.objects.filter(project=project)
                            messages.warning(request, "No prediction is available for this model")
                            return render(request, 'projects/project_detail.html',
                                          {'all_models': models,
                                           'project_id': project_id})

                        response = HttpResponse(file, content_type='text/csv')
                        response['Content-Disposition'] = 'attachment; filename=' + model.model_name + '_prediction.csv'
                        return response
            return render(request, 'error.html', {'status_code': 403})
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
                prediction_directory = 'predictions/project_' + project_id + '/'
                if model_id == 'cp':
                    try:
                        file = open(prediction_directory + 'crisprpred_prediction.csv', 'r')
                    except FileNotFoundError:
                        return Response(status=status.HTTP_404_NOT_FOUND)
                    response = HttpResponse(file, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=crisprpred_prediction.csv'
                    return response
                elif model_id == 'cpp':
                    try:
                        file = open(prediction_directory + 'crisprpred_plus_prediction.csv', 'r')
                    except FileNotFoundError:
                        return Response(status=status.HTTP_404_NOT_FOUND)
                    response = HttpResponse(file, content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename=crisprpred_plus_prediction.csv'
                    return response
                elif model_id == 'cps':
                    try:
                        file = open(prediction_directory + 'crisprpred_seq_prediction.csv', 'r')
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
                            file = open(prediction_directory + model.model_name +
                                        '_prediction.csv', 'r')
                        except FileNotFoundError:
                            return Response(status=status.HTTP_404_NOT_FOUND)

                        response = HttpResponse(file, content_type='text/csv')
                        response['Content-Disposition'] = 'attachment; filename=' + model.model_name + '_prediction.csv'
                        return response
            return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


class InstructionView(generic.View):
    @staticmethod
    def get(request):
        return render(request, 'projects/instructions.html', {})


class ResultView(generic.View):
    model = PredictionModel
    template_name = 'projects/prediction_results.html'

    def get(self, request, **kwargs):
        project_id = kwargs.get('project_id')
        model_id = kwargs.get('model_id')
        result_directory = 'static/project_' + project_id + '/'
        get_directory = '/' + result_directory
        if self.request.user.is_authenticated:
            projects = Project.objects.filter(pk=project_id, user=request.user)
            if projects:
                project = projects[0]
                if model_id == 'cp':
                    try:
                        open(result_directory + 'crisprpred_metrics.png', 'r')
                    except FileNotFoundError:
                        models = PredictionModel.objects.filter(project=project)
                        messages.warning(request, 'No results were created for this model')
                        return render(request, 'projects/project_detail.html',
                                      {'all_models': models,
                                       'project_id': project_id})
                    path_table = get_directory + 'crisprpred_metrics.png'
                    path_roc = get_directory + 'crisprpred_roc_curve.png'
                    path_pr = get_directory + 'crisprpred_pr_curve.png'
                    return render(request, self.template_name,
                                  {'path_table': path_table,
                                   'path_roc': path_roc,
                                   'path_pr': path_pr})
                elif model_id == 'cpp':
                    try:
                        open(result_directory + 'crisprpred_plus_metrics.png', 'r')
                    except FileNotFoundError:
                        models = PredictionModel.objects.filter(project=project)
                        messages.warning(request, 'No results were created for this model')
                        return render(request, 'projects/project_detail.html',
                                      {'all_models': models,
                                       'project_id': project_id})
                    path_table = get_directory + 'crisprpred_plus_metrics.png'
                    path_roc = get_directory + 'crisprpred_plus_roc_curve.png'
                    path_pr = get_directory + 'crisprpred_plus_pr_curve.png'
                    return render(request, self.template_name,
                                  {'path_table': path_table,
                                   'path_roc': path_roc,
                                   'path_pr': path_pr})
                elif model_id == 'cps':
                    try:
                        open(result_directory + 'crisprpred_seq_metrics.png', 'r')
                    except FileNotFoundError:
                        models = PredictionModel.objects.filter(project=project)
                        messages.warning(request, 'No results were created for this model')
                        return render(request, 'projects/project_detail.html',
                                      {'all_models': models,
                                       'project_id': project_id})
                    path_table = get_directory + 'crisprpred_seq_metrics.png'
                    path_roc = get_directory + 'crisprpred_seq_roc_curve.png'
                    path_pr = get_directory + 'crisprpred_seq_pr_curve.png'
                    return render(request, self.template_name,
                                  {'path_table': path_table,
                                   'path_roc': path_roc,
                                   'path_pr': path_pr})
                else:
                    models = PredictionModel.objects.filter(project=project, pk=model_id)
                    if models:
                        model = models[0]
                        try:
                            open(result_directory + model.model_name + '_metrics.png', 'r')
                        except FileNotFoundError:
                            models = PredictionModel.objects.filter(project=project)
                            messages.warning(request, 'No results were created for this model')
                            return render(request, 'projects/project_detail.html',
                                          {'all_models': models,
                                           'project_id': project_id})
                        path_table = get_directory + model.model_name + "_metrics.png"
                        path_roc = get_directory + model.model_name + "_roc_curve.png"
                        path_pr = get_directory + model.model_name + "_pr_curve.png"
                        return render(request, self.template_name,
                                      {'path_table': path_table,
                                       'path_roc': path_roc,
                                       'path_pr': path_pr})
            return render(request, 'error.html', {'status_code': 403})
        else:
            return render(request, 'login_warning.html', {})


class ResultAPIView(APIView):
    @staticmethod
    def get(request, **kwargs):
        project_id = kwargs.get('project_id')
        model_id = kwargs.get('model_id')

        result_directory = 'static/project_' + project_id + '/'
        get_directory = '/' + result_directory

        site_domain = get_current_site(request).domain

        projects = Project.objects.filter(pk=project_id, user=request.user)
        if projects:
            project = projects[0]
            if model_id == 'cp':
                try:
                    open(result_directory + 'crisprpred_metrics.png', 'r')
                except FileNotFoundError:
                    return Response(status=status.HTTP_404_NOT_FOUND)

                path_table = get_directory + 'crisprpred_metrics.png'
                path_roc = get_directory + 'crisprpred_roc_curve.png'
                path_pr = get_directory + 'crisprpred_pr_curve.png'

                response_urls = {'path_table': site_domain + path_table, 'path_roc': site_domain + path_roc,
                                 'path_pr': site_domain + path_pr}

                return JsonResponse(response_urls)

            elif model_id == 'cpp':
                try:
                    open(result_directory + 'crisprpred_plus_metrics.png', 'r')
                except FileNotFoundError:
                    return Response(status=status.HTTP_404_NOT_FOUND)

                path_table = get_directory + 'crisprpred_plus_metrics.png'
                path_roc = get_directory + 'crisprpred_plus_roc_curve.png'
                path_pr = get_directory + 'crisprpred_plus_pr_curve.png'
                response_urls = {'path_table': site_domain + path_table, 'path_roc': site_domain + path_roc,
                                 'path_pr': site_domain + path_pr}

                return JsonResponse(response_urls)

            elif model_id == 'cps':
                try:
                    open(result_directory + 'crisprpred_seq_metrics.png', 'r')
                except FileNotFoundError:
                    return Response(status=status.HTTP_404_NOT_FOUND)

                path_table = get_directory + 'crisprpred_seq_metrics.png'
                path_roc = get_directory + 'crisprpred_seq_roc_curve.png'
                path_pr = get_directory + 'crisprpred_seq_pr_curve.png'
                response_urls = {'path_table': site_domain + path_table, 'path_roc': site_domain + path_roc,
                                 'path_pr': site_domain + path_pr}

                return JsonResponse(response_urls)
            else:
                models = PredictionModel.objects.filter(project=project, pk=model_id)
                if models:
                    model = models[0]
                    try:
                        open(result_directory + model.model_name + '_metrics.png', 'r')
                    except FileNotFoundError:
                        return Response(status=status.HTTP_404_NOT_FOUND)
                    path_table = get_directory + model.model_name + "_metrics.png"
                    path_roc = get_directory + model.model_name + "_roc_curve.png"
                    path_pr = get_directory + model.model_name + "_pr_curve.png"
                    response_urls = {'path_table': site_domain + path_table, 'path_roc': site_domain + path_roc,
                                     'path_pr': site_domain + path_pr}

                    return JsonResponse(response_urls)
        return Response(status=status.HTTP_404_NOT_FOUND)
