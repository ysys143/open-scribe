"""Non-secret effective configuration inspection."""
import argparse
import json
import sys
from src.core.config.document import load_settings,settings_path


def main(argv):
    parser=argparse.ArgumentParser(prog='scribe config')
    parser.add_argument('action',choices=('show','validate'))
    args=parser.parse_args(argv)
    try:
        data=load_settings()
        from src.core.speech.adapters import REGISTRY,policy
        asr=data['stages']['asr'];cap=REGISTRY.get(asr['model'])
        if cap:
            spec,provider,enabled=policy(asr['model'],asr['options'],asr['provider'])
            effective={'provider':provider,'diarization':spec.diarization,'diarize':enabled,'single_request':spec.diarization=='supported','stream':False if spec.diarization=='supported' else data['output']['stream']}
        else:effective={'diarization':'unsupported','single_request':False,'stream':data['output']['stream']}
        print(json.dumps({'path':str(settings_path()),'settings':data,'effective_asr':effective} if args.action=='show' else {'path':str(settings_path()),'valid':True},ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError,RuntimeError) as error:
        print(str(error),file=sys.stderr);return 1
