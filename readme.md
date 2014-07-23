# argos.corpora
A corpus-builder for Argos.

This is very simple: it just collects article data from a set of sources
specified in `sources.json` at regular intervals. Later this data can be
processed, used for training, or w/e.

## Setup
* Setup `config.py`
* Setup the virtualenv and install the dependencies (`requirements.txt`)
* Setup the `crontab`
* Ensure MongoDB is running
* Activate the virtualenv and run `python main.py load_sources` to load
the sources (from `sources.json`) into the database.