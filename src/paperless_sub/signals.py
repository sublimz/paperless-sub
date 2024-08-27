from django.db.models.signals import m2m_changed
from datetime import date, timedelta, timezone
import re
import hashlib
import json
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
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from paperless_sub.checks import check_dates_conformity, check_doc_type_conformity

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

    # Vérification et status du champ publier
    id_cf_publier=CustomField.objects.get(name='Publier')
    if CustomFieldInstance.objects.filter(document_id=doc.id,field_id=id_cf_publier.id).exists():
        cf_doc=CustomFieldInstance.objects.get(document_id=doc.id,field_id=id_cf_publier.id)
        print(f"Document mis à jour : {doc.id} {doc.title} {doc.archive_path}")

        # Document mis à jour et publier à vrai        
        if cf_doc.value_bool == True:    
            print(f"traitement de la publication pour {doc.id} {doc.archive_path}")
            try:
                if check_dates_conformity(doc.id) and check_doc_type_conformity(doc.id):
                    mySignTest=SignDocument()
                    doc.checksum = hashlib.md5(doc.archive_path.read_bytes()).hexdigest()

                    # on vérifie la signature
                    if not mySignTest.verif_already_published(doc.archive_path):
                        #on applique le timbre et on signe
                        mySignTest.applyStamp(doc.archive_path, inUrl="http://exemple.com", inChecksumValue=doc.checksum )
                        mySignTest.applySignature(doc.archive_path)

                        doc.checksum = hashlib.md5(doc.archive_path.read_bytes()).hexdigest()
                        print(f"tampon ajouté sur {doc.id} {doc.archive_path}")
                        
                        #Document.objects.filter(id=doc.id).update(modified=now())

                        #Suppression du champ publier
                        cf_doc.delete()
                        
                        #On ajoute le flag en ligne
                        id_cf_online, created=CustomField.objects.get_or_create(name='En ligne',data_type="boolean")
                        cf_online, created=CustomFieldInstance.objects.get_or_create(document_id=doc.id,field_id=id_cf_online.id)
                        cf_online.value_bool=True
                        cf_online.save()

                        #Changement des permissions
                        g_public, created = Group.objects.get_or_create(name='public')
                        g_instructeur, created = Group.objects.get_or_create(name='instructeur')
                        assign_perm("view_document", g_public, doc)
                        assign_perm("view_document", g_instructeur, doc)
                        remove_perm("change_document", g_instructeur, doc)
                        doc.owner = User.objects.get(username='admin')
                        doc.save()

                        #Màj
                        #content_type = ContentType.objects.get_for_model(Document)
                        #log_entry = LogEntry.objects.create(object_id=doc.id,content_type=content_type,action=LogEntry.Action.UPDATE,changes=json.dumps(
                        #    {
                        #        "Publication": [doc.id, "None"],
                        #    },
                        #))
                        #TODOS
                        #Ajouter les shared links

                        #doc.save.apply_async()
                        #update_document_archive_file.apply_async([doc.id], priority=0)
                        #bulk_update_documents.delay(doc.id)
                        

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
