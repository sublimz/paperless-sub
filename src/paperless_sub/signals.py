from django.db.models.signals import m2m_changed
from datetime import date, timedelta
import re
import hashlib
from django.dispatch import receiver
import logging
from django.db.models.signals import pre_save, post_save
from documents.models import Document
from documents.models import CustomField
from documents.models import CustomFieldInstance
from documents.tasks import consume_file,bulk_update_documents,update_document_archive_file
from celery import shared_task
from celery.signals import task_postrun
from auditlog.models import LogEntry
from .sign import SignDocument

logger = logging.getLogger("paperless.handlers")

#Après ajout du doc initialisation des valeurs
@task_postrun.connect
def task_postrun_handler(sender=consume_file, **kwargs):
    print(f"-------------------  Tâche terminée : --{sender.name}- result:--{kwargs['retval']}--")
    match = re.search(r"(?<=Success\. New document id )\d+(?= created)", str(kwargs['retval']))
        
    if match:
        doc_id = int(match.group())
        print(f"{doc_id} de type {type(doc_id)}")
        #date de début de publication à la date du jour
        dp=CustomField.objects.get(name='Date de début de publication')
        ddp=CustomFieldInstance.objects.get(document_id=doc_id,field_id=dp.id)
        if ddp.value_date is None:
            ddp.value_date=date.today()
            ddp.save()
        #date de fin de publication dans 60 jrs
        fp=CustomField.objects.get(name='Date de fin de publication')
        dfp=CustomFieldInstance.objects.get(document_id=doc_id,field_id=fp.id)
        if dfp.value_date is None:
            dfp.value_date=date.today() + timedelta(days=60)
            dfp.save()
        #Publier à faux
        p=CustomField.objects.get(name='Publier')
        cp=CustomFieldInstance.objects.get(document_id=doc_id,field_id=p.id)
        if cp.value_bool is None:
            cp.value_bool=False
            cp.save()


            
#Evaluation de si on publie
@receiver(post_save, sender=CustomFieldInstance)
def custom_fields_post_save(sender, instance, created, **kwargs):
    if not created:
        doc=Document.objects.get(id=instance.document_id)

        id_cf_publier=CustomField.objects.get(name='Publier')
        dp=CustomField.objects.get(name='Date de début de publication')
        ddp=CustomFieldInstance.objects.get(document_id=doc.id,field_id=dp.id)
        fp=CustomField.objects.get(name='Date de fin de publication')
        dfp=CustomFieldInstance.objects.get(document_id=doc.id,field_id=fp.id)
        
        #si la màj concerne le champ Publier et que sa valeur est True 
        # et que la date de début et de fin sont non null
        if ( instance.field_id==id_cf_publier.id and instance.value_bool==True 
             and ddp.value_date is not None and dfp.value_date is not None ):
            
            # debug : print(f"{id_cf_publier.id}L'objet CustomField {instance.id} et le champ {instance.field_id} à pris la valeur {instance.value_bool} pour le {instance.document_id} par {sender}")
            try:
                if doc.mime_type != "application/pdf":
                   logger.warning(
                   f"Document {doc.id} is not a PDF, cannot add watermark",
                   )
                print(f"on publie le {doc.id} qui se situe {doc.source_path}")
                #on tamponne le doc
                mySignTest=SignDocument()
                mySignTest.applyStamp(doc.source_path, inUrl="http://exemple.com", inChecksumValue="1d3sf1sd53f1s53" )
                doc.checksum = hashlib.md5(doc.source_path.read_bytes()).hexdigest()
                doc.save()
                print(f"tampon ajouté sur {doc.id}")
                update_document_archive_file(document_id=doc.id)
                bulk_update_documents([doc.id])

            except Exception as e:
                logger.exception(f"Error on trying add watermark on {doc.id}: {e}")





                #CustomFieldInstance.objects.get(document_id=1,field_id=3).delete()

#note = Note.objects.get(id=int(request.GET.get("id")))
#if settings.AUDIT_LOG_ENABLED:
#    LogEntry.objects.log_create(
#        instance=doc,
#        changes=json.dumps(
#            {
#                "Note Deleted": [note.id, "None"],
#            },
#        ),
#        action=LogEntry.Action.UPDATE,
#    )

#    doc=instance
#    if created:
#        print(f"L'objet {doc.id} a été créé par {sender}")
#
#
#    if not created:
#        print(f"L'objet {doc.id} a été mis à jour par {sender}")
#
#	    ##Détection de à publier
#        qs=CustomFieldInstance.objects.get(document_id=doc.id, field_id=CustomField.objects.get(name='Publier'))
#        print(f"qs à la valeur {qs.value_bool}")
#        ##Retourne faux si la checkbox est coché
#        print(qs.value_bool)
#
#        if qs.value_bool == False :
#            print("on veut publier")
#            print(qs.id)
#            entries = LogEntry.objects.filter(object_pk=qs.id,object_repr="Publier : False").order_by('-timestamp').values_list('id', flat=True)
#            eid_list = list(entries)
#            print(eid_list)
#            if eid_list is None:
#                print("----- jamais publier, on va publier")
#
