from django.test import TestCase


class VdpUrlsSmokeTest(TestCase):
    """Basic smoke tests for routing and template rendering."""

    def test_home_route(self):
        response = self.client.get('/home/')
        self.assertEqual(response.status_code, 200)
