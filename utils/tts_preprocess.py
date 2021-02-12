"""
Processes text so that it is read correctly.
"""
import logging
import re

import roman_num as roman


class TTSPreprocessor:
    """
    Processes text so that it is read correctly.

    Modules:
        Roman numbers
        Ordinal numbers
        Full names
    """

    def __init__(self, use_roman=True, use_ordinal=True, full_names=True):
        self.use_roman = use_roman
        self.use_ordinal = use_ordinal
        self.full_names = full_names

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
        if self.use_ordinal:
            output = self.ordinal_preprocessor(output)
        return output


if __name__ == "__main__":
    import sys

    preprocessor = TTSPreprocessor()
    for line in sys.stdin:
        print(preprocessor.preprocess_sentence(line))
