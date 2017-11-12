import os
import urllib.parse

import sys

import re
from googleapiclient.discovery import build
import pprint

from langdetect import detect_langs

my_api_key = os.environ.get('GOOGLE_CUSTOM_SEARCH_API_TOKEN')
my_cse_id_all = os.environ.get('GOOGLE_CSE_ID_ALL')
my_cse_id_yurasic_ru_all = os.environ.get('GOOGLE_CSE_ID_YURASIC_RU_ALL')


# https://stackoverflow.com/questions/37083058/programmatically-searching-google-in-python-using-custom-search

def inner_google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res['items']


CHORDS_EN = "chords"
CHORDS_RU = "аккорды"


def get_word_chords_in_lang(s):
    langs = detect_langs(s)
    if not langs:
        raise Exception("Can't guess lang (langdetect)")
    if langs[0] == 'en':
        return CHORDS_EN + " "
    if langs[0] == 'ru':
        return CHORDS_RU + " "
    print("Lang guess return " + str(langs) + " (but we want 'ru' or 'en' as first)", file=sys.stderr)
    return CHORDS_RU + " "


GSEARCH_displayLink = 'displayLink'
GSEARCH_link = 'link'
INTERESTING_KEYS = [GSEARCH_displayLink, GSEARCH_link, 'title']

iv_templates = {
    'yurasic.ru': "2db311abdefc3d",
    'urasic.ru': "2db311abdefc3d",
    'muzland.ru': "8b93af5fe73bbd",
    'mychords.net': "2278ec51479966",
}


def url_clean_http_www(url):
    if url.startswith('http'):
        url = re.sub(r'https?://', '', url)
    if url.startswith('www.'):
        url = re.sub(r'www\.', '', url)
    return url


def filter_results(result):
    result = {k: result[k] for k in INTERESTING_KEYS}
    result[GSEARCH_displayLink] = url_clean_http_www(result[GSEARCH_displayLink])

    print("---")
    print(result[GSEARCH_displayLink])
    print(result[GSEARCH_link])

    # t.me/iv?url=...&rhash=...
    # "url=" + urllib.parse.urlencode(result[GSEARCH_link]) +
    if result[GSEARCH_displayLink] in iv_templates.keys():
        result['iv'] = "t.me/iv?" + \
                       "url=" + urllib.parse.quote(result[GSEARCH_link]) + \
                       "&rhash=" + iv_templates[result[GSEARCH_displayLink]]

    return result


def google_search(s):
    results_yurasic = inner_google_search(get_word_chords_in_lang(s) + s,
                                  my_api_key, my_cse_id_yurasic_ru_all, num=3)

    ans = ["Search results: "]
    ans += ["len: " + str(len(results_yurasic))]

    results_yurasic = list(map(filter_results, results_yurasic))

    results_all = inner_google_search(get_word_chords_in_lang(s) + s,
                                  my_api_key, my_cse_id_all, num=5)

    ans = ["Search results: "]
    ans += ["len: " + str(len(results_all))]

    results_all = list(map(filter_results, results_all))

    return results_yurasic + results_all


    # sites += [urllib.parse.quote_plus(pprint.pformat(result))]
    # sites += [pprint.pformat(result)]

    ####################
    # we need next keys
    # displayLink: domain name
    # link: full link
    # snippet and title - maybe for future use
