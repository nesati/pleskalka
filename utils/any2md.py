#! ./venv/bin/python3
"""
Converts most files to markdown.
"""
import logging
import os
import tempfile

tmpdir = tempfile.TemporaryDirectory()


def pdf2md(file):
    """
    A python wrapper for the @opendocsg/pdf2md package.
    Converts a pdf file to markdown.

    :param file: path to pdf file
    :return: str: markdown
    """
    import subprocess
    return subprocess.check_output(f'node utils/pdf2md.js "{os.path.realpath(file)}"', shell=True, encoding='UTF-8')


def pandoc(file, output):
    """
    A python wrapper for the pandoc.
    Converts a file to markdown.

    :param file: path to input file
    :param output: path to markdown file
    """
    os.system(f'pandoc -o "{os.path.realpath(output)}" -t markdown_strict --atx-headers "{os.path.realpath(file)}"')


def libreoffice(file, outdir):
    """
    A python wrapper for the libre office.
    Converts a file to odt.

    :param file: path to input file
    :param outdir: path to output directory
    """
    os.system(f'soffice --headless --convert-to odt --outdir "{os.path.realpath(outdir)}" "{os.path.realpath(file)}"')


def file2md(path):
    """
    Converts most files to markdown. Assumes files have proper extensions.

    :param path: path to input file
    :return:
    """

    # get file extension
    ext = path.split(".")[-1].lower()

    # check existence of file
    if not os.path.isfile(path):
        logging.fatal('File not found!')
        exit(1)

    # convert file to markdown
    if ext in ["md", "markdown"]:
        logging.info("Interpreting as markdown")
        with open(path, 'r') as f:
            return f.read()
    elif ext == "txt":
        logging.info("plain text - Interpreting as markdown")
        with open(path, 'r') as f:
            return f.read()
    elif ext == "pdf":
        import re

        logging.info("parsing pdf using @opendocsg/pdf2md")
        md = pdf2md(path)

        if re.search(r'\w', md) is None:
            logging.warning("Pdf seems to be empty attempting OCR using OCRmyPDF")
            os.system(f'ocrmypdf -l ces -j 8 "{path}" "{os.path.join(tmpdir.name, "ocr.pdf")}"')

            logging.info("parsing pdf using @opendocsg/pdf2md")
            md = pdf2md(os.path.join(tmpdir.name, "ocr.pdf"))

            tmpdir.cleanup()
        return md
    elif ext in ['doc', 'rtf']:
        logging.info(f"parsing {ext} using libreoffice")
        libreoffice(path, tmpdir.name)

        logging.info(f"parsing odt using pandoc")
        pandoc(os.path.join(tmpdir.name, '.'.join(path.split('.')[:-1])+'.odt'), os.path.join(tmpdir.name, "converted.md"))
        with open(os.path.join(tmpdir.name, 'converted.md'), 'r', encoding='UTF-8') as f:
            md = f.read()

        tmpdir.cleanup()

        return md
    elif ext in ['html', 'odt', 'docx', 'epub', 'creole', 'dbk', 'xml', 'haddock', 'ipynb', 'jats', 'jira', 'man',
                 'muse', 'opml', 'org', 'rst', 't2t', 'textile']:
        logging.info(f"parsing {ext} using pandoc")

        pandoc(path, os.path.join(tmpdir.name, 'converted.md'))
        with open(os.path.join(tmpdir.name, 'converted.md'), 'r', encoding='UTF-8') as f:
            md = f.read()

        tmpdir.cleanup()

        return md
    else:
        logging.warning(f"unknown file extension {ext}")
        logging.info("assuming plain markdown")
        with open(path, 'r') as f:
            return f.read()


if __name__ == '__main__':
    import argparse

    args = argparse.ArgumentParser(description='Converts most files to markdown.')
    args.add_argument('path', help='path to the file to be converted to markdown')

    args = args.parse_args()

    print(file2md(args.path))
