import logging

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.middleware import PersistentRemoteUserMiddleware
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin
from rest_framework import authentication
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger("paperless.auth")


class AutoLoginMiddleware(MiddlewareMixin):
    def process_request(self, request: HttpRequest):
        # Dont use auto-login with token request
        if request.path.startswith("/api/token/") and request.method == "POST":
            return None
        try:
            request.user = User.objects.get(username=settings.AUTO_LOGIN_USERNAME)
            auth.login(
                request=request,
                user=request.user,
                backend="django.contrib.auth.backends.ModelBackend",
            )
        except User.DoesNotExist:
            pass


class AngularApiAuthenticationOverride(authentication.BaseAuthentication):
    """This class is here to provide authentication to the angular dev server
    during development. This is disabled in production.
    """

    def authenticate(self, request):
        if (
            settings.DEBUG
            and "Referer" in request.headers
            and request.headers["Referer"].startswith("http://localhost:4200/")
        ):
            user = User.objects.filter(is_staff=True).first()
            logger.debug(f"Auto-Login with user {user}")
            return (user, None)
        else:
            return None


class HttpRemoteUserMiddleware(PersistentRemoteUserMiddleware):
    """This class allows authentication via HTTP_REMOTE_USER which is set for
    example by certain SSO applications.
    """

    header = settings.HTTP_REMOTE_USER_HEADER_NAME

    def process_request(self, request: HttpRequest) -> None:
        # If remote user auth is enabled only for the frontend, not the API,
        # then we need dont want to authenticate the user for API requests.
        if (
            "/api/" in request.path
            and "paperless.auth.PaperlessRemoteUserAuthentication"
            not in settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"]
        ):
            return
        return super().process_request(request)


class PaperlessRemoteUserAuthentication(authentication.RemoteUserAuthentication):
    """
    REMOTE_USER authentication for DRF which overrides the default header.
    """

    header = settings.HTTP_REMOTE_USER_HEADER_NAME


class DefaultAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Vérifiez si l'utilisateur est authentifié
        user = request.user
        if user.is_authenticated:
            return (user, None)

        # Si aucun utilisateur n'est authentifié, utilisez l'utilisateur par défaut
        try:
            user = User.objects.filter(first_name="public").first()
            return (user, None)
        except user.DoesNotExist:
            raise AuthenticationFailed('No default user found')


class PublicAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Vérifier si le Referer contient 'public'
        if request.path.startswith("/papi/"):   
            # Récupérer l'utilisateur public
            try:
                user = User.objects.get(username='public')
                return (user, None)
            except user.DoesNotExist:
                public_user = User(id=user_id, username='public',firstname='public',lastname='public')
                public_user.set_unusable_password()
                public_user.save()
                return public_user

        # Sinon, essayer l'authentification standard
        else:
            return None


class PublicAuthenticationSave(BaseAuthentication):
    def authenticate(self, request):
        
        # Vérifier si le Referer contient 'public'
        if '/papi/' in request.path:
            # Récupérer l'utilisateur public
            try:
                user = User.objects.get(username='public')
                return (user, None)
            except user.DoesNotExist:
                raise AuthenticationFailed('No public user found')

        # Sinon, essayer l'authentification standard
        else:
            return None


class PublicAuthenticationSave2(BaseAuthentication):
    def authenticate(self, request):
        
        # Vérifier si le Referer contient 'public'
        if request.path.startswith("/papi/"):    
            # Récupérer l'utilisateur public
            try:
                request.user = User.objects.get(username='public')
                auth.login(request=request,user=request.user,backend="django.contrib.auth.backends.ModelBackend",)
            except user.DoesNotExist:
                raise AuthenticationFailed('No public user found')
        else:
            return None


class PublicUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        if request.user.is_authenticated:
            return (request.user, None)
        else:
            from django.contrib.auth.models import User
            public_user = User.objects.get(username='public')
            return (public_user, None)

    def authenticate_header(self, request):
        return 'Basic realm="API"'

    def has_permission(self, user_obj, perm, obj=None):
        """
        Vérifie si l'utilisateur a la permission spécifiée.
        Si l'utilisateur n'est pas authentifié, il vérifie les permissions de l'utilisateur public.
        """
        if not user_obj.is_authenticated:
            # Vérifier les permissions de l'utilisateur public
            public_user = User(username='public')
            return public_user.has_perm(perm)
        else:
            # Vérifier les permissions de l'utilisateur authentifié
            return super().has_perm(user_obj, perm, obj)

    def get_user(self, user_id):
        """
        Récupère l'utilisateur à partir de son ID.
        Si l'utilisateur n'est pas authentifié, il crée un utilisateur public.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            # Créer un utilisateur public
            public_user = User(id=user_id, username='public')
            public_user.set_unusable_password()
            public_user.save()
            return public_user