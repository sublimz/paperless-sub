from django.db.models.signals import m2m_changed
from datetime import date, timedelta, timezone
from unidecode import unidecode
import re
import hashlib
import json
from django.dispatch import receiver
import logging
from django.db.models.signals import pre_save, post_save
from documents.models import Document
from documents.models import Tag
from documents.models import CustomField
from documents.models import CustomFieldInstance
from documents.models import Correspondent
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
from paperless_sub.checks import check_dates_conformity, check_doc_type_conformity, check_correspondent_not_null, check_documenttype_not_null
from documents.permissions import get_objects_for_user_owner_aware
from documents.permissions import set_permissions_for_object
from rest_framework.exceptions import ValidationError
from paperless_sub.checks import test_message


logger = logging.getLogger("paperless.handlers")

"""
Ajout d'un document : initialisation des valeurs pour la publication à venir
"""
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


"""
Changement des étiquettes en masse
"""
@receiver(post_save, sender=Document.tags.through)
def bulk_tag_change(sender, instance, created, **kwargs):
    print(f"Changement des étiquettes en masse a été créé : {instance.id} {instance.name} {instance.name.lower()}")


"""
Changement d'une étiquette : modification à écrire ?, en fait en bulk edit, ce signal n'est pas envoyé
"""
@receiver(m2m_changed, sender=Document.tags.through)
def handle_tags_change(sender, instance, action, **kwargs):
    if action == "pre_add":
        # Récupérer les IDs des objets Tag qui vont être ajoutés
        new_tag_ids = kwargs.get('pk_set', set())
        
        # Récupérer les noms des tags qui vont être ajoutés
        new_tags = Tag.objects.filter(id__in=new_tag_ids).values_list('name', flat=True)
        
        # Récupérer les noms des tags déjà associés
        current_tag_ids = instance.tags.values_list('id', flat=True)
        current_tags = Tag.objects.filter(id__in=current_tag_ids).values_list('name', flat=True)
        
        print("Tags à ajouter :", list(new_tags))
        print("Tags déjà associés :", list(current_tags))

        #if not current_tags:
        #    print("instance.notag()")

        # Vérifier les conditions
        # Si à instruire vers en ligne
        if not current_tags and "En ligne" in new_tags:
            print("ON PUBLIE")  # Appeler la méthode stamp()
                



## Exemple d'utilisation
#object_id = 1  # Remplacez par l'ID de l'objet que vous souhaitez vérifier
#search_value = "Add Tags: En ligne"
#
#if log_entry_exists(YourModel, object_id, search_value):
#    print("L'entrée de log existe.")
#else:
#    print("Aucune entrée de log trouvée.")
#
#
#
#def log_entry_exists(model, object_id, search_value):
#    """
#    Vérifie si une entrée de log existe pour un objet donné et une valeur spécifiée.
#
#    :param model: Le modèle de l'objet
#    :param object_id: L'ID de l'objet
#    :param search_value: La valeur à rechercher dans le message de changement
#    :return: True si l'entrée de log existe, sinon False
#    """
#    # Obtenez le ContentType de votre modèle
#    content_type = ContentType.objects.get_for_model(model)
#
#    # Rechercher les LogEntry pour cet objet
#    log_entries = LogEntry.objects.filter(
#        content_type=content_type,
#        object_id=object_id,
#        action_flag=ADDITION,
#        change_message__icontains=search_value
#    )
#
#    # Retourne True si des entrées sont trouvées, sinon False
#    return log_entries.exists()
#

