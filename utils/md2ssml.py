#! ./venv/bin/python3
"""
Converts markdown to speech synthesis markup language.
"""
import re
from abc import ABC
from html.parser import HTMLParser

from markdown import markdown

import utils.separator as separator
from utils.tts_preprocess import TTSPreprocessor

RE_ITALICS = r"\*([^*]+)\*"
RE_QUOTES = r"[„\"“]([^^„\"“”“]+)[“\"”]"
RE_BRACKETS = r"[[({]([[\](){}]+)[\])}]"

ALLOWED_TAGS = ['em', 'strong', 'p', 'b', 'i']


class FilterHtmlTags(HTMLParser, ABC):
    """
    Removes all html tags except specified allowed_tags.
    """

    def __init__(self, allowed_tags):
        super().__init__()
        self.out = ''
        self.allowed_tags = allowed_tags

    def handle_starttag(self, tag, attrs):
        """
        Handles a starttag.

        :param tag: tag name
        :param attrs: tag attributes
        """
        if tag in ALLOWED_TAGS:
            self.out += '<' + tag + '>'
        else:
            self.out += ' '

    def handle_endtag(self, tag):
        """
        Handles a endtag.

        :param tag: tag name
        """
        if tag in ALLOWED_TAGS:
            self.out += '</' + tag + '>'
        else:
            self.out += ' '

    def handle_data(self, data):
        """
        Handles a text node.

        :param data: text
        """
        self.out += data

    def process(self, data):
        """
        Processes a html string.

        :param data: str: html to filter
        :return: str: filtered html
        """
        super().feed(data)
        return re.sub(r' +', ' ', self.out)  # remove duplicate spaces


html_filter = FilterHtmlTags(ALLOWED_TAGS)
preprocessor = TTSPreprocessor()


def paragraph_ssml_process(match):
    """
    Converts markdown to ssml in one paragraph.

    :param match: regex match where group 1 is the paragraph content
    :return: str: ssml
    """
    text = match.group(1)
    sentences = separator.separate(text)  # separate text into sentences
    sentences = filter(lambda x: len(x.strip()) > 0, sentences)
    sentences = map(preprocessor.preprocess_sentence, sentences)

    # enforce google cloud text to speech 5000 character limit
    paragraphs = []
    paragraph = []
    for sent in sentences:
        paragraph.append(sent)
        a = sum(map(len, paragraph))
        if a > 4000:  # leave some space for control tags (<p><s><emphasis>...)
            paragraph = paragraph[0:-1]
            paragraphs.append(paragraph)
            paragraph = [sent]
    paragraphs.append(paragraph)

    return "\n".join(map(lambda paragraph_sent: f"<p><s>{'</s><s>'.join(paragraph_sent)}</s></p>", paragraphs))


def md2ssml(md):
    """
    Converts a markdown string to a ssml string.

    :param md: str input markdown
    :return: str output ssml
    """

    # remove non-paragraph newlines
    md = re.sub(r'\n(?=[^\n\r])', ' ', md)

    # remove duplicate newlines
    md = re.sub(r'\n+', '\n\n', md)

    # fix ordered lists
    md = re.sub(r'^\d+\.', lambda match: match.group().replace('.', '\\.'), md, flags=re.MULTILINE)

    # fix words split by newline
    md = re.sub(r'(?<=\S)[-—―–‒−‐­]\s+', '', md)

    # fix comment tags
    md = re.sub(r'<[-!]+>', ' ', md)

    # fix whitespaces (affects markdown header parsing)
    md = re.sub(r'^\s+', '\n', md, flags=re.MULTILINE)
    md = re.sub(r'\s+$', '\n', md, flags=re.MULTILINE)

    # improve paragraph detection (paragraphs are irrelevant for pronunciation and are used as parsing helpers only)
    md = re.sub(r'(^#{1,6} .+)\n([\w\W]*?)(?=^#{1,6} .*)',
                lambda match: match.group(1) + '\n\n' + re.sub(r'\s+', ' ', match.group(2),
                                                               flags=re.MULTILINE) + '\n\n', md + '\n# ',
                flags=re.MULTILINE)

    # parse markdown
    html = markdown(md)

    # remove any unused tags
    out = html_filter.process(html)

    # emphasize italics
    out = out.replace("<em>", "<emphasis>")
    out = out.replace("</em>", "</emphasis>")

    # emphasize bold
    out = out.replace("<strong>", "<emphasis>")
    out = out.replace("</strong>", "</emphasis>")

    # emphasize terms in quotes
    out = re.sub(RE_QUOTES, lambda match: '<emphasis>' + match.group(1) + '</emphasis>', out)

    # emphasize terms in brackets
    out = re.sub(RE_BRACKETS, lambda match: '<emphasis>' + match.group(1) + '</emphasis>', out)

    # emphasize headings
    out = re.sub(r"<h[1-6]>", '<break time="1s"/><emphasis level="strong">', out)
    out = re.sub(r"</h[1-6]>", "</emphasis>", out)

    # remove empty paragraphs
    out = re.sub(r'<p>\s+</p>', '\n', out)

    # process paragraph
    paragraph_regex = r"<p>(.*?)</p>"  # using non-greedy operator (?)
    out = re.sub(paragraph_regex, paragraph_ssml_process, out)

    return out


if __name__ == '__main__':
    import sys

    print(md2ssml(sys.stdin.read()))
