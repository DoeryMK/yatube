from http import HTTPStatus

from django.test import Client, TestCase


class ViewTestClacc(TestCase):
    def setUp(self):
        self.client = Client()

    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
