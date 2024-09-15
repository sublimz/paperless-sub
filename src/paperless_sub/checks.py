from datetime import date, timedelta, timezone
import logging
from typing import Union

from documents.models import Document
from documents.models import CustomField
from documents.models import CustomFieldInstance
from documents.models import Correspondent
from documents.loggers import LoggingMixin
from documents.plugins.base import ProgressManager

class CheckPublish(LoggingMixin):
    logging_name = "paperless.consumer"
    logger = logging.getLogger("paperless.handlers")


    def __init__(self, status_mgr):
        super().__init__()  # Appel au constructeur de LoggingMixin
        self.status_mgr = status_mgr  # Gestionnaire de statut
    
    def _fail(
        self,
        message: str,
        log_message: str,
        exc_info=None,
    ):
        self.logger.error(message=message, log_message=log_message, exc_info=exc_info)

    def publish(self):
        try:
            # Logique de publication ici
            # Simulons un échec pour démonstration
            raise ValueError("Une erreur s'est produite lors de la publication.")
        except Exception as e:
            self._fail("Échec de la publication", message=str(e), log_message=str(e),exc_info=True)


logger = logging.getLogger("paperless.handlers")




#Vérifie la concordance des dates
def check_dates_conformity(doc_id):
    logger.warning(f"Vérification de la concordance des dates")
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
    logger.warning(f"Vérification que le fichier est au format pdf")
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

#Vérifie que correspondent est affecté
def check_correspondent_not_null(doc_id):
    logger.warning(f"Vérification que le champ correspondant est défini")       
    try:
        doc=Document.objects.get(id=doc_id)       
        if doc.correspondent is None:
            logger.warning(
                f"Le correspondent n'est pas défini",
            )
            return False
        else:
            return True
    except Exception as e:
        logger.exception(f"Un problème est survenu dans le contrôle de présence du correspondent {doc_id} :{e}")

#Vérifie que type de document est affecté
def check_documenttype_not_null(doc_id):
    logger.warning(f"Vérification que le type de document est défini")       
    try:
        doc=Document.objects.get(id=doc_id)       
        if doc.document_type_id is None:
            logger.warning(
                f"Le type de document n'est pas défini",
            )
            return False
        else:
            return True
    except Exception as e:
        logger.exception(f"Un problème est survenu dans le contrôle de présence du correspondent {doc_id} :{e}")

def test(doc_id):
    status_mgr = {}  # Simuler un gestionnaire de statut
    publisher = CheckPublish(status_mgr)  # Créer une instance de CheckPublish    
    publisher.publish()  # Appeler la méthode de publication