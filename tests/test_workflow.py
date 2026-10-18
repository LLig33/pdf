import unittest
from unittest.mock import patch, AsyncMock
import pymupdf as fitz
from fastapi.testclient import TestClient
import app

class Workflow(unittest.TestCase):
    def setUp(self):
        app.DOCS.clear()
        self.client = TestClient(app.app)

    def pdf(self, text=True):
        doc = fitz.open()
        page = doc.new_page(width=400, height=500)
        page.draw_rect(fitz.Rect(200, 250, 350, 400), color=(0, .5, 0), fill=(0, .8, .2))
        if text:
            page.insert_text((40, 70), 'Hello world. This is a magazine.', fontsize=12)
        data = doc.tobytes()
        doc.close()
        return data

    def upload(self, data):
        r = self.client.post('/api/documents', files={'file': ('sample.pdf', data, 'application/pdf')})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()['id']

    def test_translation_export_and_removal(self):
        token = self.upload(self.pdf())
        r = self.client.get(f'/api/documents/{token}/pages/1')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.startswith(b'\x89PNG'))
        with patch('app.translate_blocks', new=AsyncMock(return_value=['你好，世界。这是一本杂志。'])):
            r = self.client.post(f'/api/documents/{token}/translate')
        self.assertEqual(r.status_code, 200, r.text)
        r = self.client.get(f'/api/documents/{token}/download')
        self.assertEqual(r.status_code, 200)
        with fitz.open(stream=r.content, filetype='pdf') as doc:
            self.assertIn('你好', doc[0].get_text())
            self.assertNotIn('Hello', doc[0].get_text())
            self.assertEqual(tuple(doc[0].rect), (0, 0, 400, 500))
            self.assertTrue(doc[0].get_drawings())
        self.client.delete(f'/api/documents/{token}')
        self.assertEqual(self.client.get(f'/api/documents/{token}/download').status_code, 404)

    def test_scanned_document_requires_ocr(self):
        token = self.upload(self.pdf(False))
        self.assertEqual(self.client.post(f'/api/documents/{token}/translate').status_code, 422)

    def test_deployment_auth_and_health(self):
        with patch.dict('os.environ', {'SITE_PASSWORD': 'test-access-password'}):
            self.assertEqual(self.client.get('/healthz').json(), {'status': 'ok'})
            self.assertEqual(self.client.get('/').status_code, 401)
            self.assertEqual(self.client.get('/api/status').status_code, 401)
            self.assertEqual(self.client.get('/', auth=('paperbridge', 'wrong')).status_code, 401)
            self.assertEqual(self.client.get('/', auth=('paperbridge', 'test-access-password')).status_code, 200)
            r = self.client.get('/api/status', auth=('paperbridge', 'test-access-password'))
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.headers['cache-control'], 'no-store')

    def test_invalid_document_and_missing_service(self):
        self.assertEqual(self.client.post('/api/documents', files={'file': ('a.pdf', b'not pdf')}).status_code, 400)
        token = self.upload(self.pdf())
        with patch.dict('os.environ', {'TRANSLATION_API_KEY': ''}):
            self.assertEqual(self.client.post(f'/api/documents/{token}/translate').status_code, 503)
        self.assertEqual(self.client.get(f'/api/documents/{token}/download').status_code, 409)

if __name__ == '__main__':
    unittest.main()
