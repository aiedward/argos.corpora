"""
Extractor
==============

Extracts data, information and images
for articles.
"""

from http.client import IncompleteRead
from http.cookiejar import CookieJar
from readability.readability import Document
from goose import Goose
from dateutil.parser import parse

from urllib import request, error
from os.path import splitext
from http.client import BadStatusLine
from itertools import chain

from corpora.logger import logger
from corpora.request import make_request, MaxRetriesReached

class NotHTML(Exception):
    pass

def extract(url, existing_data={}, min_text_length=400, fetch_images=True):
    """
    Extracts data for an article url,
    returns extracted data as a dict.

    Can optionally provide `existing_data`,
    which is a dictionary representing an RSS-retrieved article.
    This data will be favored over extracted data (that is,
    if another value for a key is extracted, it will be overwritten
    by an existing value in `existing_data`).
    """

    # Complete HTML content for this entry.
    try:
        entry_data, html = extract_entry_data(url, fetch_images=fetch_images)
    except (error.HTTPError, error.URLError, ConnectionResetError, BadStatusLine) as e:
        if type(e) in [error.URLError, BadStatusLine] or e.code == 404:
            # Can't reach, skip.
            logger.exception('Error extracting data for url {0}'.format(url))
            return
        else:
            # Just skip so things don't break!
            logger.exception('Error extracting data for url {0}'.format(url))
            return
    except MaxRetriesReached:
        # Just skip so things don't break!
        logger.exception('Error extracting data for url {0}'.format(url))
        return
    except NotHTML:
        # Just skip so things don't break!
        logger.exception('Response content-type was not html for url {0}'.format(url))
        return

    if entry_data is None:
        return

    full_text = entry_data.cleaned_text

    # Skip over entries that are too short.
    if len(full_text) < min_text_length:
        return

    # Get the image url, if one is found.
    image_url = ''
    if entry_data.top_image:
        image_url = entry_data.top_image.src

    existing = {}
    if existing_data:
        published = parse(existing_data.get('published', entry_data.publish_date))
        updated = parse(existing_data.get('updated', published))
        existing = {
            'published': published,
            'updated': updated,
            'title': existing_data.get('title', entry_data.title),
            'authors': extract_authors(existing_data),
            'tags': extract_tags(existing_data, known_tags=entry_data.tags)
        }

    extracted = {
        'ext_url': entry_data.canonical_link or url,
        'text': full_text,
        'published': entry_data.publish_date,
        'title': entry_data.title,
        'image': image_url,
        'tags': entry_data.tags
    }

    # Give preference to existing data.
    return dict(chain(extracted.items(), existing.items()))


def extract_tags(entry, known_tags=None):
    """
    Extract tags from a feed's entry,
    returning it in a simpler format (a list of strings).

    Args:
        | entry (dict)        -- the entry
        | known_tags (set)    -- known tags

    This operates assuming the tags are formatted like so::

        [{'label': None,
             'scheme': 'http://www.foreignpolicy.com/category/topic/military',
             'term': 'Military'},
        {'label': None,
             'scheme': 'http://www.foreignpolicy.com/category/topic/national_security',
             'term': 'National Security'}]

    This seems to be the standard.
    """
    tags = []

    # Use known tags if available.
    if known_tags is not None:
        tags += list(known_tags)

    # If tags are supplied, use them.
    if 'tags' in entry:
        tags += [tag['term'] for tag in entry['tags']]

    return list(set(tags))

def extract_authors(entry):
    """
    Extracts authors from an entry,
    creating those that don't exist.

    Args:
        | entry (dict)   -- the entry

    There isn't a consistent way authors are specified
    in feed entries::

        # Seems to be the most common
        "author_detail": {
            "name": "John Heimer"
        }

        # Seems to always come with author_detail, i.e. redundant
        "author": "John Heimer"

        # Have only seen this empty...so ignoring it for now.
        "authors": [
            {}
        ]

        # Sometimes the name is in all caps:
        "author_detail": {
            "name": "JOHN HEIMER"
        }

        # Sometimes authors are combined into a single string,
        # with extra words.
        "author_detail" :{
            "name": "By BEN HUBBARD and HWAIDA SAAD"
        }

    In fact, some feeds use multiple forms!
    """
    names = entry.get('author_detail', {}).get('name') or entry.get('author')

    authors = []

    if names is not None:
        # Parse out the author names.
        names = names.lower()

        # Remove 'by' if its present.
        if names[0:3] == "by ":
            names = names[3:]

        # Split on commas and 'and'.
        names = names.split(',')
        if ' and ' in names[-1]:
            names += names.pop().split(' and ')

        # Remove empty strings.
        names = list(filter(None, names))

        for name in names:
            name = name.strip().title()
            authors.append(name)
    return authors


def extract_entry_data(url, fetch_images=True):
    """
    Fetch the full content for a feed entry url.

    Args:
        | url (str)    -- the url of the entry.

    Returns:
        | entry_data -- Goose object.
        | str        -- the full text, including html.
    """

    html = _get_html(url)
    g = Goose()
    g.config.enable_image_fetching = fetch_images

    try:
        # Use Goose to extract data from the raw html,
        # Use readability to give us the html of the main document.
        return g.extract(raw_html=html), Document(html).summary()

    except UnicodeDecodeError as e:
        logger.exception('UnicodeDecodeError with html: {0}'.format(html))
        return None, ''




def _get_html(url):
    # Some sites, such as NYTimes, track which
    # articles have been viewed with cookies.
    # Without cookies, you get thrown into an infinite loop.
    cookies = CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cookies))

    # Get the raw html.
    # Spoof a user agent.
    # This can help get around 403 (forbidden) errors.
    html = ''
    try:
        resp = make_request(url, open_func=opener.open, headers={'User-Agent': 'Chrome'})
        content_type = resp.headers['Content-Type']
        if 'text/html' not in content_type:
            raise NotHTML("Content-Type is not text/html, was {0}".format(content_type))
        html = resp.read()
    except IncompleteRead as e:
        html = e.partial

    # Some HTML comes with additional characters prior
    # to the actual document, so we want to strip everything up
    # to the first tag.
    html = html[html.index(b'<'):]

    return html
