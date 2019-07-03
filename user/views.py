from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from .forms import UserLogInForm, UserSignUpForm


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

            # finally save
            user.email = email
            user.username = username
            user.set_password(password)
            user.save()

            # authenticate
            user = authenticate(request, username=username, password=password)

            if user is not None:  # goes to this condition only if authentication works
                if user.is_active:
                    login(request, user)
                    return redirect('projects:index')

        return render(request, self.template_name, {'form': form})


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
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    @staticmethod
    def get(request):
        logout(request)
        return redirect('home')
