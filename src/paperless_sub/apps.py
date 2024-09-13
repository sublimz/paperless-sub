import logging
from django.apps import AppConfig
from django.db import connection
from django.db.utils import OperationalError

class PaperlessSubConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'paperless_sub'

    def ready(self):
        # Vérifiez si les migrations ont été appliquées
        if self.check_migrations_applied():
            # Effectuez vos vérifications ici
            self.perform_checks()

    def check_migrations_applied(self):
        # Vérifiez si la base de données est synchronisée avec les migrations
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM django_migrations")
                migration_count = cursor.fetchone()[0]
                return migration_count > 0
        except OperationalError:
            # La table django_migrations n'existe pas, donc pas de migrations appliquées
            return False

    def perform_checks(self):
        # Ajoutez votre logique de vérification ici
        print("migrations was applied, adding default settings")

        from paperless_sub import signals
        logger = logging.getLogger("paperless.tasks")

        # Création des étiquettes par défaut
        from documents.models import Tag
    
        try:
            tag_en_ligne=Tag.objects.get_or_create(name='En ligne')
            tag_archive=Tag.objects.get_or_create(name='Archive')
            tag_archive=Tag.objects.get_or_create(name='Nouveau')
        except Exception as e:  # pragma: no cover
            logger.exception(f"Error on default Tag creation: {e}")

        # Création des Data type par défaut
        from documents.models import DocumentType

        try:
            arr, created=DocumentType.objects.get_or_create(name='Arrêtés')
            dec, created=DocumentType.objects.get_or_create(name='Décisions')
            deli, created=DocumentType.objects.get_or_create(name='Délibérations')
            autre, created=DocumentType.objects.get_or_create(name='Autre')
        except Exception as e:  # pragma: no cover
            logger.exception(f"Error on default Document type creation: {e}")

        
        # Création des Customs Fieds par défaut
        from documents.models import CustomField
        try:
            dp, created=CustomField.objects.get_or_create(name='Date de début de publication',data_type='date')
            fp, created=CustomField.objects.get_or_create(name='Date de fin de publication',data_type='date')
            id_cf_online, created=CustomField.objects.get_or_create(name='Publier',data_type='boolean')
        except Exception as e:  # pragma: no cover
            logger.exception(f"Error on default Customs Fields creation: {e}")

        from django.contrib.auth.models import User, Permission, Group

    # Création des permissions par défaut
        from django.contrib.auth.models import User, Permission, Group

        try:
            # droit instructeur et/ou public
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
            g_model_instructeur.permissions.add(view_paperlesstask_permission)
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
            g_model_admin.permissions.add(view_paperlesstask_permission)
            # Public
            g_model_public, created = Group.objects.get_or_create(name='g_model_public')
            g_model_public.permissions.add(view_uisettings_permission)
            g_model_public.permissions.add(view_document_permission)

        except Exception as e:  # pragma: no cover
            logger.exception(f"Error on default Group creation: {e}")


        from django.contrib.auth.models import User

        try:
            public_user, created = User.objects.get_or_create(username='public', is_active=True)
            if created :
                public_user.set_password('public')
                public_user.save()
            consumer_anonyme_user, created = User.objects.get_or_create(username='consumer_anonyme', is_active=True)
            if created :
                consumer_anonyme_user.set_password('consumer_anonyme')
                consumer_anonyme_user.save()
        except Exception as e:  # pragma: no cover
            logger.exception(f"Error on default Users creation: {e}")



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
#                    i_active=Trues
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



        AppConfig.ready(self)