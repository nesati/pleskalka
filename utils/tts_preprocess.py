"""
Processes text so that it is read correctly.
"""
import logging
import re

import enchant
from weighted_levenshtein import lev
import numpy as np

import utils.roman_num as roman

diacritics = {
    'ě': 'e',
    'é': 'e',
    'ú': 'u',
    'ů': 'u',
    'š': 's',
    'č': 'c',
    'ř': 'r',
    'ž': 'z',
    'ý': 'y',
    'á': 'a',
    'í': 'i',
    'ó': 'o',
    'ď': 'd',
    'ň': 'n',
    'ť': 't',
}

diacritics = str.maketrans(diacritics)

substitute_costs = np.ones((128, 128), dtype=np.float64)

# substituting m and n is cheaper
substitute_costs[ord('m'), ord('n')] = 0.5
substitute_costs[ord('n'), ord('m')] = 0.5

# substituting r and n is cheaper
substitute_costs[ord('r'), ord('n')] = 0.5
substitute_costs[ord('n'), ord('r')] = 0.5

# for ocr correction insertion and deletion have a bigger cost than substitution
insert_costs = np.ones(128, dtype=np.float64) + 0.25
delete_costs = np.ones(128, dtype=np.float64) + 0.25


class TTSPreprocessor:
    """
    Processes text so that it is read correctly.

    Modules:
        Roman numbers
        Ordinal numbers
        Full names
        Arrows
        Autocorrect
    """

    def __init__(self, use_roman=True, use_ordinal=True, full_names=True, arrows=True, autocorrect=True):
        self.use_roman = use_roman
        self.use_ordinal = use_ordinal
        self.full_names = full_names
        self.arrows = arrows
        self.autocorrect = autocorrect

        self.dictionary = enchant.Dict("cs")

    def _roman_translate(self, match):
        output = match.group()
        match = match.group(1)
        if re.compile(roman.RE_VALIDATE).match(match):
            output = output.replace(match, str(roman.decode(match)))
        return output

    def name_preprocessor(self, text):
        """
        Finds abbreviated names and makes them into full names.

        :param text: text
        :return: modified text
        """

        letters = 'aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzž'

        output = re.sub(
            rf"(([{letters.upper()}]|Ch)\. )+[{letters.upper()}][{letters.lower()}]+",
            self._name_translate, text)
        return output

    def _shorten_name(self, name):
        name = name.split(" ")
        shortened = []
        for part in name[:-1]:
            if part[0] != "C":
                shortened.append(part[0])
            elif part[1] == "h":  # Special case for Ch
                shortened.append("Ch")
            else:
                shortened.append("C")
        shortened.append(name[-1])
        return ". ".join(shortened)

    def _name_translate(self, match):
        import wikipedia
        wikipedia.set_lang("cs")
        name = match.group()
        results = wikipedia.search(name)
        logging.debug(results)
        for result in results:
            if name.startswith(self._shorten_name(result)[:-3]):
                # the [:-3] is a crude hack to avoid problems with conjugation
                return " ".join(result.split(" ")[:-1] + [name.split(" ")[-1]])  # use the original conjugated form
        return name

    def roman_preprocessor(self, text):
        """
        Finds roman numerals and makes them into arabic numerals.

        :param text: text
        :return: modified text
        """
        output = re.sub(roman.RE_FIND, self._roman_translate, text)
        return output

    def arrow_preprocessor(self, text):
        """
        Finds arrows and writes them in plain text.

        :param text: text
        :return: modified text
        """
        output = re.sub(r'[-—―–‒−‐­=]+ ?>', ' šipka ', text)
        return output

    def onlyascii(self, char):
        if ord(char) < 48 or ord(char) > 127:
            return ''
        else:
            return char

    def distance(self, text1, text2):
        # filter text
        text1 = text1.lower()
        # unfortunately weighted_levenshtein doesn't support unicode so diacritics have a cost of 0
        text1 = text1.translate(diacritics)
        text1 = ''.join(filter(self.onlyascii, text1))

        text2 = text2.lower()
        # unfortunately weighted_levenshtein doesn't support unicode so diacritics have a cost of 0
        text2 = text2.translate(diacritics)
        text2 = ''.join(filter(self.onlyascii, text2))

        return lev(text1, text2, insert_costs=insert_costs, delete_costs=delete_costs,
                   substitute_costs=substitute_costs)

    def autocorrect_preprocessor(self, text):
        """
        Checks each word againts a dictionary and tries to correct it.

        :param text: text
        :return: modified text
        """

        tokens = re.finditer(r'([-—―–‒−‐­0-9aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzž]+|[^ ])', text,
                             flags=re.IGNORECASE)
        words = []
        for token in tokens:
            token = token.group()
            if len(token) == 1 and token[0] not in '-—―–‒−‐­0-9aábcčdďeéěfghiíjklmnňoópqrřsštťuúůvwxyýzž':
                words.append(token)
            elif self.dictionary.check(token):
                words.append(token)
            else:
                suggestions = self.dictionary.suggest(token)

                if len(suggestions) == 0:
                    logging.warning(f'no correction for {token}')
                    words.append(token)
                    continue

                distances = list(map(lambda suggestion: self.distance(suggestion, token), suggestions))
                min_distance = min(distances)

                if min_distance > 2:
                    logging.warning(f'no correction for {token}')
                    words.append(token)
                    continue

                min_positions = [i for i, x in enumerate(distances) if x == min_distance]

                if len(min_positions) > 1:
                    logging.warning(f'ambiguous correction for {token}')
                    logging.debug(f'corrections: {list(map(lambda idx: suggestions[idx], min_positions))}')
                    words.append(token)
                    continue

                words.append(suggestions[min_positions[0]])

        return " ".join(words)

    def ordinal_preprocessor(self, text):
        """
        Finds roman numerals and marks them in ssml.

        :param text: text
        :return: modified text
        """

        # assumes ordinal numbers are max 2 digits long
        text = re.sub(r'([0-9]{1,2})\.[^$]',
                      lambda match: f' <say-as interpret-as="ordinal">{match.group(1)}.</say-as> ', text)

        return text

    def preprocess_sentence(self, text):
        """
        Modifies input based on settings.

        :param text: text
        :return: modified text
        """
        output = text
        if self.full_names:
            output = self.name_preprocessor(output)
        if self.use_roman:
            output = self.roman_preprocessor(output)
        if self.arrows:
            output = self.arrow_preprocessor(output)
        if self.autocorrect:
            output = self.autocorrect_preprocessor(output)
        if self.use_ordinal:
            output = self.ordinal_preprocessor(output)
        return output


if __name__ == "__main__":
    import sys

    preprocessor = TTSPreprocessor()
    for line in sys.stdin:
        print(preprocessor.preprocess_sentence(line))
