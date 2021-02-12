#! ./venv/bin/python3
"""
Converts most files to markdown.
"""
import logging
import os


def pdf2md(file):
    """
    A python wrapper for the @opendocsg/pdf2md package.
    Converts a pdf file to markdown.

    :param file: path to pdf file
    :return: str: markdown
    """
    import subprocess
    return subprocess.check_output(f"node utils/pdf2md.js '{os.path.realpath(file)}'", shell=True, encoding='UTF-8')


def pandoc(file, output):
    """
    A python wrapper for the pandoc.
    Converts a file to markdown.

    :param file: path to input file
    :param output: path to markdown file
    """
    os.system(f"pandoc -o '{os.path.realpath(output)}' -t markdown_strict '{os.path.realpath(file)}'")


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
            os.system(f"ocrmypdf -l ces -j 8 '{path}' '{path}.ocr.pdf'")

            logging.info("parsing pdf using @opendocsg/pdf2md")
            md = pdf2md(path + ".ocr.pdf")

            os.remove(path + ".ocr.pdf")
        return md
    elif ext == 'doc':
        # TODO convert using libreoffice
        logging.fatal('.doc not support please convert to docx using other program')
        exit(1)
    elif ext in ['html', 'odt', 'docx', 'epub']:  # TODO all formats supported by pandoc
        logging.info(f"parsing {ext} using pandoc")

        pandoc(path, '/tmp/converted.md')
        with open('/tmp/converted.md', 'r') as f:
            md = f.read()

        os.remove('/tmp/converted.md')

        return md
    elif ext == "ssml":
        logging.info("Interpreting as raw SSML")
        with open(path, 'r') as f:
            ssml = f.read()
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
