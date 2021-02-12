#! ./venv/bin/python3
"""
Reads most files supplied.
"""

from utils.any2md import file2md
from utils.md2ssml import md2ssml
from utils.ssml2audio import ssml2audio

if __name__ == '__main__':
    import argparse
    import logging

    logging.getLogger().setLevel(logging.INFO)

    args = argparse.ArgumentParser(description='Converts most files to audio.')
    args.add_argument('path', help='path to the file to be converted to audio')

    args = args.parse_args()

    ssml2audio(md2ssml(file2md(args.path)), '.'.join(args.path.split('.')[:-1]))
