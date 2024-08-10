from django.apps import AppConfig

class PaperlessSubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'paperless_sub'

    def ready(self):
        from django.dispatch import receiver
        from django.contrib.auth.models import User, Permission
        from django.contrib.contenttypes.models import ContentType
        from documents.models import User as DocumentUser


        if not DocumentUser.objects.filter(username='consumer_anonyme').exists():
            # Créer les utilisateurs système
            system_user_1 = DocumentUser.objects.create_user(
                username='consumer_anonyme',
                first_name='consumer_anonyme',
                last_name='consumer_anonyme',
                password='consumer_anonyme_sub',
                is_active=True
            )

        if not DocumentUser.objects.filter(username='public').exists():
            system_user_2 = DocumentUser.objects.create_user(
                username='public',
                first_name='public',
                last_name='public',
                password='public',
                is_active=True
            )
        AppConfig.ready(self)