__author__ = 'daniel@spooncow.com'

"""
Admin Actions:
    - write a new post
    - update a post
    - delete a post
    - edit their profile (bio, blurb, display name, etc.) TODO - link to G+ profile
"""
import os
from webapp2_extras import jinja2
from unicodedata import normalize  # for slugify
import webapp2
import config
import re
# import json #to serialise our preferences
from webapp2_extras import json  # use this one??
from google.appengine.ext import ndb


# json.dumps(pyDict)
# json.loads(jsonStr)

"""
Configure our template environment
- set the directory to match the current theme set in our config.py
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

    def _pre_put_hook(self):
        # if we don't have a slug set create one from the title.
        # if we do have a slug then clean it before saving
        if not self.slug:
            self.slug = slugify(self.title)
        else:
            self.slug = slugify(self.slug)


class BaseHandler(webapp2.RequestHandler):
    """ Set some base methods for our handlers so they use Jinja2 correctly and easily
    """
    @webapp2.cached_property
    def jinja2(self):
        # Set the default folder to '/themes/<theme>' instead of 'templates'
        jinja2.default_config['template_path'] = os.path.join(
            os.path.dirname(__file__),
            'themes/admin',
            config.admin_theme  # pull the templates from our configured theme
        )

        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)

    def render_response(self, _template, **context):
        """
        :param _template:
        :param context:
        :return:

         Renders a template and writes the result to the response.
         Also attaches a header and footer template.
         This isn't the best way to it, but it will do for now
        TODO - make this into a single page template + content
        """
        resp_body = self.jinja2.render_template(_template, **context)
        self.response.write(resp_body)


class MainAdminHandler(BaseHandler):
    """ Display the admin dashboard - a list of recent posts, pages and other dashboard
    """
    def get(self, **kwargs):
        # TODO - make this into a dictionary of name:url for the template to cycle through
        template_values = {
            "new_post_url" : webapp2.uri_for('admin-post-edit-new', _full=True, task='edit'),
            "post_list_url": webapp2.uri_for('admin-posts-list', _full=True),
            "new_page_url": webapp2.uri_for('admin-page-edit-new', _full=True, task='edit'),
            "page_list_url": webapp2.uri_for('admin-pages-list', _full=True),
            "preferences_url": webapp2.uri_for('admin-preferences', _full=True)
        }
        self.render_response('dashboard.html', **template_values)


class PostListAdminHandler(BaseHandler):
    """ Display the post list page - a list of recent posts
    """
    def get(self, **kwargs):
        posts = Post.get_posts()
        template_values = {
            'posts': posts
        }
        self.render_response('post_list.html', **template_values)

class PostAdminHandler(BaseHandler):
    """ Create, Edit, Delete, or Preview posts
    """
    def get(self, task=None, post_slug=None, **kwargs):
        # self.response.write('<br/>'+webapp2.uri_for('admin-post-edit', _full=True, task=task, post_slug=post_slug))
        # ^ generate a url
        run_task = getattr(self, task)
        if run_task:
            run_task(post_slug)
        else:
            self.response.write('Bad task')  # This should never happen but just in case...

    def post(self, **kwargs):
        id = int(self.request.get('id'))
        title = self.request.get('title')
        slug = self.request.get('slug')
        status = self.request.get('status')
        post_type = self.request.get('post_type')
        body = self.request.get('body')

        # if we have a slug, then clean it, if not then slugify the title to give us a slug
        # TODO - validate the title to make sure we have one
        if slug:
            slug = slugify(slug)
        else:
            slug = slugify(title)

        if id:
            # not new Post get the old one
            post = Post.get_by_id(id)

            """
            Check post to confirm that our slug is unique
            Do a search by slug. if we get no hits, or a hit with the same id
                (i.e. the same object) then we are good to save
            """
            chkpost = Post.get_by_slug(slug)
            if chkpost and (chkpost.key.id() != id):
                counter = 1
                tmpslug = slug+str(counter)
                chkpost = Post.get_by_slug(tmpslug)
                # hope this works. loop through adding 1,2,3 etc to the end of the slug until we get a unique one
                while chkpost and (chkpost.key.id() != id):
                    counter += 1
                    tmpslug = slug+str(counter)
                    chkpost = Post.get_by_slug(tmpslug)

                slug = tmpslug

            # save the Post once we have a safe slug
            post.title = title
            post.slug = slug
            post.body = body
            post.status = status
            post.post_type = post_type

            post.put()
        else:
            # it is a new Post
            # check that the slug is unique
            chkpost = Post.get_by_slug(slug)
            if chkpost:
                counter = 1
                tmpslug = slug+str(counter)
                chkpost = Post.get_by_slug(tmpslug)
                # hope this works. loop through adding 1,2,3 etc to the end of the slug until we get a unique one
                # unique = no match
                while chkpost:
                    counter += 1
                    tmpslug = slug+str(counter)
                    chkpost = Post.get_by_slug(tmpslug)

                slug = tmpslug
            # save the new post.
            # TODO - this whole section isn't particularly DRY, it will need a refactor at some point
            post = Post()
            post.title = title
            post.slug = slug
            post.body = body
            post.status = status
            post.post_type = post_type

            post.put()

        self.response.write('<html><body>You wrote:<pre>')
        self.response.write(self.request.get('body'))
        self.response.write('</pre></body></html>')

    def edit(self, post_slug=None):
        template_values = {}
        # get our post and prep the template vars if we were passed a post_slug
        if post_slug:
            post = Post.get_by_slug(post_slug)

            if post:
                """
                I can pass the post object, but then it fails if it is empty.
                If I split up the object into individual variables then they work fine
                {{ post.blah }} <- errors on a new post entity
                {{ blah }} <- doesn't error
                TODO - I should probably be doing some checks rather than relying on it to fail...
                """
                template_values = {
                    'title': post.title,
                    'slug': post.slug,
                    'body': post.body,
                    'status': post.status,
                    'post_type': post.post_type,
                    'id': post.key.id(),
                    'site_name': config.site_name
                }
            else:
                # TODO - throw a 404
                self.response.write('No matching slug! 404')

        self.render_response('post_edit.html', **template_values)

    def delete(self):
        # this function should run on a http delete and also on a get task=delete
        # it's hacky but it lets us use plain urls to delete inside the site instead of putting mini-forms everywhere
        self.response.write('Delete')


class PageListAdminHandler(BaseHandler):
    """ Display the page list page - a list of recent pages
    """
    def get(self, **kwargs):
        self.response.write('Hello world Page List!')


class PageAdminHandler(BaseHandler):
    """ Create, Edit, Delete, or Preview pages
    """
    def get(self, task=None, page_id=None, **kwargs):
        self.response.write('Hello world Page!')
        if task:
            self.response.write('task: '+task)
        else:
            self.response.write('no task')

        if page_id:
            self.response.write(page_id)
        else:
            self.response.write('no page id')


class ProfileAdminHandler(BaseHandler):
    """
    Change user specific settings
    - Set display name
    - Set avatar
    - Set bio
    - Set preferences etc.
    """
    def get(self, **kwargs):
        self.response.write('Hello world Profile!')


class SettingsAdminHandler(BaseHandler):
    """
    Adjust site wide settings
    - currently using config.py, but may change it to use Datastore OR defaults in config.py
    """
    def get(self, **kwargs):
        self.response.write('Hello world Settings!')


app = webapp2.WSGIApplication([
    webapp2.Route(r'/admin', handler=MainAdminHandler, name='admin-home'),
    webapp2.Route(r'/admin/posts', handler=PostListAdminHandler, name='admin-posts-list'),
    webapp2.Route('/admin/post/<task:edit>', handler=PostAdminHandler, name='admin-post-edit-new'),  # for new posts
    webapp2.Route('/admin/post/<task:edit|delete|preview>/<post_slug>', handler=PostAdminHandler, name='admin-post-edit'),
    webapp2.Route('/admin/pages', handler=PageListAdminHandler, name='admin-pages-list'),
    webapp2.Route('/admin/page/<task:edit>', handler=PageAdminHandler, name='admin-page-edit-new'),  # for new pages
    webapp2.Route('/admin/page/<task:edit|delete|preview>/<page_slug>', handler=PageAdminHandler, name='admin-page-edit'),
    webapp2.Route('/admin/profile', handler=ProfileAdminHandler, name='admin-profile'),
    webapp2.Route('/admin/settings', handler=SettingsAdminHandler, name='admin-settings')
], debug=True)
