import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch,MagicMock
from src.core.config.document import load_settings,validate

ROOT=Path(__import__('src.core.config.document',fromlist=['x']).__file__).resolve().parents[3]


class UnifiedSettingsTests(unittest.TestCase):
    def execute(self,folder,config,code):
        path=Path(folder)/'settings.json';path.write_text(json.dumps(config))
        (Path(folder)/'.env').write_text('OPENAI_API_KEY=dotenv-sentinel\nOPEN_SCRIBE_STREAM=false\nOPEN_SCRIBE_SUMMARY=false\n')
        env=os.environ.copy()
        for name in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','OPENROUTER_API_KEY'):env.pop(name,None)
        env.update(OPEN_SCRIBE_SETTINGS=str(path),OPEN_SCRIBE_STREAM='false',OPEN_SCRIBE_SUMMARY='false',MIN_WORKER='999',OPEN_SCRIBE_DOWNLOADS_PATH='/ignored')
        run=subprocess.run([sys.executable,'-B','-c','import sys;sys.path.insert(0,'+repr(str(ROOT))+');'+code],cwd=folder,env=env,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        return json.loads(run.stdout)

    def test_json_overrides_old_environment_and_never_autoloads_dotenv(self):
        with tempfile.TemporaryDirectory() as d:
            result=self.execute(d,{'copy_to_path':'copies','workers':{'min':2},'output':{'stream':True},'stages':{'summary':{'enabled':True}}},
                "import json,os;from src.core.config.settings import Config;print(json.dumps({'copy':str(Config.DOWNLOADS_PATH),'stream':Config.ENABLE_STREAM,'summary':Config.ENABLE_SUMMARY,'workers':Config.MIN_WORKER,'key':bool(Config.OPENAI_API_KEY),'env_key':'OPENAI_API_KEY' in os.environ}))")
            self.assertEqual(result,{'copy':str((Path(d)/'copies').resolve()),'stream':True,'summary':True,'workers':2,'key':False,'env_key':False})

    def test_null_copy_and_cli_overrides_do_not_edit_file(self):
        with tempfile.TemporaryDirectory() as d:
            result=self.execute(d,{'copy_to_path':None,'stages':{'summary':{'enabled':True}}},
                "import json;from src.core.config.settings import Config;from src.core.presentation.cli import create_argument_parser;args=create_argument_parser().parse_args(['input.wav','--no-summary']);print(json.dumps({'copy':Config.COPY_TO_DOWNLOADS,'summary':args.summary,'configured_summary':Config.ENABLE_SUMMARY}))")
            self.assertEqual(result,{'copy':False,'summary':False,'configured_summary':True})

    def test_show_does_not_read_key_file_and_validate_rejects_invalid_settings(self):
        with tempfile.TemporaryDirectory() as d:
            result=self.execute(d,{'providers':{'openai':{'api_key_file':'does-not-exist'}}},
                "from src.core.presentation.configuration import main;main(['show'])")
            self.assertEqual(result['settings']['providers']['openai']['api_key_file'],str((Path(d)/'does-not-exist').resolve()))
            self.assertNotIn('dotenv-sentinel',json.dumps(result))
            for bad in ({'output':{'stream':'true'}},{'copy_to_path':True},{'unknown':1},{'workers':{'min':6,'max':2}},{'providers':{'openai':{'api_key':'forbidden'}}}):
                with self.assertRaises(ValueError):validate(bad,Path(d)/'settings.json')

    def test_json_paths_reach_actual_transcription_and_copy_and_keep_original(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'원본.wav';source.write_bytes(b'fixture original')
            code="""
import contextlib,io,json
from pathlib import Path
from unittest.mock import patch,MagicMock
from src.core.presentation.cli import main
from src.core.config.settings import Config
transcriber=MagicMock();transcriber.is_available.return_value=True;transcriber.transcribe.return_value='보존할 본문'
sys.argv=['scr',str(Path.cwd()/'원본.wav')]
with patch('src.core.presentation.cli.get_transcriber',return_value=transcriber),contextlib.redirect_stdout(io.StringIO()):
    assert main()==0
assert (Config.TRANSCRIPT_PATH/'원본.txt').read_text()=='보존할 본문'
assert (Config.DOWNLOADS_PATH/'원본.txt').read_text()=='보존할 본문'
print(json.dumps({'original_kept':(Path.cwd()/'원본.wav').exists(),'database':Config.DB_PATH.exists(),'copy':str(Config.DOWNLOADS_PATH)}))
"""
            result=self.execute(d,{'copy_to_path':'custom-copy','paths':{'data':'custom-data'},'stages':{'summary':{'enabled':False}},'output':{'stream':False}},code)
            self.assertEqual(result,{'original_kept':True,'database':True,'copy':str((Path(d)/'custom-copy').resolve())})

    def test_integrations_and_downloader_use_json_instead_of_environment(self):
        from src.integrations import notion
        from src.integrations.downloader import YouTubeDownloader
        config=validate({'download':{'remote_components':[],'player_clients':['web']},'integrations':{'notion':{'enabled':True,'database_id':'json-db'}}},Path('/tmp/settings.json'))
        with tempfile.TemporaryDirectory() as d,patch('src.core.config.document.load_settings',return_value=config),patch('src.core.providers.models.credential',return_value=None),patch.dict(os.environ,{'OPEN_SCRIBE_YTDLP_REMOTE_COMPONENTS':'ignored','OPEN_SCRIBE_YTDLP_PLAYER_CLIENT':'ignored','PROXY_URL':'ignored'}):
            dl=YouTubeDownloader(Path(d)/'audio',Path(d)/'video',Path(d)/'temp')
            self.assertEqual(dl._base_opts()['extractor_args']['youtube']['player_client'],['web'])
            self.assertNotIn('proxy',dl._base_opts())
            self.assertNotIn('remote_components',dl._base_opts())
        fake=MagicMock();fake.Client.return_value.post.return_value.json.return_value={'id':'page'}
        with patch.object(notion,'load_settings',return_value=config),patch.object(notion,'credential',return_value='fixture'),patch.object(notion,'_get_client',return_value=fake),patch.dict(os.environ,{'OPEN_SCRIBE_NOTION':'false','NOTION_DATABASE_ID':'ignored'}):
            self.assertTrue(notion.is_configured())
            self.assertEqual(notion.save_to_notion('title','url','engine',transcript='text'),'page')
            self.assertEqual(fake.Client.return_value.post.call_args.kwargs['json']['parent']['database_id'],'json-db')
