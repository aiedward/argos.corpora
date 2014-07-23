"""
Collector
==============

Collects articles from remote feeds to build a corpus.
"""

from corpora.models import Feed, Article
from corpora import extractor
from corpora.request import MaxRetriesReached
from corpora.logger import logger, notify

import json
import feedparser
from urllib import error
from dateutil.parser import parse

from xml.sax._exceptions import SAXException
from http.client import BadStatusLine

def collect():
    """
    Collects articles from all of the feeds.
    """

    stats = {}
    for feed in Feed.objects:
        try:
            logger.info('Fetching from {0}...'.format(feed.ext_url))
            new_articles = fetch(feed)
            stats[feed.ext_url] = len(new_articles)

        except SAXException as e:
            # Error with the feed, make a note.
            logger.info('Error fetching from {0}.'.format(feed.ext_url))
            feed.errors += 1
            feed.save()
    pretty_stats = json.dumps(stats, sort_keys=True, indent=4)
    notify('Corpora collection complete.', 'Total article count: {0}\n\nResults for this pass:\n{1}'.format(len(Article.objects), pretty_stats))

def fetch(feed):
    """
    Fetches articles from a single feed.
    """
    # Fetch the feed data.
    data = feedparser.parse(feed.ext_url)
    new_articles = []

    # If the `bozo` value is anything
    # but 0, there was an error parsing (or connecting) to the feed.
    if data.bozo:
        # Some errors are ok.
        if not isinstance(data.bozo_exception, feedparser.CharacterEncodingOverride) and not isinstance(data.bozo_exception, feedparser.NonXMLContentType):
            raise data.bozo_exception

    for entry in data.entries:

        # URL for this entry.
        url = entry['links'][0]['href']

        # Check for an existing Article.
        # If one exists, skip.
        if Article.objects(ext_url=url).first():
            continue

        # Complete HTML content for this entry.
        try:
            entry_data, html = extractor.extract_entry_data(url)
        except (error.HTTPError, error.URLError, ConnectionResetError, BadStatusLine) as e:
            if type(e) == error.URLError or e.code == 404:
                # Can't reach, skip.
                logger.exception('Error extracting data for url {0}'.format(url))
                continue
            else:
                # Just skip so things don't break!
                logger.exception('Error extracting data for url {0}'.format(url))
                continue
        except MaxRetriesReached:
            # Just skip so things don't break!
            logger.exception('Error extracting data for url {0}'.format(url))
            continue

        if entry_data is None:
            continue

        full_text = entry_data.cleaned_text

        # Skip over entries that are too short.
        if len(full_text) < 400:
            continue

        url = entry_data.canonical_link or url
        published = parse(entry.get('published')) if entry.get('published') else entry_data.publish_date
        updated = parse(entry.get('updated')) if entry.get('updated') else published
        title = entry.get('title', entry_data.title)

        # Secondary check for an existing Article,
        # by checking the title and source.
        existing = Article.objects(title=title).first()
        if existing and existing.feed.source == feed.source:
            continue

        # Download and save the top article image.
        image_url = ''
        if entry_data.top_image:
            image_url = entry_data.top_image.src

        article = Article(
            ext_url=url,
            feed=feed,
            text=full_text,
            authors=extractor.extract_authors(entry),
            tags=extractor.extract_tags(entry, known_tags=entry_data.tags),
            title=title,
            created_at=published,
            updated_at=updated,
            image=image_url
        )
        article.save()
        new_articles.append(article)

    return new_articles
