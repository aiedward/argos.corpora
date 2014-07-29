import re
from mwlib import parser
from mwlib.refine.compat import parse_txt
from lxml import etree

from corpora import extractor
from corpora.logger import logger
from sampler.models import SampleEvent, SampleArticle

NAMESPACE = 'http://www.mediawiki.org/xml/export-0.8/'

# This will extract the source url and the published date from the MediaWiki markup.
# Example:
# {{source|url=http://bigstory.ap.org/article/why-airlines-didnt-avoid-risky-ukraine-airspace|title=Why airlines didn't avoid risky Ukraine airspace|author=David Koenig and Scott Mayerowitz|pub=Associated Press|date=July 18, 2014}}
# returns ('http://...', 'July 18, 2014')
SOURCE_RE = re.compile(r'\{\{source\|url=([^\|\n]+)[|\n].+?(?<=date=)([^\n\}]+)', re.DOTALL)

# This is used to check if a page is non-English.
FOREIGNLANG_RE = re.compile(r'\{\{foreign language\}\}')

def _find(elem, *tags):
        """
        Finds a particular subelement of an element.

        Args:
            | elem (lxml Element)  -- the MediaWiki text to cleanup.
            | *tags (strs)      -- the tag names to use. See below for clarification.

        Returns:
            | lxml Element -- the target element.

        You need to provide the tags that lead to it.
        For example, the `text` element is contained
        in the `revision` element, so this method would
        be used like so::

            _find(elem, 'revision', 'text')

        This method is meant to replace chaining calls
        like this::

            text_el = elem.find('{%s}revision' % NAMESPACE).find('{%s}text' % NAMESPACE)
        """
        for tag in tags:
            elem = elem.find('{%s}%s' % (NAMESPACE, tag))
        return elem

def process_element(elem):
    ns = int(_find(elem, 'ns').text)
    if ns != 0: return

    # Get the text of the page.
    text = _find(elem, 'revision', 'text').text

    # Exclude pages marked as 'foreign language'.
    if FOREIGNLANG_RE.search(text) is not None: return

    title = _find(elem, 'title').text

    # Extract the source links.
    sources = SOURCE_RE.findall(text)

    return {
        'title': title,
        'sources': sources
    }

def sample(file):
    """
    Parses a WikiNews pages-articles XML dump,
    (which you can get at http://dumps.wikimedia.org/enwikinews/latest/)
    and generates SampleEvents and SampleArticles from the pages.
    """
    logger.info('Sampling from {0}...'.format(file))

    # Create the iterparse context
    context = etree.iterparse(file, events=('end',), tag='{%s}%s' % (NAMESPACE, 'page'))

    # Iterate
    for event, elem in context:
        # Run process_element on the element.
        data = process_element(elem)

        # Extract remote data for source urls,
        # if available.
        if data is not None:
            build_samples(**data)

        # Clear the elem, since we're done with it
        elem.clear()

        # Eliminate now-empty refs from the root node
        # to the specified tag.
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    # Clean up the context
    del context

    logger.info('Sampling complete.')

def build_samples(title, sources):
    # We want at least two sources.
    if len(sources) < 2: return

    logger.info('Building sample event `{0}`'.format(title))
    e = SampleEvent.objects(title=title).first()
    if e is None:
        e = SampleEvent(title=title)
        e.save()

    for url, published in sources:
        if SampleArticle.objects(ext_url=url).first():
            continue
        d = extractor.extract(url, existing_data={
            'published': published
        })
        if d is not None:
            a = SampleArticle(**d)
            a.event = e
            a.save()