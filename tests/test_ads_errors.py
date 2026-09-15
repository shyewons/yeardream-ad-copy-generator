import unittest
from unittest.mock import patch, Mock
import httpx
from ollama import ResponseError
from langchain_core.exceptions import OutputParserException
from fastapi.testclient import TestClient
from main import app


class AdErrorTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.payload = dict(product_name='Cup', features='350ml', target='Worker', channel='Instagram', tone='Friendly')

    def test_model_errors(self):
        cases = [
            (ConnectionError('offline'), 503, 'MODEL_UNAVAILABLE'),
            (httpx.ConnectError('offline'), 503, 'MODEL_UNAVAILABLE'),
            (httpx.ReadTimeout('slow'), 504, 'MODEL_TIMEOUT'),
            (OutputParserException('invalid JSON'), 502, 'INVALID_MODEL_OUTPUT'),
            (ResponseError('missing', 404), 503, 'MODEL_NOT_FOUND'),
            (ResponseError('failed', 500), 502, 'MODEL_ERROR'),
            (RuntimeError('private internal detail'), 500, 'INTERNAL_ERROR'),
        ]
        for error, status, code in cases:
            with self.subTest(code=code), patch('services.ad_generator.chain', Mock(invoke=Mock(side_effect=error))), self.assertLogs('routers.ads', level='ERROR'):
                response = self.client.post('/ads/generate', json=self.payload)
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json()['detail']['code'], code)
                self.assertNotIn('private internal detail', response.text)

    def test_invalid_output(self):
        with patch('services.ad_generator.chain', Mock(invoke=Mock(return_value={}))), self.assertLogs('routers.ads', level='ERROR'):
            response = self.client.post('/ads/generate', json=self.payload)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['detail']['code'], 'INVALID_MODEL_OUTPUT')

    def test_invalid_input_does_not_call_model(self):
        with patch('services.ad_generator.chain') as chain:
            response = self.client.post('/ads/generate', json={})
            self.assertEqual(response.status_code, 422)
            chain.invoke.assert_not_called()

    def test_success(self):
        ad = dict(headline='Title', body='Body', cta='See more', hashtags=['#cup'])
        with patch('services.ad_generator.chain', Mock(invoke=Mock(return_value=ad))):
            response = self.client.post('/ads/generate', json=self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ad)


if __name__ == '__main__':
    unittest.main()
