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
from google.appengine.api import quota
from django.template import TemplateDoesNotExist

from GoldQuest import GoldQuest
from GoldQuest.DataStoreDataHandler import *

import Py2XML
import dumpdict

class KeyValueInt(db.Model):
    """Shards for the counter"""
    name = db.StringProperty(required=True, default='')
    value = db.IntegerProperty(required=True, default=0)

def get_value(name):
    """Retrieve the value for a given key."""
    k = db.Key.from_path('KeyValueInt', name)
    val = db.get(k)
    #val = KeyValueInt.all().filter('name =', name).get()
    if not val:
        val = KeyValueInt(key_name=name, name=name, value=0)
    return val

def set_value(name, value):
    """Update the value for a given name."""
    k = db.Key.from_path('KeyValueInt', name)
    val = db.get(k)
    if not val:
        val = KeyValueInt(key_name=name, name=name, value=value)
    else:
        val.value = value
    val.put()

def inc_value(name, inc=1):
    """Increment the value for a given sharded counter."""
    def txn(name, inc):
        val = get_value(name)
        val.value += inc
        val.put()
    db.run_in_transaction(txn, name, inc)

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
        logging.info(template_values)
        accept = self.request.headers['Accept']
        logging.info('Accept content-type: %s' % accept)
        #(mime, parms, qval, accept_parms) = httpheader.parse_accept_header(accept)
        acceptparams = httpheader.parse_accept_header(accept)
        logging.info(acceptparams)
        #logging.info('mime: %s, parms: %s, qval: %s, accept_parms: %s' % (mime, parms, qval, accept_parms))
        format = self.request.get("format")
        logging.info('selected format: %s' % format)
        if (format and format == 'json') or httpheader.acceptable_content_type(accept, 'application/json'):
            self.output_json(template_values)
        elif (not acceptparams or not accept or accept == '*/*' or httpheader.acceptable_content_type(accept, 'text/html')) and not format:
            self.output_html(page, template_values, layout)
        elif (format and format == 'xml') or (httpheader.acceptable_content_type(accept, 'application/xml') and not format):
            self.output_xml(template_values)
        elif template_values or format == 'text':
            #elif httpheader.acceptable_content_type(accept, 'text/plain'):
                if isinstance(template_values, basestring):
                    self.output_text(template_values)
                else:
                    try:
                        self.output_text(template_values['message'])
                    except KeyError, e:
                        self.output_text(str(template_values))
        else:
            logging.info('Defaulting output to html.')
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
    _cfg = None
    _game = None
    _channel = None

    def __init__(self):
        start = quota.get_request_cpu_usage()
        self._cfg = ConfigParser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        self._cfg.read(config_path)
        self._game = GoldQuest.GoldQuest(self._cfg)
        self._channel = ChannelUpdater()
        end = quota.get_request_cpu_usage()
        logging.info("GoldQuest init cost %d megacycles." % (end - start))

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
        start = quota.get_request_cpu_usage()
        response = self._game.play(command, True)
        end = quota.get_request_cpu_usage()
        logging.info("GoldQuest play %s cost %d megacycles." % (command, end - start))
        if response and response['message']:
            logging.info(response)
            #self.response.out.write(response)
            response['id'] = uuid.uuid4().hex
            response['command'] = command
            start = quota.get_request_cpu_usage()
            self.track_values(response)
            end = quota.get_request_cpu_usage()
            logging.info("GoldQuest track values cost %d megacycles." % (end - start))
            if command != 'stats':
                self._channel.send_all_update(response)
            start = quota.get_request_cpu_usage()
            self.show_page(command, response, 'default')
            end = quota.get_request_cpu_usage()
            logging.info("GoldQuest show page cost %d megacycles." % (end - start))
        else:
            self.response.set_status(404)

    def track_values(self, response):
        command = response['command']
        if command == 'loot':
            try:
                loot = response['data']['loot']
            except KeyError, e:
                pass
            else:
                inc_value('gold', loot)
        elif command == 'fight':
            try:
                if response['data']['hero']['alive']:
                    inc_value('kills')
            except KeyError, e:
                logging.info('Hero killed a monster, but response was broken.')
                logging.info(e)
                logging.info(response)
        elif command == 'reroll':
            inc_value('heroes')

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
        gold = get_value('gold').value
        kills = get_value('kills').value
        hero_count = get_value('heroes').value
        level = 0
        high_level_hero = DSHero.all().order("-level").get()
        if high_level_hero:
            level = high_level_hero.level
        values = {
            'heroes': heroes,
            'gold': gold,
            'kills': kills,
            'level': level,
            'hero_count': hero_count,
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
        """
        channels = self.get_channels()
        if not hasattr(channels, client_id):
            logging.info("Adding new client: %s" % client_id)
            channels[client_id] = str(datetime.now())
            self.set_channels(channels)

    def disconnect(self, client_id):
        """
        Remove client_id from list of active clients.
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
