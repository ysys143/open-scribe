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
        print(json.dumps({'path':str(settings_path()),'settings':data} if args.action=='show' else {'path':str(settings_path()),'valid':True},ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError) as error:
        print(str(error),file=sys.stderr);return 1
