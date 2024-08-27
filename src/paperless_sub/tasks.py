import logging
from django.utils import timezone
from celery import Task
from celery import shared_task

logger = logging.getLogger("paperless.tasks")

from documents.models import Document
from documents.models import CustomField
from documents.models import CustomFieldInstance
from django.contrib.auth.models import User, Permission, Group
from guardian.shortcuts import assign_perm, remove_perm

@shared_task
def unpublishing():
    try:
        dp, created=CustomField.objects.get_or_create(name='Date de début de publication',data_type='date')
        fp, created=CustomField.objects.get_or_create(name='Date de fin de publication',data_type='date')
        id_cf_online, created=CustomField.objects.get_or_create(name='En ligne',data_type='boolean')
        q=CustomField.objects.filter(name='En ligne')
        document_en_ligne=CustomFieldInstance.objects.filter(field_id__in=q, value_bool=True)

        #document_en_ligne=CustomFieldInstance.objects.filter(field_id__in=id_cf_online, value_bool=True)
        #CustomFieldInstance.objects.filter(document_id__in=affected_docs,field_id__in=remove_custom_fields,)
        #document_en_ligne=CustomFieldInstance.objects.filter(field_id__in=q, value_bool=True)
        #document_en_ligne
        #<QuerySet [<CustomFieldInstance: En ligne : True>, <CustomFieldInstance: En ligne : True>, <CustomFieldInstance: En ligne : True>, <CustomFieldInstance: En ligne : True>]>

        for document in document_en_ligne :

            ddp, created=CustomFieldInstance.objects.get_or_create(document_id=document.document_id,field_id=dp.id)
            dfp, created=CustomFieldInstance.objects.get_or_create(document_id=document.document_id,field_id=fp.id)
            today=timezone.now().date() 
            print(f"{document.document_id}---{dfp.value_date}")
            if dfp.value_date is not None:
                if today > dfp.value_date:
                    print(f"Document à dépublier {document.document_id} ----- début {ddp.value_date} fin {dfp.value_date} ")
                    # on retire en ligne
                    if CustomFieldInstance.objects.filter(document_id=document.document_id,field_id=id_cf_online.id).exists():
                        cf_online=CustomFieldInstance.objects.filter(document_id=document.document_id,field_id=id_cf_online.id)
                        cf_online.delete()
                    # on ajoute archive
                    id_cf_archive, created=CustomField.objects.get_or_create(name='Archive',data_type="boolean")
                    cf_archive, created=CustomFieldInstance.objects.get_or_create(document_id=document.document_id,field_id=id_cf_archive.id)
                    cf_archive.value_bool=True
                    cf_archive.save()
                    g_public, created = Group.objects.get_or_create(name='public')
                    g_instructeur, created = Group.objects.get_or_create(name='instructeur')
                    doc=Document.objects.get(id=document.document_id)
                    remove_perm("view_document", g_public, doc)
                else:
                    print(f"Reste publier {document.document_id}")
    
    except Exception as e:  # pragma: no cover
        logger.exception(f"Error while try to unpublishing: {e}")

