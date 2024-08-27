from datetime import date, timedelta, timezone
import logging

from documents.models import Document
from documents.models import CustomField
from documents.models import CustomFieldInstance

logger = logging.getLogger("paperless.handlers")

#Vérifie la concordance des dates
def check_dates_conformity(doc_id):
    try:
        dp=CustomField.objects.get(name='Date de début de publication')
        ddp, created=CustomFieldInstance.objects.get_or_create(document_id=doc_id,field_id=dp.id)
        fp=CustomField.objects.get(name='Date de fin de publication')
        dfp, created=CustomFieldInstance.objects.get_or_create(document_id=doc_id,field_id=fp.id)
        if ddp.value_date > dfp.value_date:
            logger.warning(
                f"La date de fin publication est postérieure à la date du début",
            )
            return False
        elif ddp.value_date < date.today():
            logger.warning(
                f"La date de début de publication ne peut être antérieur à la date du jour",
            )
            return False
        else:
            return True
    except Exception as e:
        logger.exception(f"Un problème est survenu dans le contrôle des dates de publication {doc_id} :{e}")

#Vérifie qu'on utilise un pdf
def check_doc_type_conformity(doc_id):
    try:
        doc=Document.objects.get(id=doc_id)
        if doc.mime_type != "application/pdf":
            logger.warning(
                f"Document {doc_id} is not a PDF, cannot add watermark",
            )
            return False
        else:
            return True
    except Exception as e:
        logger.exception(f"Un problème est survenu dans le contrôle des dates de publication {doc_id} :{e}")