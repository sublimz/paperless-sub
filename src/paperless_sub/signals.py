from django.db.models.signals import m2m_changed
from datetime import date, timedelta
import re
from django.dispatch import receiver
import logging
from django.db.models.signals import pre_save, post_save
from documents.models import Document
from documents.models import CustomField
from documents.models import CustomFieldInstance
from celery import shared_task
from celery.signals import task_postrun


logger = logging.getLogger("paperless.handlers")

@task_postrun.connect
def task_postrun_handler(sender=None, **kwargs):
    print(f"-------------------  Tâche terminée : --{sender.name}- result: {kwargs['retval']}")

    if sender.name == "documents.tasks.consume_file" :
        pattern = r'id (\d+)'
        match = re.search(pattern, kwargs['retval'])
        
        if match:
            doc_id = match.group(1)
            dp=CustomField.objects.get(name='Date de début de publication')
            ddp=CustomFieldInstance.objects.get(document_id=doc_id,field_id=dp.id)
            fp=CustomField.objects.get(name='Date de fin de publication')
            dfp=CustomFieldInstance.objects.get(document_id=doc_id,field_id=fp.id)

            if ddp.value_date is None:
                ddp.value_date=date.today()
                ddp.save()
            if dfp.value_date is None:
                dfp.value_date=date.today() + timedelta(days=60)
                dfp.save()

@receiver(post_save, sender=Document)
def custom_field_instance_updated(sender, instance, created, **kwargs):
    if not created:
        print(f"L'objet {instance} a été mis à jour.")