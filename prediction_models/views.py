from datetime import datetime
from subprocess import Popen

from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views import generic
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import PredictionModelForm
from .models import PredictionModel
from .serializer import PredictionModelGetSerializer, PredictionModelPostSerializer


class PredictionModelListView(generic.View):
    model = PredictionModel
    template_name = 'prediction_models/prediction_models_list.html'

    def get(self, request):
        if self.request.user.is_authenticated:
            models = PredictionModel.objects.filter(user=self.request.user)
            return render(request, self.template_name, {'all_models': models})
        else:
            return render(request, 'login_warning.html', {})


class PredictionModelListAPIView(APIView):
    @staticmethod
    def get(request):
        models = PredictionModel.objects.filter(user=request.user)
        serializer = PredictionModelGetSerializer(models, many=True)
        return Response(serializer.data)


class PublicModelListView(generic.View):
    model = PredictionModel
    template_name = 'prediction_models/public_models_list.html'

    def get(self, request):
        if self.request.user.is_authenticated:
            models = PredictionModel.objects.filter(is_public=True)
            return render(request, self.template_name, {'all_models': models})
        else:
            return render(request, 'login_warning.html', {})


class PredictionModelCreateView(generic.View):
    form_class = PredictionModelForm
    template_name = 'prediction_models/prediction_model_form.html'

    def get(self, request):
        if self.request.user.is_authenticated:
            form = self.form_class(None)
            return render(request, self.template_name, {'form': form})
        else:
            return render(request, 'login_warning.html', {})

    def post(self, request):
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
                prediction_model.user = request.user

                models = PredictionModel.objects.filter(model_name=model_name, user=request.user)
                if models:
                    messages.warning(request, "A model with this name already exists in this project")
                    return render(request, self.template_name, {'form': form})

                prediction_model.save()

                log = open('Logs/creation_log_' + str(prediction_model.pk) + '.txt', 'w')
                if prediction_model.model_type == 1:
                    Popen(['python', 'CRISPR_Methods/train_crisprpred.py', str(prediction_model.pk),
                           prediction_model.model_name,
                           str(prediction_model.training_file), request.user.email], stdout=log, stderr=log)
                elif prediction_model.model_type == 2:
                    Popen(['python', 'CRISPR_Methods/train_crisprpred_plus.py', str(prediction_model.pk),
                           prediction_model.model_name,
                           str(prediction_model.training_file), request.user.email], stdout=log, stderr=log)
                else:
                    Popen(['python', 'CRISPR_Methods/train_crisprpred_seq.py', str(prediction_model.pk),
                           prediction_model.model_name,
                           str(prediction_model.training_file), request.user.email], stdout=log, stderr=log)
                return redirect(reverse('prediction_models:models_list'))
            return render(request, self.template_name, {'form': form})
        else:
            return render(request, 'login_warning.html', {})


class PredictionModelCreateAPIView(APIView):
    parser_classes = (MultiPartParser,)

    @staticmethod
    def post(request):
        serializer = PredictionModelPostSerializer(data=request.data)
        print(serializer)
        if serializer.is_valid():
            model_name = serializer.validated_data['model_name']
            model_type = serializer.validated_data['model_type']
            training_file = request.FILES.get('training_file')
            consent_for_file = serializer.validated_data['consent_for_file']
            is_public = serializer.validated_data['is_public']

            models = PredictionModel.objects.filter(model_name=model_name, user=request.user)
            if models:
                return Response(status=status.HTTP_403_FORBIDDEN)
            prediction_model = PredictionModel(model_name=model_name, model_type=model_type,
                                               training_file=training_file, consent_for_file=consent_for_file,
                                               is_public=is_public, user=request.user)
            prediction_model.save()

            log = open('Logs/creation_log_' + str(prediction_model.pk) + '.txt', 'w')
            if prediction_model.model_type == 1:
                Popen(['python', 'CRISPR_Methods/train_crisprpred.py', str(prediction_model.pk),
                       prediction_model.model_name,
                       str(prediction_model.training_file), request.user.email], stdout=log, stderr=log)
            elif prediction_model.model_type == 2:
                Popen(['python', 'CRISPR_Methods/train_crisprpred_plus.py', str(prediction_model.pk),
                       prediction_model.model_name,
                       str(prediction_model.training_file), request.user.email], stdout=log, stderr=log)
            else:
                Popen(['python', 'CRISPR_Methods/train_crisprpred_seq.py', str(prediction_model.pk),
                       prediction_model.model_name,
                       str(prediction_model.training_file), request.user.email], stdout=log, stderr=log)
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)


