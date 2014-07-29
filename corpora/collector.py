"""
Collector
==============

Collects articles from remote feeds to build a corpus.
"""

from corpora.models import Feed, Article
from corpora import extractor
from corpora.logger import logger, notify

import json
import feedparser

from xml.sax._exceptions import SAXException

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

        data = extractor.extract(url, existing_data=entry)

        if data is None:
            continue

        # Secondary check for an existing Article,
        # by checking the title and source.
        existing = Article.objects(title=data['title']).first()
        if existing and existing.feed.source == feed.source:
            continue

        data['feed'] = feed

        article = Article(**data)
        article.save()
        new_articles.append(article)

    return new_articles
