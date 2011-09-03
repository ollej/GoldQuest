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
import simplejson
import string
import httpheader

#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from django.template import TemplateDoesNotExist

from GoldQuest import GoldQuest
from GoldQuest.DataStoreDataHandler import *

import Py2XML
import dumpdict

class PageHandler(webapp.RequestHandler):
    """
    Default page handler, supporting html templates, layouts, output formats etc.
    """

    basepath = os.path.dirname(__file__)

    def parse_accept(self, accept):
        logging.info('accept: %s' % accept)
        (mime, charset) = string.split(accept, '; ', 2)
        encoding = 'utf-8'
        if charset:
            (foo, encoding) = string.split(charset, '=', 2)
        return (mime, encoding)

    def get_template(self, page, values, layout='default'):
        page = "%s.html" % page
        path = os.path.join(self.basepath, 'views', page)
        logging.info('template pathname: %s' % path)
        content = template.render(path, values)
        if layout:
            path = os.path.join(self.basepath, 'views', 'layouts', '%s.html' % layout)
            content = template.render(path, { 'content': content })
        return content

    def show_page(self, page, template_values=None, layout='default'):
        """
        Select output format based on Accept headers.
        """
        accept = self.request.headers['Accept']
        logging.info('Accept content-type: %s' % accept)
        logging.info(template_values)
        #(mime, parms, qval, accept_parms) = httpheader.parse_accept_header(accept)
        acceptparams = httpheader.parse_accept_header(accept)
        logging.info(acceptparams)
        #logging.info('mime: %s, parms: %s, qval: %s, accept_parms: %s' % (mime, parms, qval, accept_parms))
        if httpheader.acceptable_content_type(accept, 'application/json'):
            self.output_json(template_values)
        elif httpheader.acceptable_content_type(accept, 'text/html'):
            self.output_html(page, template_values, layout)
        elif httpheader.acceptable_content_type(accept, 'application/xml'):
            self.output_xml(template_values)
        else:
            #elif httpheader.acceptable_content_type(accept, 'text/plain'):
            self.output_text(template_values['message'])
        return
        (mime, encoding) = self.parse_accept(accept)
        if mime == 'text/plain':
            self.output_text(template_values['response']['message'])
        elif mime == 'application/json':
            self.output_json(template_values)
        elif mime == 'application/xml':
            self.output_xml(template_values)
        else:
            self.output_html(page, template_values, layout)

    def output_json(self, template_values=None):
        self.response.headers.add_header('Content-Type', 'application/json', charset='utf-8')
        jsondata = simplejson.dumps(template_values)
        self.response.out.write(jsondata)

    def output_xml(self, template_values=None):
        self.response.headers.add_header('Content-Type', 'application/xml', charset='utf-8')
        serializer = Py2XML.Py2XML()
        values = { 'response': template_values }
        xmldata = serializer.parse(values)
        self.response.out.write(xmldata)

    def output_text(self, content):
        self.response.headers.add_header('Content-Type', 'text/plain', charset='utf-8')
        self.response.out.write(content)

    def output_html(self, page, template_values=None, layout='default'):
        try:
            content = self.get_template(page, template_values, layout)
            self.response.out.write(content)
        except TemplateDoesNotExist:
            self.response.set_status(404)

class GoldQuestHandler(PageHandler):
    def __init__(self):
        cfg = ConfigParser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        cfg.read(config_path)
        self.game = GoldQuest.GoldQuest(cfg)

    def output_html(self, page, template_values=None, layout='default'):
        """
        Override the html output to print data.
        """
        values = {
            'command': page,
            'content': dumpdict.dumpdict(template_values, br='<br/>', html=1),
        }
        return super(GoldQuestHandler, self).output_html('api', values, layout)

    def get(self, command):
        response = self.game.play(command, True)
        if response and response['message']:
            logging.info(response)
            #self.response.out.write(response)
            self.show_page(command, response, 'default')
        else:
            self.response.set_status(404)

class MainPageHandler(PageHandler):
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


def main():
    application = webapp.WSGIApplication([(r'/api/(.*)', GoldQuestHandler),
                                          (r'/(.*)', MainPageHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
