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
import uuid
from datetime import datetime

#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import channel
from google.appengine.api import memcache
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

    def get_template(self, page, values, layout='default'):
        page = "%s.html" % page
        path = os.path.join(self.basepath, 'views', page)
        logging.info('template pathname: %s' % path)
        content = template.render(path, values)
        if layout:
            path = os.path.join(self.basepath, 'views', 'layouts', '%s.html' % layout)
            content = template.render(path, { 'content': content })
        return content

    def parse_pagename(self, page):
        (pagename, ext) = os.path.splitext(page)
        logging.info("page: %s pagename: %s ext: %s" % (page, pagename, ext))
        # TODO: filter unwanted characters
        return (pagename, ext)

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
        elif accept == '*/*' or httpheader.acceptable_content_type(accept, 'text/html'):
            self.output_html(page, template_values, layout)
        elif httpheader.acceptable_content_type(accept, 'application/xml'):
            self.output_xml(template_values)
        else:
            #elif httpheader.acceptable_content_type(accept, 'text/plain'):
            try:
                self.output_text(template_values['message'])
            except KeyError, e:
                self.output_text(template_values)

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
    _cfg = None
    _game = None
    _channel = None

    def __init__(self):
        self._cfg = ConfigParser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        self._cfg.read(config_path)
        self._game = GoldQuest.GoldQuest(self._cfg)
        self._channel = ChannelUpdater()

    def output_html(self, page, template_values=None, layout='default'):
        """
        Override the html output to print data.
        """
        values = {
            'command': page,
            'content': dumpdict.dumpdict(template_values, br='<br/>', html=1),
        }
        return super(GoldQuestHandler, self).output_html('api_response', values, layout)

    def get(self, command):
        response = self._game.play(command, True)
        if response and response['message']:
            logging.info(response)
            #self.response.out.write(response)
            response['id'] = uuid.uuid4().hex
            if command != 'stats':
                self._channel.send_all_update(response)
            self.show_page(command, response, 'default')
        else:
            self.response.set_status(404)

class MainPageHandler(PageHandler):
    _channel = None

    def __init__(self):
        self._channel = ChannelUpdater()

    def get(self, page):
        template_values = {}
        (pagename, ext) = self.parse_pagename(page)
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
                self.show_page(pagename, None, 'default')
                #self.response.set_status(404)
            else:
                func()

    def page_heroes(self):
        heroes = DSHero.all().order("-gold").fetch(10)
        values = {
            'heroes': heroes,
        }
        self.show_page('heroes', values)

    def page_game(self):
        (token, client_id) = self._channel.create_channel()
        values = {
            'channel_token': token,
            'channel_client_id': client_id,
        }
        self.show_page('game', values, 'bare')

class ChannelUpdater(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ChannelUpdater, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self._channels = self.get_channels()

    def get_channels(self):
        return simplejson.loads(memcache.get('channels') or '{}')

    def set_channels(self, channels):
        memcache.set('channels', simplejson.dumps(channels))

    def create_channel(self):
        client_id = uuid.uuid4().hex
        token = channel.create_channel(client_id)
        return (token, client_id)

    def send_update(self, client_id, message):
        """
        Send a message as JSON to the client identified with client_id.
        """
        message = simplejson.dumps(message)
        logging.info('Sending message to client: %s - %s' % (client_id, message))
        channel.send_message(client_id, message)

    def send_all_update(self, message):
        """
        Send message to all connected clients.
        """
        channels = self.get_channels()
        for client_id in channels.iterkeys():
            self.send_update(client_id, message)

    def connect(self, client_id):
        """
        Add client_id to list of active clients.
        TODO: Needs persistence
        """
        channels = self.get_channels()
        if not hasattr(channels, client_id):
            logging.info("Adding new client: %s" % client_id)
            channels[client_id] = str(datetime.now())
            self.set_channels(channels)

    def disconnect(self, client_id):
        """
        Remove client_id from list of active clients.
        TODO: Needs persistence
        """
        channels = self.get_channels()
        try:
            del channels[client_id]
        except KeyError, e:
            logging.info("Tried to remove unknown client: %s" % client_id)
        else:
            self.set_channels(channels)

class ChannelHandler(webapp.RequestHandler):
    _channel = None

    def __init__(self):
        self._channel = ChannelUpdater()

    def post(self, action):
        client_id = self.request.get('from')
        logging.info('Channel client %s %s' % (client_id, action))
        if action == 'connected':
            self._channel.connect(client_id)
        elif action == 'disconnected':
            self._channel.disconnect(client_id)


def main():
    application = webapp.WSGIApplication([(r'/api/(.*)', GoldQuestHandler),
                                          (r'/_ah/channel/(connected|disconnected)/', ChannelHandler),
                                          (r'/(.*)', MainPageHandler),
                                          ],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