class PredictView(generic.View):
    model = PredictionModel
    template_name = 'prediction_models/prediction.html'
    prev_url = None

    def get(self, request, **kwargs):
        if self.request.user.is_authenticated:
            model_id = kwargs.get('model_id')
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
                models = PredictionModel.objects.filter(user=request.user, pk=model_id)
                if models:
                    model_name = models[0].model_name
                    try:
                        open('saved_models/' + str(model_id) + '.pkl', 'rb')
                    except FileNotFoundError:
                        messages.warning(request, "Training haven\'t finished yet")
                        return redirect(request.META.get('HTTP_REFERER'))
                    return render(request, self.template_name, {'model': model_name})
                return render(request, 'error.html', {'status_code': 403})
        else:
            return render(request, 'login_warning.html', {})

    def post(self, request, **kwargs):
        if self.request.user.is_authenticated:
            prediction_file = request.FILES.get('prediction_file')
            model_id = kwargs.get('model_id')
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
                prediction_models = PredictionModel.objects.filter(user=request.user, pk=model_id)
                if prediction_models:
                    prediction_model = prediction_models[0]
                    prediction_model.used_for_prediction_count += 1
                    prediction_model.recent_running_time = datetime.now()
                    model_type = prediction_model.model_type
                    model_name = prediction_model.model_name
                    prediction_model.save()
                else:
                    return render(request, 'error.html', {'status_code': 404})

            fs = FileSystemStorage()
            filename = fs.save('model_' + str(model_id) + '/' + prediction_file.name, prediction_file)

            log = open('Logs/prediction_log_' + str(request.user.pk) + '_' + str(model_id) + '_prediction.txt', 'w')
            Popen(['python', 'CRISPR_Methods/predict.py', str(request.user.pk), str(model_id),
                   str(model_type), model_name,
                   str(filename), request.user.email], stdout=log, stderr=log)

            return redirect(reverse('prediction_models:models_list'))
        else:
            return render(request, 'login_warning.html', {})


class PredictAPIView(APIView):
    parser_classes = (MultiPartParser,)

    @staticmethod
    def post(request, **kwargs):
        prediction_file = request.FILES.get('prediction_file')
        model_id = kwargs.get('model_id')
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
            prediction_models = PredictionModel.objects.filter(user=request.user, pk=model_id)
            if prediction_models:
                prediction_model = prediction_models[0]
                prediction_model.used_for_prediction_count += 1
                prediction_model.recent_running_time = datetime.now()
                model_type = prediction_model.model_type
                model_name = prediction_model.model_name
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)

        fs = FileSystemStorage()
        filename = fs.save('model_' + str(model_id) + '/' + prediction_file.name, prediction_file)

        log = open('Logs/prediction_log_' + str(request.user.pk) + '_' + str(model_id) + '_prediction.txt', 'w')
        Popen(['python', 'CRISPR_Methods/predict.py', str(request.user.pk), str(model_id),
               str(model_type), model_name,
               str(filename), request.user.email], stdout=log, stderr=log)

        return Response(status=status.HTTP_202_ACCEPTED)


