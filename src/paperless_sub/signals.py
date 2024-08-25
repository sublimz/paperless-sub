from django.db.models.signals import m2m_changed
from datetime import date, timedelta, timezone
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
from django.contrib.auth.models import User, Permission, Group
from guardian.shortcuts import assign_perm, remove_perm
from django.shortcuts import render, redirect
from django.contrib import messages
from documents.signals import document_updated, document_consumption_finished

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
        ddp, created=CustomFieldInstance.objects.get_or_create(document_id=doc_id,field_id=dp.id)
        if ddp.value_date is None:
            ddp.value_date=date.today()
            ddp.save()
        #date de fin de publication dans 60 jrs
        fp=CustomField.objects.get(name='Date de fin de publication')
        dfp, created=CustomFieldInstance.objects.get_or_create(document_id=doc_id,field_id=fp.id)
        if dfp.value_date is None:
            dfp.value_date=date.today() + timedelta(days=60)
            dfp.save()
        #Publier à faux
        p=CustomField.objects.get(name='Publier')
        cp, created=CustomFieldInstance.objects.get_or_create(document_id=doc_id,field_id=p.id)
        if cp.value_bool is None:
            cp.value_bool=False
            cp.save()

@receiver(document_updated)
def mon_recepteur(sender, **kwargs):
    doc = kwargs.get('document')
    # Traitez le document comme nécessaire
    id_cf_publier=CustomField.objects.get(name='Publier')

    if CustomFieldInstance.objects.filter(document_id=doc.id,field_id=id_cf_publier.id).exists():
        print(f"Document mis à jour : {doc.id} {doc.title}")
        cf_doc=CustomFieldInstance.objects.get(document_id=doc.id,field_id=id_cf_publier.id)
        if cf_doc.value_bool == True:
            ## Ajouter contrôle date de publication
            print("traitement de la publication")
            try:
                if doc.mime_type != "application/pdf":
                    logger.warning(
                    f"Document {doc.id} is not a PDF, cannot add watermark",
                    )
                else :
                    mySignTest=SignDocument()
                    doc.checksum = hashlib.md5(doc.source_path.read_bytes()).hexdigest()

                    if not mySignTest.verif_already_published(doc.source_path):
                        mySignTest.applyStamp(doc.source_path, inUrl="http://exemple.com", inChecksumValue=doc.checksum )
                        #mySignTest.applySignature(doc.source_path)

                        doc.checksum = hashlib.md5(doc.source_path.read_bytes()).hexdigest()
                        print(f"tampon ajouté sur {doc.id}")
                        cf_doc.value_bool=False
                        #Document.objects.filter(id=doc.id).update(modified=now())

                        #Suppression du champ publier
                        cf_doc.delete()

                        g_public, created = Group.objects.get_or_create(name='public')
                        g_instructeur, created = Group.objects.get_or_create(name='instructeur')
                        assign_perm("view_document", g_public, doc)
                        assign_perm("view_document", g_instructeur, doc)
                        remove_perm("change_document", g_instructeur, doc)
                        #Màj
                        update_document_archive_file.apply_async([doc.id], priority=0)
                        bulk_update_documents([doc.id])


    
            except Exception as e:
                logger.exception(f"Error on trying add watermark on {doc.id} :{e}")




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
