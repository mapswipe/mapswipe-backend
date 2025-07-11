import typing
from unittest import mock

from django.urls import reverse
from firebase_admin import auth

from apps.user.factories import UserFactory
from main.tests import TestCase

FIREBASE_AUTH_URL = reverse("firebase_auth")


class TestFirebaseAuth(TestCase):
    @staticmethod
    def _get_firebase_token_payload(uid: str, email: str, email_verified: bool):
        return {
            "uid": uid,
            "email": email,
            "email_verified": email_verified,
        }

    @typing.override
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_inactive = UserFactory.create(email="fb_inactive@test.com")

    @mock.patch("apps.common.serializers.auth.verify_id_token")
    def test_valid_firebase_login(self, mock_verify_id_token: mock.MagicMock):
        user = UserFactory.create(
            email="fb_active@test.com",
            fb_uid="firebase-user-uid-01",
        )

        firebase_token_payload = self._get_firebase_token_payload(
            uid=user.fb_uid,
            email=user.email,
            email_verified=True,
        )
        mock_verify_id_token.return_value = firebase_token_payload

        response = self.client.post(FIREBASE_AUTH_URL, {"token": "valid-token"}, format="json")

        assert user.fb_uid == firebase_token_payload["uid"]
        user.refresh_from_db()
        assert response.status_code == 200
        assert user.fb_uid == firebase_token_payload["uid"]

    @mock.patch("apps.common.serializers.auth.verify_id_token")
    def test_invalid_token(self, mock_verify_id_token: mock.MagicMock):
        for fb_exception in [
            auth.InvalidIdTokenError("Error"),
            auth.RevokedIdTokenError("Error"),
            auth.UserDisabledError("Error"),
            Exception("Not sure what happened"),
        ]:
            assert_msg = f"Firebase <{fb_exception}> should have this assert"
            mock_verify_id_token.side_effect = fb_exception

            response = self.client.post(FIREBASE_AUTH_URL, {"token": "invalid"}, format="json")
            assert response.status_code == 400, assert_msg
            assert "token" in response.json(), assert_msg

    @mock.patch("apps.common.serializers.auth.verify_id_token")
    def test_user_not_found(self, mock_verify_id_token: mock.MagicMock):
        firebase_token_payload = self._get_firebase_token_payload(
            uid="random-user-01",
            email="random-user@test.com",
            email_verified=True,
        )
        mock_verify_id_token.return_value = firebase_token_payload

        response = self.client.post(FIREBASE_AUTH_URL, {"token": "valid"}, format="json")
        assert response.status_code == 400
        assert response.json() == {
            "non_field_errors": ["user not invited as manager yet. please contact admin"],
        }

    @mock.patch("apps.common.serializers.auth.verify_id_token")
    def test_user_email_not_verified(self, mock_verify_id_token: mock.MagicMock):
        firebase_token_payload = self._get_firebase_token_payload(
            uid="random-user-01",
            email="random-user@test.com",
            email_verified=False,
        )
        mock_verify_id_token.return_value = firebase_token_payload

        response = self.client.post(FIREBASE_AUTH_URL, {"token": "valid"}, format="json")
        assert response.status_code == 400
        assert response.json() == {
            "token": ["user email is not verified"],
        }

    @mock.patch("apps.common.serializers.auth.verify_id_token")
    def test_inactive_user(self, mock_verify: mock.MagicMock):
        user = UserFactory.create(
            email="inactive@example.com",
            is_active=False,
        )
        firebase_token_payload = {
            "uid": "inactive-user-01",
            "email": user.email,
            "email_verified": True,
        }

        mock_verify.return_value = firebase_token_payload

        response = self.client.post(FIREBASE_AUTH_URL, {"token": "valid"}, format="json")
        assert response.status_code == 400
        assert response.json() == {
            "non_field_errors": ["user is inactive. please contact admin"],
        }
