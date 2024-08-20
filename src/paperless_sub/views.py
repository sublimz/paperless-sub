from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render
from django.views.generic import TemplateView
from documents.views import *



class PublicIndexView(TemplateView):
    template_name = "pindex.html"

    def get_frontend_language(self):
        return "fr-FR"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # Check if the user is anonymous
        if self.request.user.is_anonymous:
            user=User.objects.get(username="public")
            login(
                request=self.request,
                user=user,
                backend="django.contrib.auth.backends.ModelBackend",
            )

        context["cookie_prefix"] = "pub_"+settings.COOKIE_PREFIX
        context["username"] = User.objects.get(username="public").username
        context["full_name"] = User.objects.get(username="public").last_name
        context["styles_css"] = f"publicfrontend/{self.get_frontend_language()}/styles.css"
        context["runtime_js"] = f"publicfrontend/{self.get_frontend_language()}/runtime.js"
        context["polyfills_js"] = (
            f"publicfrontend/{self.get_frontend_language()}/polyfills.js"
        )
        context["main_js"] = f"publicfrontend/{self.get_frontend_language()}/main.js"
        context["webmanifest"] = (
            f"publicfrontend/{self.get_frontend_language()}/manifest.webmanifest"
        )
        context["apple_touch_icon"] = (
            f"publicfrontend/{self.get_frontend_language()}/apple-touch-icon.png"
        )
        return context




"""

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

def my_view(request):
    # Check if the user is anonymous
    if request.user.is_anonymous:
        # Try to get or create the user
        user, created = User.objects.get_or_create(
            username=request.session.session_key,
            defaults={
                'email': f'anonymous_user_{request.session.session_key}@example.com',
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
            }
        )

        # Log the user in
        login(request, user)

    # Now you can use the request.user object
    context = {
        'user': request.user,
    }
    return render(request, 'my_template.html', context)

"""