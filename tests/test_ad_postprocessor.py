import unittest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from main import app
from services.ad_postprocessor import clean_text, clean_ad_data

class PostprocessTests(unittest.TestCase):
    def test_text(self):
        self.assertEqual(clean_text('## **텀블러** ☕️\n\n- 350ml, 면 100%\n- [확인](https://example.com)'), '텀블러\n\n350ml, 면 100%\n확인')
        self.assertEqual(clean_text('👩🏽‍💻 1️⃣ 가족 👨‍👩‍👧‍👦'), '가족')

    def test_limits_and_tags(self):
        data = clean_ad_data(dict(headline='가'*120, body='나'*1100, cta='다'*120, hashtags=['#Cup', 'cup', ' #면 100% ', '😀', '#a', '#b', '#c', '#d']))
        self.assertEqual([len(data[k]) for k in ('headline','body','cta')], [100,1000,100])
        self.assertEqual(data['hashtags'], ['#Cup','#면100','#a','#b','#c'])

    def test_api_cleanup_and_invalid_output(self):
        client = TestClient(app)
        payload = dict(product_name='Cup',features='350ml',target='Worker',channel='Instagram',tone='Friendly')
        for title, status in [('**제목** 📚',200), ('📚',502)]:
            with self.subTest(title=title), patch('services.ad_generator.chain', Mock(invoke=Mock(return_value=dict(headline=title,body='본문',cta='확인',hashtags=['#컵'])))):
                if status == 502:
                    with self.assertLogs('routers.ads', level='ERROR'):
                        response=client.post('/ads/generate',json=payload)
                else:
                    response=client.post('/ads/generate',json=payload)
                self.assertEqual(response.status_code,status)
                if status == 200:
                    self.assertEqual(response.json()['headline'],'제목')
                else:
                    self.assertEqual(response.json()['detail']['code'],'INVALID_MODEL_OUTPUT')
