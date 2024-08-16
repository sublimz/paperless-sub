from django.apps import AppConfig

class PaperlessSubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'paperless_sub'

    def ready(self):

        from paperless_sub import signals

        from django.dispatch import receiver
        from django.db import DatabaseError, OperationalError
        from django.contrib.auth.models import User, Permission
        from django.contrib.contenttypes.models import ContentType
        from documents.models import User as DocumentUser
        from documents.models import CustomField
        from documents.models import Workflow
        from documents.models import WorkflowAction
        from documents.models import WorkflowTrigger

        import logging

        try:
            if not DocumentUser.objects.filter(username='consumer_anonyme').exists():
                # Créer les utilisateurs système
                add_document_permission=Permission.objects.get(codename='add_document', content_type__app_label='documents')
                system_user_1 = DocumentUser.objects.create_user(
                    username='consumer_anonyme',
                    first_name='consumer_anonyme',
                    last_name='consumer_anonyme',
                    password='consumer_anonyme_sub',
                    is_active=True
                )
                system_user_1.user_permissions.add(add_document_permission)

            if not DocumentUser.objects.filter(username='public').exists():
                view_uisettings_permission = Permission.objects.get(codename='view_uisettings', content_type__app_label='documents')
                view_document_permission = Permission.objects.get(codename='view_document', content_type__app_label='documents')  
                system_user_2 = DocumentUser.objects.create_user(
                    username='public',
                    first_name='public',
                    last_name='public',
                    password='public',
                    is_active=True
                )
                system_user_2.user_permissions.add(view_uisettings_permission, view_document_permission)

            if not CustomField.objects.filter(name='Date de début de publication').exists():
                CustomField.objects.create(name='Date de début de publication',data_type='date')

            if not CustomField.objects.filter(name='Date de fin de publication').exists():
                CustomField.objects.create(name='Date de fin de publication',data_type='date')    

            """
            if not Workflow.objects.filter(name='[SUB] ajoute champ perso date debut pub et date fin pub').exists()
                Workflow.objects.create(name='[SUB] ajoute champ perso date debut pub et date fin pub',order=1,enabled=1)
                WorkflowAction.objects.create(workflow_id=1,workflowaction_id=1)
                WorkflowTrigger.objects.create(workflow_id=1,workflowtrigger_id=1)
            """

        except:
            pass


        AppConfig.ready(self)