import os
import logging
import hashlib
from django.conf import settings
from celery import Task
from celery import shared_task
from celery import chain
from celery import chord
from celery import group

from documents.models import Document
from documents.models import DocumentType
from documents.models import StoragePath
from documents.models import Tag
from documents.tasks import bulk_update_documents
from documents.tasks import consume_file
from documents.tasks import update_document_archive_file


logger = logging.getLogger("paperless.tasks")


@shared_task
def watermark():

    public_tags = Tag.objects.filter(name='public')
    qs = Document.objects.filter(tags__in=public_tags)
    affected_docs = []
 
    
    from pikepdf import Pdf, Rectangle, Page
    import pikepdf

    watermark_tasks = []
 
    for doc in qs:

        logger.info(
            f"Add watermark for document {doc.id}",
        )
        
        if doc.mime_type != "application/pdf":
            logger.warning(
                f"Document {doc.id} is not a PDF, cannot add watermark",
            )
            continue
        try:

            #cartouche
            watermark_file=Pdf.open("../static/certs/watermark.pdf")
            thumbnail = Page(watermark_file.pages[0])

            with pikepdf.open(doc.source_path, allow_overwriting_input=True) as pdf:
                for i in range(len(pdf.pages)):
                    destination_page=Page(pdf.pages[i])
                    destination_page.add_overlay(thumbnail, Rectangle(0, 0, 300, 300))

                #enregistrer le fichier
                #pdf.save("../static/page1_with_page2_thumbnail.pdf")
                
            
                pdf.save()
                pdf.close()
                doc.checksum = hashlib.md5(doc.source_path.read_bytes()).hexdigest()
                doc.save()
                

                watermark_tasks.append(
                    update_document_archive_file.s(
                        document_id=doc.id,
                    ),
                )

                logger.info(f"Watermark added from document {doc.id}")
                affected_docs.append(doc.id)              


        except Exception as e:
            logger.exception(f"Error on trying add watermark on {doc.id}: {e}")

    if len(affected_docs) > 0:
        bulk_update_task = bulk_update_documents.si(document_ids=affected_docs)
        chord(header=watermark_tasks, body=bulk_update_task).delay()

