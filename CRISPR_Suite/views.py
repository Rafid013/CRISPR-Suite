from django.views import generic
from django.shortcuts import render
from django.contrib import messages


class HomePage(generic.TemplateView):
    template_name = "home.html"

    def get(self, request, *args, **kwargs):
        # check if the user is guest or not (the username is same as the session key for a guest)
        if request.user.username != request.session.session_key:
            # messages.success(request, 'Hello ' + request.user.username)
            return render(request, self.template_name, {'is_guest': False})
        else:
            # messages.success(request, 'Hello Guest')
            return render(request, self.template_name, {'is_guest': True})


class AboutPage(generic.TemplateView):
    template_name = "about.html"

    def get(self, request, *args, **kwargs):
        # check if the user is guest or not (the username is same as the session key for a guest)
        if request.user.username != request.session.session_key:
            return render(request, self.template_name, {'is_guest': False})
        else:
            return render(request, self.template_name, {'is_guest': True})