"""
Mise à jour d'un document : vérification de si il est à publier
"""
@receiver(document_updated)
def mon_recepteur(sender, **kwargs):
    doc = kwargs.get('document')

    # Vérification et statut du champ publier
    id_cf_publier=CustomField.objects.get(name='Publier')

    # On récupère la liste des tags
    current_tag_ids = doc.tags.values_list('id', flat=True)
    current_tags = Tag.objects.filter(id__in=current_tag_ids).values_list('name', flat=True)

    if CustomFieldInstance.objects.filter(document_id=doc.id,field_id=id_cf_publier.id).exists():
        cf_doc=CustomFieldInstance.objects.get(document_id=doc.id,field_id=id_cf_publier.id)
        print(f"Document mis à jour : {doc.id} {doc.title} {doc.archive_path}")

        # Document mis à jour et publier à vrai        
        if cf_doc.value_bool == True:
            #raise ValidationError("Condition non remplie.")

            print(f"traitement de la publication pour {doc.id} {doc.archive_path}")
            try:

                if (check_dates_conformity(doc.id) 
                    and check_doc_type_conformity(doc.id) 
                    and check_correspondent_not_null(doc.id) 
                    and check_documenttype_not_null(doc.id) 
                    and "Archive" not in current_tags 
                    and "En ligne" not in current_tags ):

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
                        tag_en_ligne = Tag.objects.get(name="En ligne")
                        #tag_a_instruire = Tag.objects.get(name="A instruire")
                        #tag_archive = Tag.objects.get(name="Archive")
                        doc.tags.add(tag_en_ligne)

                        #Ajout du custom flag en ligne
                        #id_cf_online, created=CustomField.objects.get_or_create(name='En ligne',data_type="boolean")
                        #cf_online, created=CustomFieldInstance.objects.get_or_create(document_id=doc.id,field_id=id_cf_online.id)
                        #cf_online.value_bool=True
                        #cf_online.save()
     
                        doc.owner = User.objects.get(username='admin')

                        #Reconstituion du groupe gi du correspondant et assignation du groupe au correspondant
                        correspondant= Correspondent.objects.get(id=doc.correspondent_id)
                        correspondant_normalized=unidecode(correspondant.name.lower().replace(" ", "_"))
                        gi_name=f'{doc.correspondent_id}_gi_{correspondant_normalized}'
                        group_gi_name, created=Group.objects.get_or_create(name=gi_name)
                        assign_perm('view_correspondent',group_gi_name,correspondant)


                        #print(f"Permission 'view_correspondent' assignée au groupe --{gi_name}-- sur l'objet {correspondant}.")
                        #Changement des permissions
                        #### A vérifier, changer les droits pour que le correspondant ne soit qu'en visu après publication
                        g_public, created = Group.objects.get_or_create(name='g_public')
                        g_instructeur, created = Group.objects.get_or_create(name='g_model_instructeur')
                        assign_perm('view_document', g_public, doc)
                        assign_perm('view_document', g_instructeur, doc)
                        assign_perm('view_document', group_gi_name, doc)

                        remove_perm('change_document', g_instructeur, doc)
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
                        
            except ValidationError as e:
                # Vous pouvez gérer l'erreur ici ou la laisser remonter
                raise e  # Propagation de l'exception

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


""" Création des groupes de droits lors de la création du correspondant """
@receiver(post_save, sender=Correspondent)
def correspondant_created(sender, instance, created, **kwargs):
    if created:
        print(f"Un nouveau correspondant a été créé : {instance.id} {instance.name} {instance.name.lower()}")

        g_model_instructeur = Group.objects.get(name='g_model_instructeur')
        g_model_admin= Group.objects.get(name='g_model_admin')
        ## on supprimes les espaces et on ajoute gi_ en préfixe
        name_gi_instance = f'{instance.id}'+"_gi_"+instance.name.lower().replace(" ", "_")
        name_ga_instance = f'{instance.id}'+"_ga_"+instance.name.lower().replace(" ", "_")
        
        nouveau_groupe_i, created = Group.objects.get_or_create(name=name_gi_instance)
        nouveau_groupe_a, created = Group.objects.get_or_create(name=name_ga_instance)
        ## Copier les permissions du groupe modèle vers le nouveau
        nouveau_groupe_i.permissions.set(g_model_instructeur.permissions.all())
        nouveau_groupe_a.permissions.set(g_model_admin.permissions.all())

## l'affectation ne fonctionne pas ici !!!
## l'affectation est effecutée au niveau de la mise à jour du document, à revoir
        assign_perm('view_correspondent',nouveau_groupe_i,instance)
        assign_perm('change_correspondent',nouveau_groupe_a,instance)

##        #>>> objet = Correspondent.objects.get(id=52)
##        #>>> groupe = Group.objects.get(id=90)
##        #>>> assign_perm('change_correspondent',groupe,objet)
##        #<GroupObjectPermission: A6 | gi_a6 | change_correspondent>