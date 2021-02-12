"""
Small library for working with roman numerals.
"""

RE_FIND = r"[\s^]([MDCLXVI]+)($|[\s.,]+ [^A-Z])"
RE_VALIDATE = r"^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$"


def decode(roman):
    """
    Decodes a roman number.

    :param roman: str: roman number
    :return: int: number
    """
    num_map = dict(zip('MDCLXVI', (1000, 500, 100, 50, 10, 5, 1)))

    num = 0
    for r, r1 in zip(roman, roman[1:]):
        rd, rd1 = num_map[r], num_map[r1]
        num += -rd if rd < rd1 else rd
    return num + num_map[roman[-1]]


def encode(num):
    """
    Encodes a roman number.

    :param num: int: number
    :return: str: roman number
    """
    num_map = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'),
               (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    roman = ''
    while num > 0:
        for i, r in num_map:
            while num >= i:
                roman += r
                num -= i
    return roman
