import os
from datetime import datetime
from subprocess import Popen

from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views import generic
from django.db.models import Q
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import PredictionModelForm
from .models import PredictionModel
from .serializer import PredictionModelGetSerializer, PredictionModelPostSerializer


class DownloadTrainingExampleView(generic.View):
    @staticmethod
    def get(request):
        file = open('static/files/sample_training_file.csv', 'r')
        response = HttpResponse(file, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=sample_training_file.csv'
        return response


class DownloadPredictionExampleView(generic.View):
    @staticmethod
    def get(request):
        file = open('static/files/sample_prediction_file.csv', 'r')
        response = HttpResponse(file, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=sample_prediction_file.csv'
        return response


class PredictionModelListView(generic.View):
    model = PredictionModel
    template_name = 'prediction_models/prediction_models_list.html'

    def get(self, request):
        if self.request.user.is_authenticated:
            models = PredictionModel.objects.filter(user=self.request.user)
            if request.user.username != request.session.session_key:
                return render(request, self.template_name, {'all_models': models, 'is_guest': False})
            else:
                return render(request, self.template_name, {'all_models': models, 'is_guest': True})
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
            if request.user.username != request.session.session_key:
                return render(request, self.template_name, {'all_models': models, 'is_guest': False})
            else:
                return render(request, self.template_name, {'all_models': models, 'is_guest': True})
        else:
            return render(request, 'login_warning.html', {})


class PublicModelListAPIView(APIView):
    @staticmethod
    def get(request):
        models = PredictionModel.objects.filter(is_public=True)
        serializer = PredictionModelGetSerializer(models, many=True)
        return Response(serializer.data)


class PredictionModelCreateView(generic.View):
    form_class = PredictionModelForm
    template_name = 'prediction_models/prediction_model_form.html'

    def get(self, request):
        # check if the user is logged in and if the user is not a guest
        if self.request.user.is_authenticated and request.user.username != request.session.session_key:
            form = self.form_class(None)
            return render(request, self.template_name, {'form': form, 'is_guest': False})
        else:
            return render(request, 'login_warning.html', {})

    def post(self, request):
        # check if the user is logged in and if the user is not a guest
        if self.request.user.is_authenticated and request.user.username != request.session.session_key:
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

                # check if the user has already created a model with the given name
                models = PredictionModel.objects.filter(model_name=model_name, user=request.user)
                if models:
                    messages.warning(request, "A model with this name already exists in this project")
                    return render(request, self.template_name, {'form': form, 'is_guest': False})

                prediction_model.save()

                log = open('Logs/creation_log_' + str(prediction_model.pk) + '.txt', 'w')

                # run the code for creating the model
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
                messages.success(request, 'An email will be sent to you after model is created\n'
                                 + ' (Please check spam if no email is available)')
                return redirect(reverse('prediction_models:models_list'))
            return render(request, self.template_name, {'form': form, 'is_guest': False})
        else:
            return render(request, 'login_warning.html', {})


class PredictionModelCreateAPIView(APIView):
    parser_classes = (MultiPartParser,)

    @staticmethod
    def post(request):
        serializer = PredictionModelPostSerializer(data=request.data)
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


class CompareView(generic.View):
    template_name = 'prediction_models/compare.html'

    def get(self, request):
        if self.request.user.is_authenticated and request.user.username != request.session.session_key:
            public_models = PredictionModel.objects.filter(is_public=True).exclude(user=self.request.user)
            user_models = PredictionModel.objects.filter(user=self.request.user)
            return render(request, self.template_name, {'public_models': public_models, 'user_models': user_models,
                                                        'is_guest': False})
        else:
            return render(request, 'login_warning.html', {})

    def post(self, request):
        if self.request.user.is_authenticated and request.user.username != request.session.session_key:
            selected_user_model_ids = request.POST.getlist('user_model')
            selected_public_model_ids = request.POST.getlist('public_model')
            selected_pretrained_model_ids = request.POST.getlist('pretrained_model')

            # check if the number of selected models is more than 5
            if len(selected_user_model_ids) + len(selected_public_model_ids) + len(selected_pretrained_model_ids) > 5:
                public_models = PredictionModel.objects.filter(is_public=True).exclude(user=self.request.user)
                user_models = PredictionModel.objects.filter(user=self.request.user)
                messages.warning(request, 'Maximum 5 models can be selected for comparison')
                return render(request, self.template_name,
                              {'public_models': public_models, 'user_models': user_models,
                               'is_guest': False})
            # prediction_file will be available if an input file is uploaded
            prediction_file = request.FILES.get('prediction_file')

            # input_sequence will be available if input is provided in textbox
            input_sequence = request.POST.get('input_sequence')

            # request_time is the time comparison is requested
            request_time = request.POST.get('request_time')

            # check if input is provided
            if not prediction_file and not input_sequence:
                public_models = PredictionModel.objects.filter(is_public=True).exclude(user=self.request.user)
                user_models = PredictionModel.objects.filter(user=self.request.user)
                messages.warning(request, 'No input provided')
                return render(request, self.template_name,
                              {'public_models': public_models, 'user_models': user_models,
                               'is_guest': False})

            selected_models = PredictionModel.objects.filter(pk__in=selected_public_model_ids + selected_user_model_ids)

            selected_model_ids = ''
            selected_model_types = ''
            selected_model_names = ''

            for selected_model in selected_models:
                selected_model_ids += str(selected_model.pk) + '_'
                selected_model_types += str(selected_model.model_type) + '_'
                selected_model_names += selected_model.model_name + '_'

            if 'cp' in selected_pretrained_model_ids:
                selected_model_ids += 'cp_'
                selected_model_types += '1_'
                selected_model_names += 'CRISPRpred_'

            if 'cpp' in selected_pretrained_model_ids:
                selected_model_ids += 'cpp_'
                selected_model_types += '2_'
                selected_model_names += 'CRISPRpred++_'

            if 'cps' in selected_pretrained_model_ids:
                selected_model_ids += 'cps_'
                selected_model_types += '3_'
                selected_model_names += 'CRISPRpred(SEQ)_'

            selected_model_ids = selected_model_ids[:len(selected_model_ids) - 1]
            selected_model_types = selected_model_types[:len(selected_model_types) - 1]
            selected_model_names = selected_model_names[:len(selected_model_names) - 1]
            comparison_directory = 'comparisons/user_' + str(request.user.pk) + '/'

            # if the prediction_file does not exist, save the input provided in textbox to a file
            if prediction_file:
                fs = FileSystemStorage()
                filename = fs.save(comparison_directory + prediction_file.name, prediction_file)
            else:
                # make directory if it does not exist
                if not os.path.isdir('media/' + comparison_directory):
                    os.mkdir('media/' + comparison_directory)
                f = open('media/' + comparison_directory + 'user_' + str(request.user.pk) + '.csv', 'w')
                f.write('sgRNA,label\n')
                f.write(input_sequence)
                f.close()
                filename = comparison_directory + 'user_' + str(request.user.pk) + '.csv'

            # save the time the comparison was requested to a file
            f = open('media/' + comparison_directory + 'compare_time.txt', 'w')
            f.write(request_time)
            f.close()

            log = open('Logs/comparison_log_' + str(request.user.pk) + '.txt', 'w')

            # run the code for comparison
            Popen(['python', 'CRISPR_Methods/compare.py', str(request.user.pk), str(selected_model_ids),
                   str(selected_model_types), str(selected_model_names), str(filename), request.user.email],
                  stdout=log, stderr=log)
            messages.success(request, 'An email will be sent to you after comparison is completed\n'
                             + ' (Please check spam if no email is available)')
            return redirect(reverse('prediction_models:compare'))
        else:
            return render(request, 'login_warning.html', {})


class CompareAPIView(APIView):
    parser_classes = (MultiPartParser,)

    @staticmethod
    def get(request):
        public_models = PredictionModel.objects.filter(is_public=True).exclude(user=request.user)
        user_models = PredictionModel.objects.filter(user=request.user)
        models = public_models | user_models
        serializer = PredictionModelGetSerializer(models, many=True)
        return Response(serializer.data)

    @staticmethod
    def post(request):
        model_ids = request.POST.getlist('model')
        prediction_file = request.FILES.get('prediction_file')
        request_time = request.POST.get('request_time')
        selected_models = PredictionModel.objects.filter(pk__in=model_ids)

        if len(selected_models) > 5:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        selected_model_ids = ''
        selected_model_types = ''
        selected_model_names = ''

        for selected_model in selected_models:
            selected_model_ids += str(selected_model.pk) + '_'
            selected_model_types += str(selected_model.model_type) + '_'
            selected_model_names += selected_model.model_name + '_'

        selected_model_ids = selected_model_ids[:len(selected_model_ids) - 1]
        selected_model_types = selected_model_types[:len(selected_model_types) - 1]
        selected_model_names = selected_model_names[:len(selected_model_names) - 1]

        comparison_directory = 'comparisons/user_' + str(request.user.pk) + '/'

        fs = FileSystemStorage()
        filename = fs.save(comparison_directory + prediction_file.name, prediction_file)

        # save the time the comparison was requested to a file
        f = open('media/' + comparison_directory + 'compare_time.txt', 'w')
        f.write(request_time)
        f.close()

        log = open('Logs/comparison_log_' + str(request.user.pk) + '.txt', 'w')
        Popen(['python', 'CRISPR_Methods/compare.py', str(request.user.pk), str(selected_model_ids),
               str(selected_model_types), str(selected_model_names), str(filename), request.user.email],
              stdout=log, stderr=log)
        return Response(status=status.HTTP_200_OK)


class CompareResultView(generic.View):
    template_name = 'prediction_models/results.html'

    def get(self, request):
        result_directory = 'static/user_' + str(request.user.pk) + '/'
        get_directory = '/' + result_directory
        if self.request.user.is_authenticated and request.user.username != request.session.session_key:
            try:
                open(result_directory + 'comparison_metrics.png', 'rb')
            except FileNotFoundError:
                messages.warning(request, "No comparisons available")
                return redirect(reverse('prediction_models:compare'))
            model_info = "Comparison Result"
            path_table = get_directory + "comparison_metrics.png"
            path_roc = get_directory + "comparison_roc_curve.png"
            path_pr = get_directory + "comparison_pr_curve.png"

            f = open('media/comparisons/user_' + str(request.user.pk) + '/compare_time.txt', 'r')
            request_time = f.readline()

            return render(request, self.template_name,
                          {'path_table': path_table,
                           'path_roc': path_roc,
                           'path_pr': path_pr,
                           'model_info': model_info,
                           'request_time': request_time,
                           'is_guest': False})
        else:
            return render(request, 'login_warning.html', {})


class CompareResultAPIView(APIView):
    @staticmethod
    def get(request):
        result_directory = 'static/user_' + str(request.user.pk) + '/'
        get_directory = '/' + result_directory

        site_domain = get_current_site(request).domain

        try:
            open(result_directory + 'comparison_metrics.png', 'rb')
        except FileNotFoundError:
            return Response(status=status.HTTP_404_NOT_FOUND)
        path_table = get_directory + "comparison_metrics.png"
        path_roc = get_directory + "comparison_roc_curve.png"
        path_pr = get_directory + "comparison_pr_curve.png"
        response_urls = {'path_table': site_domain + path_table, 'path_roc': site_domain + path_roc,
                         'path_pr': site_domain + path_pr}

        return JsonResponse(response_urls)


class PredictView(generic.View):
    model = PredictionModel
    template_name = 'prediction_models/prediction.html'

    def get(self, request, **kwargs):

        if self.request.user.is_authenticated:
            model_id = kwargs.get('model_id')
            if model_id == 'cp':
                model_name = 'CRISPRpred'
                if request.user.username != request.session.session_key:
                    return render(request, self.template_name, {'model': model_name, 'is_guest': False})
                else:
                    return render(request, self.template_name, {'model': model_name, 'is_guest': True})
            elif model_id == 'cpp':
                model_name = 'CRISPRpred++'
                if request.user.username != request.session.session_key:
                    return render(request, self.template_name, {'model': model_name, 'is_guest': False})
                else:
                    return render(request, self.template_name, {'model': model_name, 'is_guest': True})
            elif model_id == 'cps':
                model_name = 'CRISPRpred(SEQ)'
                if request.user.username != request.session.session_key:
                    return render(request, self.template_name, {'model': model_name, 'is_guest': False})
                else:
                    return render(request, self.template_name, {'model': model_name, 'is_guest': True})
            else:
                models = PredictionModel.objects.filter(
                    Q(pk=model_id, is_public=True) | Q(user=request.user, pk=model_id))
                if models:
                    model_name = models[0].model_name
                    try:
                        open('saved_models/' + str(model_id) + '.pkl', 'rb')
                    except FileNotFoundError:
                        messages.warning(request, "Training haven\'t finished yet")
                        return redirect(request.META.get('HTTP_REFERER'))
                    if request.user.username != request.session.session_key:
                        return render(request, self.template_name, {'model': model_name, 'is_guest': False})
                    else:
                        return render(request, self.template_name, {'model': model_name, 'is_guest': True})
                return render(request, 'error.html', {'status_code': 403})
        else:
            return render(request, 'login_warning.html', {})

    def post(self, request, **kwargs):
        if self.request.user.is_authenticated:
            prediction_file = request.FILES.get('prediction_file')
            input_sequence = request.POST.get('input_sequence')
            request_time = request.POST.get('request_time')
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
                prediction_models = PredictionModel.objects.filter(
                    Q(pk=model_id, is_public=True) | Q(user=request.user, pk=model_id))
                if prediction_models:
                    prediction_model = prediction_models[0]
                    prediction_model.used_for_prediction_count += 1
                    prediction_model.recent_running_time = datetime.now()
                    model_type = prediction_model.model_type
                    model_name = prediction_model.model_name
                    prediction_model.save()
                else:
                    return render(request, 'error.html', {'status_code': 404})

            if not prediction_file and not input_sequence:
                messages.warning(request, 'No input provided')
                if request.user.username != request.session.session_key:
                    return render(request, self.template_name, {'model': model_name, 'is_guest': False})
                else:
                    return render(request, self.template_name, {'model': model_name, 'is_guest': True})

            if prediction_file:
                fs = FileSystemStorage()
                filename = fs.save('predictions/model_' + str(model_id) + '/' + prediction_file.name, prediction_file)
                f = open('media/predictions/model_' + str(model_id) + '/' + prediction_file.name, 'r')
                if request.user.username == request.session.session_key:
                    line_cnt = 0
                    for _ in f:
                        line_cnt += 1
                    if line_cnt > 50:
                        messages.warning(request, "You can't provide more than 50 sequences as input")
                        return render(request, self.template_name, {'model': model_name, 'is_guest': True})
            else:
                if request.user.username == request.session.session_key:
                    line_cnt = str(input_sequence).count('\n')
                    if line_cnt > 50:
                        messages.warning(request, "You can't provide more than 50 sequences as input")
                        return render(request, self.template_name, {'model': model_name, 'is_guest': True})

                if not os.path.isdir('media/predictions/model_' + str(model_id)):
                    os.mkdir('media/predictions/model_' + str(model_id))

                # check if the user is a guest or not
                if request.user.username != request.session.session_key:
                    f = open('media/predictions/model_' + str(model_id) + '/user_' + str(request.user.pk) + '.csv', 'w')
                else:
                    f = open('media/predictions/model_' + str(model_id) + '/user_' + str(request.user.username) +
                             '.csv', 'w')
                if ',' in input_sequence:
                    f.write('sgRNA,label\n')
                else:
                    f.write('sgRNA\n')
                f.write(input_sequence)
                f.close()

                if request.user.username != request.session.session_key:
                    filename = 'predictions/model_' + str(model_id) + '/user_' + str(request.user.pk) + '.csv'
                    if not os.path.isdir('predictions/user_' + str(request.user.pk)):
                        os.mkdir('predictions/user_' + str(request.user.pk))
                    f = open('predictions/user_' + str(request.user.pk) + '/' + str(model_id) + '_predict_time.txt',
                             'w')
                    f.write(request_time)
                    f.close()
                else:
                    filename = 'predictions/model_' + str(model_id) + '/user_' + str(request.user.username) + '.csv'
                    if not os.path.isdir('predictions/user_' + str(request.user.username)):
                        os.mkdir('predictions/user_' + str(request.user.username))
                    f = open('predictions/user_' + str(request.user.username) + '/' + str(model_id) +
                             '_predict_time.txt', 'w')
                    f.write(request_time)
                    f.close()

            if request.user.username != request.session.session_key:
                log = open('Logs/prediction_log_' + str(request.user.pk) + '_' + str(model_id) + '.txt', 'w')
                Popen(['python', 'CRISPR_Methods/predict.py', str(request.user.pk), str(model_id),
                       str(model_type), model_name,
                       str(filename), request.user.email], stdout=log, stderr=log)
                messages.success(request, 'An email will be sent to you after prediction is completed\n'
                                 + ' (Please check spam if no email is available)')
            else:
                log = open('Logs/prediction_log_' + str(request.user.username) + '_' + str(model_id) + '.txt', 'w')
                Popen(['python', 'CRISPR_Methods/predict.py', str(request.user.username), str(model_id),
                       str(model_type), model_name,
                       str(filename), request.user.email], stdout=log, stderr=log)
                messages.success(request, 'The prediction results will be available soon, wait a few minutes')

            return redirect('home')
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
            prediction_models = PredictionModel.objects.filter(
                Q(pk=model_id, is_public=True) | Q(user=request.user, pk=model_id))
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

        log = open('Logs/prediction_log_' + str(request.user.pk) + '_' + str(model_id) + '.txt', 'w')
        Popen(['python', 'CRISPR_Methods/predict.py', str(request.user.pk), str(model_id),
               str(model_type), model_name,
               str(filename), request.user.email], stdout=log, stderr=log)

        return Response(status=status.HTTP_202_ACCEPTED)


class DownloadView(generic.View):
    def get(self, request, **kwargs):
        model_id = kwargs.get('model_id')
        if self.request.user.is_authenticated:
            if request.user.username == request.session.session_key:
                user_id = request.user.username
            else:
                user_id = request.user.pk
            prediction_directory = 'predictions/user_' + str(user_id) + '/'
            if model_id != 'cp' and model_id != 'cpp' and model_id != 'cps':
                models = PredictionModel.objects.filter(Q(pk=model_id, is_public=True) | Q(user=request.user,
                                                                                           pk=model_id))
            else:
                models = None
            if models or model_id == 'cp' or model_id == 'cpp' or model_id == 'cps':
                try:
                    file = open(prediction_directory + str(model_id) +
                                '_prediction.csv', 'r')
                except FileNotFoundError:
                    messages.warning(request, "No prediction is available for this model yet")
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
            models = PredictionModel.objects.filter(Q(pk=model_id, is_public=True) | Q(user=request.user, pk=model_id))
        else:
            models = None
        if models or model_id == 'cp' or model_id == 'cpp' or model_id == 'cps':
            try:
                file = open(prediction_directory + str(model_id) + '_prediction.csv', 'r')
            except FileNotFoundError:
                return Response(status=status.HTTP_404_NOT_FOUND)

            response = HttpResponse(file, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=' + str(model_id) + '_prediction.csv'
            return response
        return Response(status=status.HTTP_404_NOT_FOUND)


class InstructionView(generic.View):
    @staticmethod
    def get(request):
        if request.user.username != request.session.session_key:
            return render(request, 'prediction_models/instructions.html', {'is_guest': False})
        else:
            return render(request, 'prediction_models/instructions.html', {'is_guest': True})


class ResultView(generic.View):
    model = PredictionModel
    template_name = 'prediction_models/results.html'

    def get(self, request, **kwargs):
        model_id = kwargs.get('model_id')
        if self.request.user.is_authenticated:
            if request.user.username != request.session.session_key:
                user_id = request.user.pk
            else:
                user_id = request.user.username

            result_directory = 'static/user_' + str(user_id) + '/'
            get_directory = '/' + result_directory

            if model_id != 'cp' and model_id != 'cpp' and model_id != 'cps':
                models = PredictionModel.objects.filter(
                    Q(pk=model_id, is_public=True) | Q(user=request.user, pk=model_id))
            else:
                models = None
            if models or model_id == 'cp' or model_id == 'cpp' or model_id == 'cps':
                try:
                    open(result_directory + str(model_id) + '_metrics.png', 'r')
                except FileNotFoundError:
                    messages.warning(request, 'No results were created for this model yet')
                    return redirect(request.META.get('HTTP_REFERER'))
                path_table = get_directory + str(model_id) + "_metrics.png"
                path_roc = get_directory + str(model_id) + "_roc_curve.png"
                path_pr = get_directory + str(model_id) + "_pr_curve.png"

                model_info = 'Results for '
                if model_id == 'cp':
                    model_info += 'Pretrained Model: '
                    model_info += 'CRISPRpred'
                elif model_id == 'cpp':
                    model_info += 'Pretrained Model: '
                    model_info += 'CRISPRpred++'
                elif model_id == 'cps':
                    model_info += 'Pretrained Model: '
                    model_info += 'CRISPRpred(SEQ)'
                elif models[0].user == request.user:
                    model_info += 'Your Model: '
                    model_info += models[0].model_name
                else:
                    model_info += 'Public Model: '
                    model_info += models[0].model_name
                    model_info += ' Owned by '
                    model_info += models[0].user.username

                f = open('predictions/user_' + str(user_id) + '/' + str(model_id) + '_predict_time.txt', 'r')
                request_time = f.readline()

                return render(request, self.template_name,
                              {'path_table': path_table,
                               'path_roc': path_roc,
                               'path_pr': path_pr,
                               'model_info': model_info,
                               'request_time': request_time,
                               'is_guest': False})
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
            models = PredictionModel.objects.filter(Q(pk=model_id, is_public=True) | Q(user=request.user, pk=model_id))
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


class DeleteView(generic.View):
    @staticmethod
    def get(request, **kwargs):
        if request.user.is_authenticated:
            model_id = kwargs.get('model_id')
            model = PredictionModel.objects.filter(pk=model_id, user=request.user)
            if model:
                model[0].delete()
                return redirect(reverse('prediction_models:models_list'))
            return render(request, 'error.html', {'status_code': 403})
        else:
            return render(request, 'login_warning.html', {})


class DeleteAPIView(APIView):
    @staticmethod
    def post(request, **kwargs):
        model_id = kwargs.get('model_id')
        model = PredictionModel.objects.filter(pk=model_id, user=request.user)
        if model:
            model[0].delete()
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)
