from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import Document


class TestTrashAPI(APITestCase):
    def setUp(self):
        super().setUp()

        self.user = User.objects.create_superuser(username="temp_admin")
        self.client.force_authenticate(user=self.user)
        cache.clear()

    def test_api_trash(self):
        """
        GIVEN:
            - Existing document
        WHEN:
            - API request to delete document
            - API request to restore document
            - API request to empty trash
        THEN:
            - Document is moved to trash
            - Document is restored from trash
            - Trash is emptied
        """

        document = Document.objects.create(
            title="Title",
            content="content",
            checksum="checksum",
            mime_type="application/pdf",
        )

        self.client.force_login(user=self.user)
        self.client.delete(f"/api/documents/{document.pk}/")
        self.assertEqual(Document.objects.count(), 0)
        self.assertEqual(Document.global_objects.count(), 1)
        self.assertEqual(Document.deleted_objects.count(), 1)

        resp = self.client.get("/api/trash/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

        resp = self.client.post(
            "/api/trash/",
            {"action": "restore", "documents": [document.pk]},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Document.objects.count(), 1)

        resp = self.client.get("/api/trash/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 0)

        self.client.delete(f"/api/documents/{document.pk}/")
        resp = self.client.post(
            "/api/trash/",
            {"action": "empty", "documents": [document.pk]},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Document.global_objects.count(), 0)

    def test_trash_api_empty_all(self):
        """
        GIVEN:
            - Existing documents in trash
        WHEN:
            - API request to empty trash
        THEN:
            - Trash is emptied
        """

        document = Document.objects.create(
            title="Title",
            content="content",
            checksum="checksum",
            mime_type="application/pdf",
        )
        document.delete()
        document2 = Document.objects.create(
            title="Title2",
            content="content2",
            checksum="checksum2",
            mime_type="application/pdf",
        )
        document2.delete()

        self.client.force_login(user=self.user)
        resp = self.client.post(
            "/api/trash/",
            {"action": "empty", "documents": []},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Document.global_objects.count(), 0)

    def test_api_trash_insufficient_permissions(self):
        """
        GIVEN:
            - Existing document with owner = user2 in trash
        WHEN:
            - user 1 makes API request to empty document from trash
        THEN:
            - 403 Forbidden
        """

        user1 = User.objects.create_user(username="user1")
        self.client.force_authenticate(user=user1)
        self.client.force_login(user=user1)
        user2 = User.objects.create_user(username="user2")
        document = Document.objects.create(
            title="Title",
            content="content",
            checksum="checksum",
            mime_type="application/pdf",
            owner=user2,
        )
        document.delete()

        resp = self.client.post(
            "/api/trash/",
            {"action": "empty", "documents": [document.pk]},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Document.global_objects.count(), 1)

    def test_api_trash_invalid_params(self):
        """
        GIVEN:
            - Existing documents
        WHEN:
            - API request to trash with invalid params
        THEN:
            - 400 Bad Request
        """

        document = Document.objects.create(
            title="Title",
            content="content",
            checksum="checksum",
            mime_type="application/pdf",
        )

        self.client.force_login(user=self.user)

        # document isn't in trash
        resp = self.client.post(
            "/api/trash/",
            {"action": "restore", "documents": [document.pk]},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("have not yet been deleted", resp.data["documents"][0])
