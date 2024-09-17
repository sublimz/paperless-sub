from datetime import date, timedelta, timezone
import logging
from typing import Union

from documents.models import Document
from documents.models import CustomField
from documents.models import CustomFieldInstance
from documents.models import Correspondent
from documents.loggers import LoggingMixin
from documents.plugins.base import ProgressManager
from rest_framework.exceptions import ValidationError

logger = logging.getLogger("paperless.handlers")

#Vérifie la concordance des dates
def check_dates_conformity(doc_id):
    logger.debug(f"Vérification de la concordance des dates")
    dp=CustomField.objects.get(name='Date de début de publication')
    ddp, created=CustomFieldInstance.objects.get_or_create(document_id=doc_id,field_id=dp.id)
    fp=CustomField.objects.get(name='Date de fin de publication')
    dfp, created=CustomFieldInstance.objects.get_or_create(document_id=doc_id,field_id=fp.id)
    if ddp.value_date > dfp.value_date:
        logger.debug(f"La date de fin publication est antérieure à la date du début",)
        raise ValidationError("La date de fin publication est antérieure à la date du début")
        return False
    elif ddp.value_date < date.today():
        logger.debug(f"La date de début de publication ne peut être antérieure à la date du jour",)
        raise ValidationError("La date de début de publication ne peut être antérieure à la date du jour")
        return False
    else:
        return True

#Vérifie qu'on utilise un pdf
def check_doc_type_conformity(doc_id):
    logger.debug(f"Vérification que le fichier est au format pdf")
    doc=Document.objects.get(id=doc_id)
    if doc.mime_type != "application/pdf":
        logger.debug(f"Document {doc_id} is not a PDF, cannot add watermark",)
        raise ValidationError(f"Le document {doc_id} n'est pas au format pdf, impossible de le signer ")
        return False
    else:
        return True

#Vérifie que correspondent est affecté
def check_correspondent_not_null(doc_id):
    logger.debug(f"Vérification que le champ correspondant n'est pas renseigné")       
    doc=Document.objects.get(id=doc_id)       
    if doc.correspondent is None:
        logger.debug(f"Le correspondant n'est pas renseigné",)
        raise ValidationError("Le correspondant n'est pas renseigné")
        return False
    else:
        return True

#Vérifie que type de document est affecté
def check_documenttype_not_null(doc_id):
    logger.debug(f"Vérification que le type de document est défini")       
    doc=Document.objects.get(id=doc_id)       
    if doc.document_type_id is None:
        logger.debug(f"Le type de document n'est pas renseigné",)
        raise ValidationError("Le type de document n'est pas renseigné")
        return False
    else:
        return True

def test_message(doc_id):
    doc=Document.objects.get(id=doc_id)
    if doc.document_type_id is None:
        raise ValidationError("document_type_id : null.")
        return False