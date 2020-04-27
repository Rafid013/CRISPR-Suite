from django.views import generic
from django.shortcuts import render


class HomePage(generic.TemplateView):
    template_name = "home.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'username': request.user.username})


class AboutPage(generic.TemplateView):
    template_name = "about.html"
