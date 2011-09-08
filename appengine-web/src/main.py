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

#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '1.2')

import ConfigParser
import sys
import os
import logging
import simplejson
import string
import httpheader
import uuid
from datetime import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import channel
from google.appengine.api import memcache
from google.appengine.api import quota
from django.template import TemplateDoesNotExist
from appengine_utilities.sessions import Session

from GoldQuest import GoldQuest
from GoldQuest.DataStoreDataHandler import *

import Py2XML
import dumpdict

# TODO: Move into own file.
def LogUsageCPU(func):
    def repl_func(*args):
        start = quota.get_request_cpu_usage()
        ret = func(*args)
        end = quota.get_request_cpu_usage()
        logging.debug("%s method cost %d megacycles." % (func.__name__, end - start))
        return ret
    return repl_func

# TODO: Move into own module.
class KeyValueInt(db.Model):
    """Shards for the counter"""
    name = db.StringProperty(required=True, default='')
    value = db.IntegerProperty(required=True, default=0)

@LogUsageCPU
def get_value(name):
    """Retrieve the value for a given key."""
    k = db.Key.from_path('KeyValueInt', name)
    val = db.get(k)
    #val = KeyValueInt.all().filter('name =', name).get()
    if not val:
        val = KeyValueInt(key_name=name, name=name, value=0)
    return val

@LogUsageCPU
def set_value(name, value):
    """Update the value for a given name."""
    k = db.Key.from_path('KeyValueInt', name)
    val = db.get(k)
    if not val:
        val = KeyValueInt(key_name=name, name=name, value=value)
    else:
        val.value = value
    val.put()

@LogUsageCPU
def inc_value(name, inc=1):
    """Increment the value for a given sharded counter."""
    def txn(name, inc):
        val = get_value(name)
        val.value += inc
        val.put()
    db.run_in_transaction(txn, name, inc)

# TODO: Move into own file.
class PageHandler(webapp.RequestHandler):
    """
    Default page handler, supporting html templates, layouts, output formats etc.
    """

    _basepath = os.path.dirname(__file__)

    @LogUsageCPU
    def get_template(self, page, values, layout='default'):
        page = "%s.html" % page
        path = os.path.join(self._basepath, 'views', page)
        logging.debug('template pathname: %s' % path)
        content = template.render(path, values)
        if layout:
            path = os.path.join(self._basepath, 'views', 'layouts', '%s.html' % layout)
            content = template.render(path, { 'content': content })
        return content

    def parse_pagename(self, page):
        (pagename, ext) = os.path.splitext(page)
        logging.debug("page: %s pagename: %s ext: %s" % (page, pagename, ext))
        # TODO: filter unwanted characters
        return (pagename, ext)

    @LogUsageCPU
    def show_page(self, page, template_values=None, layout='default', default_format=None):
        """
        Select output format based on Accept headers.
        """
        logging.debug(template_values)
        accept = self.request.headers['Accept']
        logging.debug('Accept content-type: %s' % accept)
        #(mime, parms, qval, accept_parms) = httpheader.parse_accept_header(accept)
        acceptparams = httpheader.parse_accept_header(accept)
        logging.debug(acceptparams)
        #logging.debug('mime: %s, parms: %s, qval: %s, accept_parms: %s' % (mime, parms, qval, accept_parms))
        format = self.request.get("format")
        if not format and default_format:
            format = default_format
        logging.debug('selected format: %s' % format)
        if format == 'html' or ((not acceptparams or not accept or accept == '*/*' or httpheader.acceptable_content_type(accept, 'text/html')) and not format):
            self.output_html(page, template_values, layout)
        elif format == 'json' or httpheader.acceptable_content_type(accept, 'application/json'):
            self.output_json(template_values)
        elif format == 'xml' or (httpheader.acceptable_content_type(accept, 'application/xml') and not format):
            self.output_xml(template_values)
        elif format == 'text' or httpheader.acceptable_content_type(accept, 'text/plain'):
            #elif httpheader.acceptable_content_type(accept, 'text/plain'):
            if isinstance(template_values, basestring):
                self.output_text(template_values)
            else:
                try:
                    self.output_text(template_values['message'])
                except KeyError, e:
                    self.output_text(str(template_values))
        else:
            logging.debug('Defaulting output to html.')
            self.output_html(page, template_values, layout)

    @LogUsageCPU
    def output_json(self, template_values=None):
        self.response.headers.add_header('Content-Type', 'application/json', charset='utf-8')
        jsondata = simplejson.dumps(template_values)
        self.response.out.write(jsondata)

    @LogUsageCPU
    def output_xml(self, template_values=None):
        self.response.headers.add_header('Content-Type', 'application/xml', charset='utf-8')
        serializer = Py2XML.Py2XML()
        values = { 'response': template_values }
        xmldata = serializer.parse(values)
        self.response.out.write(xmldata)

    @LogUsageCPU
    def output_text(self, content):
        self.response.headers.add_header('Content-Type', 'text/plain', charset='utf-8')
        self.response.out.write(content)

    @LogUsageCPU
    def output_html(self, page, template_values=None, layout='default'):
        try:
            content = self.get_template(page, template_values, layout)
            self.response.out.write(content)
        except TemplateDoesNotExist:
            self.response.set_status(404)

