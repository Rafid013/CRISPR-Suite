from django.views import generic
from django.shortcuts import render


class HomePage(generic.TemplateView):
    template_name = "home.html"

    def get(self, request, *args, **kwargs):
        if request.user.username != request.session.session_key:
            return render(request, self.template_name, {'username': request.user.username,
                                                        'is_guest': "False"})
        return render(request, self.template_name, {'username': 'Guest',
                                                    'is_guest': "True"})


class AboutPage(generic.TemplateView):
    template_name = "about.html"
