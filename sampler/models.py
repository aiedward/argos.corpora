from mongoengine import *
from datetime import datetime

import config

# Connect to MongoDB.
connect('argos_corpora', host=config.MONGO_URI)

class SampleArticle(EmbeddedDocument):
    ext_url     = StringField(unique=True)
    title       = StringField()
    text        = StringField()
    image       = StringField()
    authors     = ListField(StringField())
    created_at  = DateTimeField(default=datetime.utcnow)
    updated_at  = DateTimeField(default=datetime.utcnow)

class SampleEvent(Document):
    title = StringField()
    articles = ListField(EmbeddedDocumentField(SampleArticle))
