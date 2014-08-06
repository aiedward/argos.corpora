# argos.corpora
A corpus-builder for Argos.

This is very simple: it just collects article data from a set of sources
specified in `sources.json` at regular intervals. Later this data can be
processed, used for training, or w/e.

This project has the additional functionality of digesting WikiNews
`pages-articles` XML dumps to build out evaluation Event clusters (see
below).


## Setup
* Setup `config.py`
* Run `setup.sh`
* Setup the `crontab`
* Activate the virtualenv and run `python main.py load_sources` to load
the sources (from `sources.json`) into the database.

## Exporting the database
At some point you will probably want to move the data elsewhere for
processing.

If you ssh into your machine with the database, you can get an export:
```bash
$ mongodump -d argos_corpora -o /tmp
$ tar -cvzf /tmp/dump.tar.gz /tmp/argos_corpora
```

From your local machine, you can grab it with `scp`
and then import into a local MongoDB instance.
```bash
$ scp remoteuser@remotemachine:/tmp/dump.tar.gz .
$ tar -zxvf dump.tar.gz
$ cd dump
$ mongorestore argos_corpora
```

It's likely though that you want to export only the training fields
(`title` and `text`) to a JSON for training:
```bash
$ mongoexport -d argos_corpora -c article -f title,text --jsonArray -o articles.json
```

## The Sampler Package
The `sampler` package can digest WikiNews `pages-articles` XML dumps for
the purpose of assembling evaluation data.

It takes a WikiNews page with at least two cited sources and assumes that
it constitutes an Event, and its sources are member articles. This data
is saved to MongoDB and can later be used to evaluate the performance of
the main Argos project's clustering.

You can download the latest `pages-articles` dump at
[http://dumps.wikimedia.org/enwikinews/latest/](http://dumps.wikimedia.org/enwikinews/latest/).

I strongly suggest you pare down this dump file to maybe only the last
100 pages, so you're not fetching a ton of articles.

To use it, run:
```
$ python main.py sample /path/to/the/wikinews/dump.xml
```

That will parse the pages, and for any page that has over two cited
sources, it will fetch the article data for those sources and save
everything to MongoDB.

Then you can export that data:
```
$ mongoexport -d argos_corpora -c sample_event --jsonArray -o ~/Desktop/sample_events.json
```

And this can be used in the main [argos](https://github.com/publicscience/argos) project's for evaluation.