class DownloadView(generic.View):
    def get(self, request, **kwargs):
        model_id = kwargs.get('model_id')
        user_id = request.user.pk
        if self.request.user.is_authenticated:
            prediction_directory = 'predictions/user_' + str(user_id) + '/'
            if model_id != 'cp' and model_id != 'cpp' and model_id != 'cps':
                models = PredictionModel.objects.filter(user=request.user, pk=model_id)
            else:
                models = None
            if models or model_id == 'cp' or model_id == 'cpp' or model_id == 'cps':
                try:
                    file = open(prediction_directory + str(model_id) +
                                '_prediction.csv', 'r')
                except FileNotFoundError:
                    messages.warning(request, "No prediction is available for this model")
                    return redirect(request.META.get('HTTP_REFERER'))

                response = HttpResponse(file, content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename=' + str(model_id) + '_prediction.csv'
                return response
            return render(request, 'error.html', {'status_code': 404})
        else:
            return render(request, 'login_warning.html', {})


class DownloadAPIView(APIView):
    @staticmethod
    def get(request, **kwargs):
        model_id = kwargs.get('model_id')
        user_id = request.user.pk
        prediction_directory = 'predictions/user_' + str(user_id) + '/'
        if model_id != 'cp' and model_id != 'cpp' and model_id != 'cps':
            models = PredictionModel.objects.filter(user=request.user, pk=model_id)
        else:
            models = None
        if models or model_id == 'cp' or model_id == 'cpp' or model_id == 'cps':
            try:
                file = open(prediction_directory + str(model_id) + '_prediction.csv', 'r')
            except FileNotFoundError:
                messages.warning(request, "No prediction is available for this model")
                return redirect(reverse('prediction_models:models_list'))

            response = HttpResponse(file, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=' + str(model_id) + '_prediction.csv'
            return response
        return Response(status=status.HTTP_404_NOT_FOUND)


class InstructionView(generic.View):
    @staticmethod
    def get(request):
        return render(request, 'prediction_models/instructions.html', {})


class ResultView(generic.View):
    model = PredictionModel
    template_name = 'prediction_models/prediction_results.html'

    def get(self, request, **kwargs):
        model_id = kwargs.get('model_id')
        user_id = request.user.pk
        result_directory = 'static/user_' + str(user_id) + '/'
        get_directory = '/' + result_directory
        if self.request.user.is_authenticated:
            if model_id != 'cp' and model_id != 'cpp' and model_id != 'cps':
                models = PredictionModel.objects.filter(user=request.user, pk=model_id)
            else:
                models = None
            if models or model_id == 'cp' or model_id == 'cpp' or model_id == 'cps':
                try:
                    open(result_directory + str(model_id) + '_metrics.png', 'r')
                except FileNotFoundError:
                    messages.warning(request, 'No results were created for this model')
                    return redirect(request.META.get('HTTP_REFERER'))
                path_table = get_directory + str(model_id) + "_metrics.png"
                path_roc = get_directory + str(model_id) + "_roc_curve.png"
                path_pr = get_directory + str(model_id) + "_pr_curve.png"
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
        model_id = kwargs.get('model_id')
        user_id = request.user.pk
        result_directory = 'static/user_' + str(user_id) + '/'
        get_directory = '/' + result_directory

        site_domain = get_current_site(request).domain

        if model_id != 'cp' and model_id != 'cpp' and model_id != 'cps':
            models = PredictionModel.objects.filter(user=request.user, pk=model_id)
        else:
            models = None
        if models or model_id == 'cp' or model_id == 'cpp' or model_id == 'cps':
            try:
                open(result_directory + str(model_id) + '_metrics.png', 'r')
            except FileNotFoundError:
                return Response(status=status.HTTP_404_NOT_FOUND)
            path_table = get_directory + str(model_id) + "_metrics.png"
            path_roc = get_directory + str(model_id) + "_roc_curve.png"
            path_pr = get_directory + str(model_id) + "_pr_curve.png"
            response_urls = {'path_table': site_domain + path_table, 'path_roc': site_domain + path_roc,
                             'path_pr': site_domain + path_pr}

            return JsonResponse(response_urls)
        return Response(status=status.HTTP_404_NOT_FOUND)
