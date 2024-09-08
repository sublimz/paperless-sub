import logging
from django.apps import AppConfig

class PaperlessSubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'paperless_sub'

    def ready(self):

        from paperless_sub import signals
        logger = logging.getLogger("paperless.tasks")
        from documents.models import Tag

    # Création des étiquettes par défaut
        try:
            tag_en_ligne=Tag.objects.get_or_create(name='En ligne')
            tag_archive=Tag.objects.get_or_create(name='Archive')
            tag_archive=Tag.objects.get_or_create(name='Nouveau')
        except Exception as e:  # pragma: no cover
            logger.exception(f"Error on default Tag creation: {e}")

        from documents.models import CustomField

    # Création des Customs Fieds par défaut
        try:
            dp, created=CustomField.objects.get_or_create(name='Date de début de publication',data_type='date')
            fp, created=CustomField.objects.get_or_create(name='Date de fin de publication',data_type='date')
            id_cf_online, created=CustomField.objects.get_or_create(name='Publier',data_type='boolean')
        except Exception as e:  # pragma: no cover
            logger.exception(f"Error on default Customs Fields creation: {e}")

        from django.contrib.auth.models import User, Permission, Group

    # Création des permissions par défaut
        try:
            # droit instructeur
            view_uisettings_permission = Permission.objects.get(codename='view_uisettings', content_type__app_label='documents')
            view_document_permission = Permission.objects.get(codename='view_document', content_type__app_label='documents')
            add_document_permission = Permission.objects.get(codename='add_document', content_type__app_label='documents')  
            change_document_permission = Permission.objects.get(codename='change_document', content_type__app_label='documents')
            view_tag_permission = Permission.objects.get(codename='view_tag', content_type__app_label='documents')
            view_correspondent_permission = Permission.objects.get(codename='view_correspondent', content_type__app_label='documents')
            view_documenttype_permission = Permission.objects.get(codename='view_documenttype', content_type__app_label='documents')
            view_paperlesstask_permission = Permission.objects.get(codename='view_paperlesstask', content_type__app_label='documents')
            view_logentry_permission = Permission.objects.get(codename='view_logentry', content_type__app_label='admin')
            view_sharelink_permission = Permission.objects.get(codename='view_sharelink', content_type__app_label='documents')
            view_customfield_permission = Permission.objects.get(codename='view_customfield', content_type__app_label='documents')
            # droit administrateur
            delete_document_permission = Permission.objects.get(codename='delete_document', content_type__app_label='documents')

            # Instructeur
            g_model_instructeur, created = Group.objects.get_or_create(name='g_model_instructeur')
            g_model_instructeur.permissions.add(view_uisettings_permission)
            g_model_instructeur.permissions.add(view_document_permission)
            g_model_instructeur.permissions.add(add_document_permission)
            g_model_instructeur.permissions.add(change_document_permission)
            g_model_instructeur.permissions.add(view_tag_permission)
            g_model_instructeur.permissions.add(view_correspondent_permission)
            g_model_instructeur.permissions.add(view_documenttype_permission)
            g_model_instructeur.permissions.add(view_logentry_permission)
            g_model_instructeur.permissions.add(view_sharelink_permission)
            g_model_instructeur.permissions.add(view_customfield_permission)
            # Admin
            g_model_admin, created = Group.objects.get_or_create(name='g_model_admin')
            g_model_admin.permissions.add(view_uisettings_permission)
            g_model_admin.permissions.add(view_document_permission)
            g_model_admin.permissions.add(add_document_permission)
            g_model_admin.permissions.add(change_document_permission)
            g_model_admin.permissions.add(delete_document_permission)
            g_model_admin.permissions.add(view_tag_permission)
            g_model_admin.permissions.add(view_correspondent_permission)
            g_model_admin.permissions.add(view_documenttype_permission)
            g_model_admin.permissions.add(view_logentry_permission)
            g_model_admin.permissions.add(view_sharelink_permission)
            g_model_admin.permissions.add(view_customfield_permission)


        except Exception as e:  # pragma: no cover
            logger.exception(f"Error on default Group creation: {e}")




#        from django.dispatch import receiver
#        from django.db import DatabaseError, OperationalError
#from django.contrib.auth.models import User, Permission, Group
#        from django.contrib.contenttypes.models import ContentType
#        from documents.models import User as DocumentUser
#        from documents.models import CustomField
#        from documents.models import Workflow
#        from documents.models import WorkflowAction
#        from documents.models import WorkflowTrigger
#
#        import logging
#
#        try:
#            if not DocumentUser.objects.filter(username='consumer_anonyme').exists():
#                # Créer les utilisateurs système
#                add_document_permission=Permission.objects.get(codename='add_document', content_type__app_label='documents')
#                system_user_1 = DocumentUser.objects.create_user(
#                    username='consumer_anonyme',
#                    first_name='consumer_anonyme',
#                    last_name='consumer_anonyme',
#                    password='consumer_anonyme_sub',
#                    is_active=True
#                )
#                system_user_1.user_permissions.add(add_document_permission)
#
#            if not DocumentUser.objects.filter(username='public').exists():
#                view_uisettings_permission = Permission.objects.get(codename='view_uisettings', content_type__app_label='documents')
#                view_document_permission = Permission.objects.get(codename='view_document', content_type__app_label='documents')  
#                system_user_2 = DocumentUser.objects.create_user(
#                    username='public',
#                    first_name='public',
#                    last_name='public',
#                    password='public',
#                    is_active=True
#                )
#                system_user_2.user_permissions.add(view_uisettings_permission, view_document_permission)
#
#            if not Group.objects.filter(name='instructeur').exists():
#                add_document_permission=Permission.objects.get(codename='add_document', content_type__app_label='documents')
#                view_uisettings_permission = Permission.objects.get(codename='view_uisettings', content_type__app_label='documents')
#                view_document_permission = Permission.objects.get(codename='view_document', content_type__app_label='documents')  
#                instructeur_group, created = Group.objects.get_or_create(name='instructeur')
#                instructeur_group.permissions.add(add_document_permission,view_uisettings_permission, view_document_permission)
#
#            if not Group.objects.filter(name='public').exists():
#                view_uisettings_permission = Permission.objects.get(codename='view_uisettings', content_type__app_label='documents')
#                view_document_permission = Permission.objects.get(codename='view_document', content_type__app_label='documents')  
#                public_group, created = Group.objects.get_or_create(name='public')
#                public_group.permissions.add(view_uisettings_permission, view_document_permission)    
#
#            if not CustomField.objects.filter(name='Date de début de publication').exists():
#                CustomField.objects.get_or_create(name='Date de début de publication',data_type='date')
#
#            if not CustomField.objects.filter(name='Date de fin de publication').exists():
#                CustomField.objects.get_or_create(name='Date de fin de publication',data_type='date')
#
#            if not CustomField.objects.filter(name='A publier').exists():
#                CustomField.objects.get_or_create(name='A publier',data_type='boolean')            
#
#            
#            if not Workflow.objects.filter(name='[SUB] ajoute champ perso date debut pub et date fin pub').exists():
#                Workflow.objects.get_or_create(name='[SUB] ajoute champ perso date debut pub et date fin pub',order=1,enabled=1)
#                WorkflowAction.objects.get_or_create(workflow_id=1,workflowaction_id=1)
#                WorkflowTrigger.objects.get_or_create(workflow_id=1,workflowtrigger_id=1)
#
#
#        except:
#            pass


        AppConfig.ready(self)