from main.tests import TestCase


class TestHealthCheck(TestCase):
    def test_html(self):
        response = self.client.get("/health-check/")
        assert response.status_code == 200
        assert response.content not in [None, ""]

    def test_json(self):
        for url, headers in [
            ("/health-check/?format=json", {}),
            ("/health-check/", dict(accept="application/json")),
        ]:
            response = self.client.get(url, headers=headers)
            assert response.status_code == 200

            resp_data = response.json()

            # Check custom fields
            app_data = resp_data.pop("app")
            assert app_data["environment"] == "DEV"
            assert app_data["git"] is not None
            assert app_data["git"]["commit"] is not None
            self.assertWarning(app_data["git"]["branch"] is not None, "git branch name is empty")
            assert app_data["git"]["repository"] is not None
            assert app_data["git"]["repository"]["url"] is not None
            assert app_data["git"]["repository"]["commit"] is not None
            assert app_data["git"]["repository"]["commit_github_metadata"] is not None
            self.assertWarning(app_data["git"]["repository"]["branch"] is not None, "git repository's branch name is empty")
