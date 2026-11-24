import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from src.core.providers import models


def run_post(handle,**kwargs):
    """Call models.post against a mock transport; return (result_or_error, sleeps, output)."""
    sleeps=[];output=io.StringIO()
    real=httpx.Client
    def factory(*args,**kw):return real(transport=httpx.MockTransport(handle),timeout=kw.get('timeout'))
    with patch.object(models,'credential',return_value='fixture'),patch.object(httpx,'Client',side_effect=factory),\
         patch.object(models.time,'sleep',side_effect=sleeps.append),contextlib.redirect_stdout(output):
        try:result=models.post('openai','audio/transcriptions',**kwargs)
        except Exception as error:result=error
    return result,sleeps,output.getvalue()


class PostRetryTests(unittest.TestCase):
    def test_transport_error_is_retried_then_succeeds(self):
        calls=[]
        def handle(request):
            calls.append(request)
            if len(calls)<3:raise httpx.ReadTimeout('slow',request=request)
            return httpx.Response(200,json={'text':'ok'})
        result,sleeps,output=run_post(handle,json_body={})
        self.assertEqual(result,{'text':'ok'})
        self.assertEqual(len(calls),3)
        self.assertEqual(len(sleeps),2)
        self.assertIn('ReadTimeout',output)

    def test_transport_error_stops_after_three_attempts_and_names_the_cause(self):
        calls=[]
        def handle(request):
            calls.append(request);raise httpx.ConnectError('down',request=request)
        result,sleeps,_=run_post(handle,json_body={})
        self.assertIsInstance(result,ValueError)
        self.assertEqual(len(calls),3)
        self.assertRegex(str(result),'3 attempts')
        self.assertRegex(str(result),'ConnectError')
        self.assertRegex(str(result),'outcome uncertain')

    def test_rate_limit_and_server_errors_are_retried(self):
        for status in (429,500,502,503,504):
            with self.subTest(status=status):
                calls=[]
                def handle(request):
                    calls.append(request)
                    return httpx.Response(status if len(calls)==1 else 200,json={'text':'ok'})
                result,_,_=run_post(handle,json_body={})
                self.assertEqual(result,{'text':'ok'})
                self.assertEqual(len(calls),2)

    def test_retry_after_header_is_honored_within_limit(self):
        calls=[]
        def handle(request):
            calls.append(request)
            if len(calls)==1:return httpx.Response(429,headers={'retry-after':'7'},json={})
            return httpx.Response(200,json={'text':'ok'})
        _,sleeps,_=run_post(handle,json_body={})
        self.assertEqual(sleeps,[7])

    def test_client_errors_are_not_retried(self):
        for status in (400,401,403,404):
            with self.subTest(status=status):
                calls=[]
                def handle(request):
                    calls.append(request);return httpx.Response(status,json={})
                result,sleeps,_=run_post(handle,json_body={})
                self.assertIsInstance(result,ValueError)
                self.assertRegex(str(result),'HTTP '+str(status))
                self.assertEqual(len(calls),1)
                self.assertEqual(sleeps,[])

    def test_exhausted_http_error_reports_status_and_attempts(self):
        calls=[]
        def handle(request):
            calls.append(request);return httpx.Response(503,json={})
        result,_,_=run_post(handle,json_body={})
        self.assertIsInstance(result,ValueError)
        self.assertEqual(len(calls),3)
        self.assertRegex(str(result),'HTTP 503')
        self.assertRegex(str(result),'3 attempts')

    def test_malformed_success_body_is_retried(self):
        calls=[]
        def handle(request):
            calls.append(request)
            return httpx.Response(200,content=b'{"text":') if len(calls)==1 else httpx.Response(200,json={'text':'ok'})
        result,_,_=run_post(handle,json_body={})
        self.assertEqual(result,{'text':'ok'})

    def test_file_upload_is_resent_in_full_on_each_attempt(self):
        bodies=[]
        def handle(request):
            bodies.append(request.read())
            if len(bodies)==1:raise httpx.ReadError('reset',request=request)
            return httpx.Response(200,json={'text':'ok'})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'chunk.wav';path.write_bytes(b'RIFF-fixture-audio-bytes')
            with path.open('rb') as audio:
                result,_,_=run_post(handle,data={'model':'gpt-transcribe'},files={'file':(path.name,audio,'audio/wav')})
        self.assertEqual(result,{'text':'ok'})
        self.assertEqual(len(bodies),2)
        self.assertIn(b'RIFF-fixture-audio-bytes',bodies[0])
        self.assertIn(b'RIFF-fixture-audio-bytes',bodies[1])


if __name__=='__main__':
    unittest.main()
