from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.models import User
from documents.views import *



class PublicIndexView(TemplateView):
    template_name = "pindex.html"

    def get_frontend_language(self):
        if hasattr(
            self.request.user,
            "ui_settings",
        ) and self.request.user.ui_settings.settings.get("language"):
            lang = self.request.user.ui_settings.settings.get("language")
        else:
            lang = get_language()
        # This is here for the following reason:
        # Django identifies languages in the form "en-us"
        # However, angular generates locales as "en-US".
        # this translates between these two forms.
        if "-" in lang:
            first = lang[: lang.index("-")]
            second = lang[lang.index("-") + 1 :]
            return f"{first}-{second.upper()}"
        else:
            return lang

    def get_context_data(self, **kwargs):

        if request.user.is_anonymous:
            # Try to get or create the user
            user, created = User.objects.get_or_create(
                username=request.session.session_key,
                defaults=User.objects.filter(username='public')
            )
            login(request,user)
            context = super().get_context_data(**kwargs)
            context["cookie_prefix"] = settings.COOKIE_PREFIX
            context["username"] = self.request.user.username
            context["full_name"] = self.request.user.get_full_name()
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
