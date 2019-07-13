from django.shortcuts import render, redirect, Http404, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.generic import View
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from .forms import UserLogInForm, UserSignUpForm, PasswordResetForm, SetPasswordForm
from .token import activation_token
from django.contrib import messages


# Create your views here.
class UserSignUpView(View):
    form_class = UserSignUpForm
    template_name = 'user/signup_form.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            # save data locally, so commit=False
            user = form.save(commit=False)

            # clean data
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']

            if password != confirm_password:
                messages.warning(request, "Password and Confirm Password does not match")
                return render(request, self.template_name, {'form': form})

            if email and User.objects.filter(email=email).exclude(username=username).exists():
                messages.warning(request, "An account already exists with this email")
                return render(request, self.template_name, {'form': form})

            # finally save
            user.email = email
            user.username = username
            user.set_password(password)
            user.is_active = False
            user.save()

            site_name = get_current_site(request)
            message = render_to_string('user/account_activation_email.html', {
                "user": user,
                "domain": site_name.domain,
                "uid": user.pk,
                "token": activation_token.make_token(user)
            })
            subject = "Confirmation Email for CRISPR Suite Account"
            email_to = email
            to_list = [email_to]
            email_from = settings.EMAIL_HOST_USER
            send_mail(subject, message, email_from, to_list, fail_silently=False)
            return redirect('user:account_activation_sent')

        return render(request, self.template_name, {'form': form})


def account_activation_sent(request):
    return render(request, 'user/account_activation_sent.html')


def activate(request, uid, token):
    try:
        user = get_object_or_404(User, pk=uid)
    except:
        raise Http404("No user found")
    if user is not None and activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('home')
    else:
        return render(request, 'user/account_activation_invalid.html')


class UserLogInView(View):
    form_class = UserLogInForm
    template_name = 'user/login_form.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            # clean data
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # authenticate
            user = authenticate(request, username=username, password=password)

            if user is not None:  # goes to this condition only if authentication works
                if user.is_active:
                    login(request, user)
                    return redirect('home')
                else:
                    return redirect('user:account_activation_sent')
        messages.warning(request, "Username and Password does not match or Account has not been verified yet")
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    @staticmethod
    def get(request):
        logout(request)
        return redirect('home')


class PasswordResetView(View):
    form_class = PasswordResetForm
    template_name = "user/password-reset.html"

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            # clean data
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                site_name = get_current_site(request)
                message = render_to_string('user/password-reset-email.html', {
                    "user": user,
                    "domain": site_name.domain,
                    "uid": user.pk,
                    "token": activation_token.make_token(user)
                })
                subject = "Reset your password"
                email_to = email
                to_list = [email_to]
                email_from = settings.EMAIL_HOST_USER
                send_mail(subject, message, email_from, to_list, fail_silently=False)
                return redirect('user:password-reset-done')

            except User.DoesNotExist:
                messages.warning(request, "No account with this email exists!")
                return render(request, self.template_name, {'form': form})
        return render(request, self.template_name, {'form': form})


class PasswordResetDoneView(View):
    @staticmethod
    def get(request):
        return render(request,'user/password-reset-done.html')


class PasswordResetConfirmView(View):
    template_name = "user/password-reset-confirm.html"
    form_class = SetPasswordForm

    def get(self, request,**kwargs):
        form = self.form_class(None)
        uid = kwargs.get('uid')
        token = kwargs.get('token')
        try:
            user = get_object_or_404(User, pk=uid)
        except:
            raise Http404("No user found")
        if user is not None and activation_token.check_token(user, token):
            return render(request, self.template_name, {'form': form})
        else:
            return render(request, 'user/password-reset-invalid.html')

    def post(self,request,**kwargs):
        uid = kwargs.get('uid')
        form = self.form_class(request.POST)
        if form.is_valid():
            # clean data
            new_password = form.cleaned_data['new_password']
            confirm_new_password = form.cleaned_data['confirm_new_password']

            if new_password != confirm_new_password:
                messages.warning(request, "New password and confirm new password does not match")
                return render(request, self.template_name, {'form': form})

            try:
                user = get_object_or_404(User, pk=uid)
            except:
                raise Http404("No user found")
            if user is not None:
                user.set_password(new_password)
                user.save()
                login(request, user)
                messages.success(request,"Successfully changed password")
                return redirect('home')

        return render(request, self.template_name, {'form': form})
