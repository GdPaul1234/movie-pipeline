#!/usr/bin/python3

import argparse
from pathlib import Path
import json
import os
import sys

def main():
    """
    Dump TVHeadEnd metadata to #{basename}.metadata.json file
    v0.3

    usage: python dump_record_metadata.py "%f" --basename "%b" \
         --title "%t" --sub-title "%s" --description "%d" \
         --start-real "%S" --stop-real "%E" \
         --error-message "%e" --nb-data-errors "%R" \
         --recording-id "%U"
    """
    scriptname = os.path.basename(__file__)
    parser = argparse.ArgumentParser(scriptname)

    parser.add_argument('fullpath', metavar='FULLPATH', help='Full path to recording')
    parser.add_argument('--basename', help='Basename of recording')
    parser.add_argument('--channel', help='Nom de la chaine')
    parser.add_argument('--title', required=True, help='Program title')
    parser.add_argument('--sub-title', required=True, help='Program subtitle or summary')
    parser.add_argument('--description', required=True, help='Program description')
    parser.add_argument('--start-real', help='Start time stamp of recording, UNIX epoch', type=int)
    parser.add_argument('--stop-real', help='Stop time stamp of recording, UNIX epoch', type=int)
    parser.add_argument('--error-message', help='Error message')
    parser.add_argument('--nb-data-errors', help='Number of data errors during recording', type=int)
    parser.add_argument('--recording-id', help='Unique ID of recording')

    options = vars(parser.parse_args())

    recording_path = Path(options['fullpath'])
    metadata_path = recording_path.with_suffix(f'{recording_path.suffix}.metadata.json')

    metadata_path.write_text(json.dumps(options, indent=2), encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())
