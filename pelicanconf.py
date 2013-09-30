#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Andrea Zonca'
SITENAME = u"Andrea Zonca's blog"
SITEURL = 'http://zonca.github.io'

TIMEZONE = 'America/Los_Angeles'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = 'feeds/all.atom.xml'
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

# Blogroll
LINKS =  (('Pelican', 'http://getpelican.com/'),
          ('Python.org', 'http://python.org/'),
          ('Jinja2', 'http://jinja.pocoo.org/'),
          ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('You can add links in your config file', '#'),
          ('Another social link', '#'),)

DEFAULT_PAGINATION = 10

ARTICLE_URL = '{date:%Y}/{date:%m}/{slug}.html'
ARTICLE_SAVE_AS = ARTICLE_URL

THEME = "./middle-theme/middle"

TWITTER_USERNAME = "andreazonca"
GITHUB_USERNAME = "zonca"
ABOUTME_USERNAME = "andreazonca"
GOOGLEPLUS_USERNAME = "102215770805040369170"
EMAIL_ADDRESS = "andrea.zonca|on the google mail service"
HOMEPAGE_INTRO = "Andrea Zonca: notes about Python, high performance computing, data analysis"

ENABLE_DISQUS = False

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = False

PLUGIN_PATH = 'pelican-plugins'
PLUGINS = ["sitemap", "googleplus_comments"]
#PLUGINS = ['liquid_tags.img', 'liquid_tags.notebook']
