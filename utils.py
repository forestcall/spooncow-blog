__author__ = 'daniel@spooncow.com (Daniel Chapman)'

from unicodedata import normalize  # for slugify
import re
from google.appengine.ext import ndb



def slugify(text, delim=u'-'):
    """utility to create and tidy up a url slug"""
    
    _punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', unicode(word)).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))
