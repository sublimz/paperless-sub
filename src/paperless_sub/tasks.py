import logging
from django.utils import timezone
from celery import Task
from celery import shared_task

logger = logging.getLogger("paperless.tasks")

from documents.models import Document
from documents.models import CustomField
from documents.models import CustomFieldInstance
from documents.models import Tag
from django.contrib.auth.models import User, Permission, Group
from guardian.shortcuts import assign_perm, remove_perm

#@shared_task
def unpublishing():
    try:
        dp, created=CustomField.objects.get_or_create(name='Date de début de publication',data_type='date')
        fp, created=CustomField.objects.get_or_create(name='Date de fin de publication',data_type='date')
        
        tag_en_ligne=Tag.objects.filter(name='En ligne')
        document_en_ligne=Document.objects.filter(tags__id__in=tag_en_ligne)

        tag_en_ligne, created=Tag.objects.get_or_create(name="En ligne")
        tag_archive, created=Tag.objects.get_or_create(name='Archive')

        for document in document_en_ligne :
            ddp, created=CustomFieldInstance.objects.get_or_create(document_id=document.id,field_id=dp.id)
            dfp, created=CustomFieldInstance.objects.get_or_create(document_id=document.id,field_id=fp.id)
            today=timezone.now().date() 
            print(f"{document.id}---{dfp.value_date}")
            if dfp.value_date is not None:
                if today > dfp.value_date:
                    print(f"Document à dépublier {document.id} ----- début {ddp.value_date} fin {dfp.value_date} ")
                    # on retire en ligne
                    #if CustomFieldInstance.objects.filter(document_id=document.id,field_id=id_cf_online.id).exists():
                    #    cf_online=CustomFieldInstance.objects.filter(document_id=document.id,field_id=id_cf_online.id)
                    #    cf_online.delete()
                    print(f"Ajout du tag en Archive, retrait du tag en ligne ")
                    document.tags.remove(tag_en_ligne)
                    document.tags.add(tag_archive)

                    print(f"Retrait du droit du groupe public ")
                    g_public, created = Group.objects.get_or_create(name='public')
                    g_instructeur, created = Group.objects.get_or_create(name='instructeur')
                    doc=Document.objects.get(id=document.id)
                    remove_perm("view_document", g_public, doc)
                else:
                    print(f"Reste publier {document.id}")
    
    except Exception as e:  # pragma: no cover
        logger.exception(f"Error while try to unpublishing: {e}")

