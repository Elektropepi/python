# -*- coding: utf-8 -*-
# setup: pip install dict.cc.py

"""Translate with Dict CC."""

import os
import re

from albertv0 import *
#from .dictccpy.dictcc import Dict

# -*- coding: utf-8 -*-

try:
    # python2
    import urllib2
    from urllib import quote_plus
except ImportError:
    # python3
    import urllib.request as urllib2
    from urllib.parse import quote_plus

import re

try:
    from bs4 import BeautifulSoup
except ImportError:
    from BeautifulSoup import BeautifulSoup
    BeautifulSoup.find_all = BeautifulSoup.findAll

AVAILABLE_LANGUAGES = {
    "en": "english",
    "de": "german",
    "fr": "french",
    "sv": "swedish",
    "es": "spanish",
    "bg": "bulgarian",
    "ro": "romanian",
    "it": "italian",
    "pt": "portuguese",
    "ru": "russian"
}


class UnavailableLanguageError(Exception):
    def __str__(self):
        return "Languages have to be in the following list: {}".format(
            ", ".join(AVAILABLE_LANGUAGES.keys()))


class Result(object):
    def __init__(self, from_lang=None, to_lang=None, translation_tuples=None):
        self.from_lang = from_lang
        self.to_lang = to_lang
        self.translation_tuples = list(translation_tuples) \
                                  if translation_tuples else []

    @property
    def n_results(self):
        return len(self.translation_tuples)


class Dict(object):
    @classmethod
    def translate(cls, word, from_language, to_language):
        if any(map(lambda l: l.lower() not in AVAILABLE_LANGUAGES.keys(),
                   [from_language, to_language])):
            raise UnavailableLanguageError

        response_body = cls._get_response(word, from_language, to_language)
        result = cls._parse_response(response_body)

        return cls._correct_translation_order(result, word)

    @classmethod
    def _get_response(cls, word, from_language, to_language):
        subdomain = from_language.lower()+to_language.lower()

        url = "https://"+subdomain+".dict.cc/?s=" + quote_plus(word.encode("utf-8"))

        req = urllib2.Request(
            url,
            None,
            {'User-agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0'}
        )

        res = urllib2.urlopen(req).read()
        return res.decode("utf-8")

    # Quick and dirty: find javascript arrays for input/output words on response body
    @classmethod
    def _parse_response(cls, response_body):
        soup = BeautifulSoup(response_body, "html.parser")

        suggestions = [tds.find_all("a") for tds in soup.find_all("td", class_="td3nl")]
        if len(suggestions) == 2:
            languages = [lang.string for lang in soup.find_all("td", class_="td2")][:2]
            if len(languages) != 2:
                raise Exception("dict.cc results page layout change, please raise an issue.")

            return Result(
                from_lang=languages[0],
                to_lang=languages[1],
                translation_tuples=zip(
                    [e.string for e in suggestions[0]],
                    [e.string for e in suggestions[1]]
                ),
            )

        translations = [tds.find_all(["a", "var"]) for tds in soup.find_all("td", class_="td7nl", attrs={'dir': "ltr"})]
        if len(translations) >= 2:
            languages = [next(lang.strings) for lang in soup.find_all("td", class_="td2", attrs={'dir': "ltr"})]
            if len(languages) != 2:
                raise Exception("dict.cc results page layout change, please raise an issue.")

            return Result(
                from_lang=languages[0],
                to_lang=languages[1],
                translation_tuples=zip(
                    [" ".join(map(lambda e: " ".join(e.strings), r)) for r in translations[0:-1:2]],
                    [" ".join(map(lambda e: e.string if e.string else "".join(e.strings), r)) for r in translations[1:-1:2]]
                ),
            )

        return Result()

    # Heuristic: left column is the one with more occurrences of the to-be-translated word
    @classmethod
    def _correct_translation_order(cls, result, word):

        if not result.translation_tuples:
            return result

        [from_words, to_words] = zip(*result.translation_tuples)

        return result if from_words.count(word) >= to_words.count(word) \
                      else Result(
                          from_lang=result.to_lang,
                          to_lang=result.from_lang,
                          translation_tuples=zip(to_words, from_words),
                      )





iconPath = os.path.dirname(__file__)+"/dictcc.png"
englishIconPath = os.path.dirname(__file__)+"/great_britain_flag.svg"
germanIconPath = os.path.dirname(__file__)+"/german_flag.svg"

__iid__ = "PythonInterface/v0.2"
__prettyname__ = "DictCC"
__version__ = "1.0"
__trigger__ = "dict "
__author__ = "Paul Ganster"
__dependencies__ = []

if not iconPath:
    iconPath = ":python_module"

def initialize():
    pass

def processResult(result):
    matches = re.match(r'(.*?)([{[].*)?$', result)
    attributes = matches.group(2)
    if attributes is not None:
        attributes = attributes.strip()
    return matches.group(1).strip(), attributes

def highlightResult(text, attributes):
    highlight = text
    if attributes is not None:
        highlight += " <small><i>" + attributes + "</i></small>"
    return highlight

def processQuery(query):
    text = query.string
    if len(text) < 4:
        return None
    parts = text.split(" ")
    if len(parts) < 1:
        return None
    return text

def getLanguageCode(language):
    if language == "Deutsch":
        return "de"
    if language == "Englisch":
        return "en"
    raise Exception("Can't get valid language code")

def getLanguageFromTranslation(query, from_language_result, to_language_result, from_translation_lang,
                               to_translation_lang):
    if query in from_language_result:
        return from_translation_lang, to_translation_lang
    if query in to_language_result:
        return to_translation_lang, from_translation_lang
    print("Can't find corresponding translation language")
    return "de", "en"

def getFromLanguage(to_language):
    if to_language == "de":
        return "en"
    if to_language == "en":
        return "de"
    return None

def handleQuery(query):
    results = []
    if query.isTriggered:
        processedQuery = processQuery(query)
        if processedQuery is None:
            return Item(
                id=__prettyname__,
                icon=iconPath,
                completion=query.rawString,
                text=__prettyname__,
                subtext="Enter a query: dict text_to_translate"
            )
        query_string = processedQuery
        translation = Dict.translate(query_string, "de", "en")
        if translation.n_results == 0:
            return Item(
                id=__prettyname__,
                icon=iconPath,
                completion=query.rawString,
                text=__prettyname__,
                subtext="No results"
            )

        from_translation_lang = getLanguageCode(translation.from_lang.strip())
        to_translation_lang = getLanguageCode(translation.to_lang.strip())
        for from_language_result, to_language_result in translation.translation_tuples:

            from_language, to_language = getLanguageFromTranslation(query.string, from_language_result,
                                                                    to_language_result, from_translation_lang,
                                                                    to_translation_lang)

            needs_switch = from_language != getLanguageCode(translation.from_lang.strip())
            if needs_switch:
                temp = from_language_result
                from_language_result = to_language_result
                to_language_result = temp

            to_language_text, to_language_attributes = processResult(to_language_result)
            from_language_text, from_language_attributes = processResult(from_language_result)
            if to_language == "en":
                result_icon = englishIconPath
            else:
                result_icon = germanIconPath
            results.append(Item(
                id=__prettyname__,
                icon=result_icon,
                completion=query.rawString,
                text=highlightResult(to_language_text, to_language_attributes),
                subtext=highlightResult(from_language_text, from_language_attributes),
                actions=[
                    ClipAction("Copy translation to clipboard", to_language_text)
                ]
        ))
    return results