# TODO: Move into own file.
class GoldQuestHandler(PageHandler):
    _cfg = None
    _game = None
    _channel = None
    _basepath = os.path.dirname(__file__)

    @LogUsageCPU
    def __init__(self):
        # Read configuration.
        start2 = quota.get_request_cpu_usage()
        self._cfg = ConfigParser.ConfigParser()
        config_path = os.path.join(self._basepath, 'config.ini')
        self._cfg.read(config_path)
        end2 = quota.get_request_cpu_usage()
        logging.debug("GoldQuest config read cost %d megacycles." % (end2 - start2))

        # Initialize game class.
        start3 = quota.get_request_cpu_usage()
        self._memcache = memcache.Client()
        self._game = GoldQuest.GoldQuest(self._cfg, self._memcache)
        self._game.setup()
        end3 = quota.get_request_cpu_usage()
        logging.debug("GoldQuest instance creation cost %d megacycles." % (end3 - start3))

        # Setup channel if necessary.
        if self._game.metadata['broadcast_actions']:
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

    @LogUsageCPU
    def get(self, command):
        start = quota.get_request_cpu_usage()
        response = self._game.play(command, True)
        end = quota.get_request_cpu_usage()
        logging.debug("GoldQuest play %s cost %d megacycles." % (command, end - start))
        if response and response['message']:
            logging.debug(response)
            #self.response.out.write(response)
            response['id'] = uuid.uuid4().hex
            response['command'] = command
            self.track_values(response)
            if command in self._game.metadata['broadcast_actions']:
                self._channel.send_all_update(response)
            self.show_page(command, response, 'default')
        else:
            self.response.set_status(404)

    @LogUsageCPU
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
            if response['success']:
                try:
                    if response['data']['hero']['alive']:
                        inc_value('kills')
                except KeyError, e:
                    logging.error('Hero killed a monster, but response was broken.')
                    logging.error(e)
                    logging.error(response)
        elif command == 'reroll':
            inc_value('heroes')

# TODO: Move into own file.
# TODO: Don't setup channels if game doesn't have broadcast_actions
class MainPageHandler(PageHandler):
    _channel = None

    @LogUsageCPU
    def __init__(self):
        self._channel = ChannelUpdater()
        self._session = Session()

    @LogUsageCPU
    def create_channel(self, client_id=None):
        token = None
        try:
            token = self._session['channel_token']
            if not client_id:
                client_id = self._session['channel_client_id']
        except KeyError:
            pass
        if not token or not client_id:
            (token, client_id) = self._channel.create_channel(client_id)
            self._session['channel_token'] = token
            self._session['channel_client_id'] = client_id
        else:
            logging.debug('Channel already exists with client_id %s and token %s', client_id, token)
        values = {
            'channel_token': token,
            'channel_client_id': client_id,
        }
        return values

    @LogUsageCPU
    def get(self, page):
        template_values = {}
        (pagename, ext) = self.parse_pagename(page)
        if not pagename or pagename == 'index':
            self.show_page('index')
        else:
            func_name = 'page_%s' % pagename
            logging.debug('loading page: %s' % func_name)
            try:
                func = getattr(self, func_name)
            except AttributeError:
                self.show_page(pagename, None, 'default')
                #self.response.set_status(404)
            else:
                func()

    @LogUsageCPU
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

    @LogUsageCPU
    def page_game(self):
        values = self.create_channel()
        self.show_page('game', values, 'bare')

    @LogUsageCPU
    def page_createchannel(self):
        client_id = self.request.get('client_id')
        values = self.create_channel(client_id)
        self.show_page('createchannel', values, '')

    def page_mobile(self):
        values = self.create_channel()
        self.show_page('game', values, 'mobile')


# TODO: Move into separate channel module
class ChannelUpdater(object):
    _instance = None
    _session = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ChannelUpdater, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self._channels = self.get_channels()
        self._session = Session()

    @LogUsageCPU
    def get_channels(self):
        return simplejson.loads(memcache.get('channels') or '{}')

    def set_channels(self, channels):
        memcache.set('channels', simplejson.dumps(channels))

    def create_id(self):
        return uuid.uuid4().hex

    def create_channel(self, client_id=None):
        if not client_id:
            client_id = self.create_id()
        token = channel.create_channel(client_id)
        return (token, client_id)

    def send_update(self, client_id, message):
        """
        Send a message as JSON to the client identified with client_id.
        """
        message = simplejson.dumps(message)
        logging.debug('Sending message to client: %s - %s' % (client_id, message))
        channel.send_message(client_id, message)

    def send_all_update(self, message):
        """
        Send message to all connected clients.
        """
        channels = self.get_channels()
        for client_id in channels.iterkeys():
            if client_id != self._session['channel_client_id']:
                self.send_update(client_id, message)

    def connect(self, client_id):
        """
        Add client_id to list of active clients.
        """
        channels = self.get_channels()
        if not hasattr(channels, client_id):
            logging.debug("Adding new client: %s" % client_id)
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
            logging.debug("Tried to remove unknown client: %s" % client_id)
        else:
            self.set_channels(channels)

# TODO: Move into separate channel module
class ChannelHandler(webapp.RequestHandler):
    _channel = None

    def __init__(self):
        self._channel = ChannelUpdater()

    def post(self, action):
        client_id = self.request.get('from')
        logging.debug('Channel client %s %s' % (client_id, action))
        if action == 'connected':
            self._channel.connect(client_id)
        elif action == 'disconnected':
            self._channel.disconnect(client_id)


@LogUsageCPU
def main():
    application = webapp.WSGIApplication([
            (r'/api/(.*)', GoldQuestHandler),
            (r'/_ah/channel/(connected|disconnected)/', ChannelHandler),
            (r'/(.*)', MainPageHandler),
        ],
        debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
