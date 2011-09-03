#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The MIT License

Copyright (c) 2011 Olle Johansson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import ConfigParser
import sys
import os
import logging

#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from django.template import TemplateDoesNotExist

from GoldQuest import GoldQuest
from GoldQuest.DataStoreDataHandler import *

class GoldQuestHandler(webapp.RequestHandler):
    def __init__(self):
        cfg = ConfigParser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        cfg.read(config_path)
        self.game = GoldQuest.GoldQuest(cfg)

    def get(self, command):
        response = self.game.play(command)
        if response:
            self.response.out.write(response)
        else:
            self.response.set_status(404)

class MainPageHandler(webapp.RequestHandler):
    basepath = os.path.dirname(__file__)

    def get_template(self, page, values, layout='default'):
        page = "%s.html" % page
        path = os.path.join(self.basepath, 'views', page)
        logging.info('template pathname: %s' % path)
        content = template.render(path, values)
        path = os.path.join(self.basepath, 'views', 'layouts', '%s.html' % layout)
        content = template.render(path, { 'content': content })
        return content

    def get(self, page):
        template_values = {}
        (pagename, ext) = os.path.splitext(page)
        logging.info("page: %s pagename: %s ext: %s" % (page, pagename, ext))
        if not pagename or pagename == 'index':
            self.show_page('index')
        elif page == 'favicon.ico':
            self.redirect('/images/favicon.ico')
        else:
            func_name = 'page_%s' % pagename
            logging.info('loading page: %s' % func_name)
            try:
                func = getattr(self, func_name)
            except AttributeError:
                self.response.set_status(404)
            else:
                func()

    def page_heroes(self):
        heroes = DSHero.all().order("-gold").fetch(10)
        values = {
            'heroes': heroes,
        }
        self.show_page('heroes', values)

    def page_game(self):
        values = {}
        self.show_page('game', values, 'bare')

    def show_page(self, page, template_values=None, layout='default'):
        try:
            content = self.get_template(page, template_values, layout)
            self.response.out.write(content)
        except TemplateDoesNotExist:
            self.response.set_status(404)

def main():
    application = webapp.WSGIApplication([(r'/api/(.*)', GoldQuestHandler),
                                          (r'/(.*)', MainPageHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
