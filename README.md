SpoonCow Blog for Google App Engine
===================================

A basic blog that will end up hosted on GAE on http://spooncow.com.

I and some associates are using this primarily as a way of learning Python, GAE and some other snappy tech.

Basic Design Philosophy:

Split system of Site and Admin
- Site is optimised for reads with heavy caching and Jinja Templates
- Admin is optimised for usability and writes/edits with Angular + Material Design

Single Model For Content
- different types of pages use different "content_type"s
- content type management is shifted out of the core project as much as possible to templates and self contained modules
- available content types are listed in config.py

We are focusing initially on three post types:

- regular blog posts : sequentially ordered, no wysiwyg just enter your own HTML
- pages : fixed pages such as about, home, faq etc.
- image posts : consists of an image and associated text

Possible future post types:

- video posts : a link to a hosted video (may add self hosting via blobstore later)
- gallery - links a bunch of images together
- custom code
- testimonials

The plan is to build this out as a blog and front end for Python web apps that a developer can throw up on GAE with minimum fuss and start building their app behind it.

There will be few, if any 'social' features built in. We will try to import those from other systems. e.g. G+ / Discus / Facebook

Feature plans:

- Post previews
- Analytics integration
- Landing pages
- SEO parameters for pages (meta data, author urls, contributor, canonical, FB tags etc.)
- SEO analysis of post content
- PubSub Atom and RSS
- Testimonials
- Evernote Integration for Blog posts (also gives us a good wysiwyg)
- Sitemap
- Automatic-menu
- Tagging posts
- Multiple Authors
- mailing list integration (mailchimp etc)
- build system to automatically add post types

One day features:

- sales funnels
- A/B content and heading testing

Admin and post writing is enforced by google accounts. The admin panel is restricted only to side admins.

We may implement more granular acl in the future but this works for us for now.
