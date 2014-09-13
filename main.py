"""
Corpora
==============

Collects article data from feeds,
but does not apply any processing on them.
Just stores the data to build a corpus
to be processed later/for later training.
"""

import sys
import json

from corpora.models import Source, Feed
from corpora import collector
import sampler

def load_sources():
    """
    Loads sources to construct a corpus from.

    The `sources.json` file should have a structure of::

        {
            'The New York Times': [
                'http//www.nytimes.com/services/xml/rss/nyt/World.xml',
                'http//www.nytimes.com/services/xml/rss/nyt/politics.xml'
            ]
        }
    """
    sources_fs = open('sources.json', 'r')
    sources = json.load(sources_fs)
    for source_name, feeds in sources.items():

        # Get/create the Source.
        source = Source.objects(name=source_name).first()
        if not source:
            source = Source(name=source_name)
            source.save()

        # Add the feeds.
        for feed_url in feeds:
            if not Feed.objects(ext_url=feed_url).first():
                feed = Feed(ext_url=feed_url, source=source)
                feed.save()

def collect():
    collector.collect()

def sample():
    if len(sys.argv) < 3:
        print('Please specify the path to the WikiNews pages-articles XML to sample from.')
        return

    sampler.sample(sys.argv[2])

def sample_preview():
    if len(sys.argv) < 3:
        print('Please specify the path to the WikiNews pages-articles XML to sample from.')
        return

    sampler.sample(sys.argv[2], preview=True)


def main():
    if len(sys.argv) < 2:
        print('You must specify a command: [load_sources, collect, sample]')
        return

    try:
        globals()[sys.argv[1]]();
    except KeyError:
        print('Doesn\'t seem to be a valid command.')
        return

if __name__ == '__main__':
    main()
