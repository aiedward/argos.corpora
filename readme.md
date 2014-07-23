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

## Exporting the database
At some point you will probably want to move the data elsewhere for
processing.

If you ssh into your machine with the database, you can get an export:
```bash
$ mongodump -d argos_corpora -o /tmp
$ tar -cvzf /tmp/dump.tar.gz /tmp/dump
```

From your local machine, you can grab it with `scp`
and then import into a local MongoDB instance.
```bash
$ scp remoteuser@remotemachine:/tmp/dump.tar.gz .
$ tar -zxvf dump.tar.gz
$ cd dump
$ mongorestore argos_corpora
```