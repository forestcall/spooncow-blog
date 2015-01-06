__author__ = 'daniel@spooncow.com (Daniel Chapman)'

from unicodedata import normalize  # for slugify
import re
from google.appengine.ext import ndb

"""
Some utility stuff for processing models
"""
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim=u'-'):
    """utility to create and tidy up a url slug"""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', unicode(word)).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))

# I am declaring the user and post models here because this is where they will be used the most
# TODO - is there a proper structure for these? e.g. a models directory or module file


class Author(ndb.Model):
    """
    Model for Authors.

    We aren't building for super high performance so we will keep authors and posts separate (i.e. normalized).

    - Authors will contain a keyReference back to their posts.
    """
    user_id  = ndb.StringProperty()  # link to google account
    name    = ndb.StringProperty()  # Author's display name
    bio     = ndb.StringProperty()  # blurb for the bottom of pages
    avatar  = ndb.BlobProperty()  # uploaded pic. TODO - pull direct from G+ profile if possible
    prefs   = ndb.StringProperty()  # will have a json list of misc preference settings
    posts   = ndb.KeyProperty(repeated=True)


class Post(ndb.Model):
    """
    Model for blog posts

    - status is a string and not an integer so custom post types can do their own thing if they need more statuses
    - Posts will link back to their author
    TODO - add category / tags in. another KeyProp list perhaps?
    """
    author      = ndb.KeyProperty()
    title       = ndb.StringProperty(required=True)
    slug        = ndb.StringProperty(required=True)
    status      = ndb.StringProperty(required=True)
    post_type   = ndb.StringProperty(required=True)
    body        = ndb.TextProperty()
    image       = ndb.BlobProperty()  # for comics, can get to image easily. also useful for header images for posts
    attributes  = ndb.StringProperty()  # will be a json list of a python dictionary of misc settings
    modified_on = ndb.DateTimeProperty(required=True, auto_now=True)
    created_on  = ndb.DateTimeProperty(required=True, auto_now_add=True)
    publish_up  = ndb.DateTimeProperty(required=True, auto_now_add=True)
    publish_down = ndb.DateTimeProperty()

    @classmethod
    def get_by_slug(cls, slug):
        q = cls.query(cls.slug == slug)
        return q.get()

    @classmethod
    def get_posts(cls, status=None, limit=20):
        if status:
            q = cls.query(cls.status == status)
        else:
            q = cls.query()
        q.order(-cls.publish_up)
        return q.fetch(limit)
