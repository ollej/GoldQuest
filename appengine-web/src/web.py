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

#import setup_django_version

import os
import logging

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from gaesessions import get_current_session

from decorators import *
import broadcast
from datastorehelpers import *
from goldenweb import *
#import GoldFrame
from GoldFrame import GoldFrame

class WebHandler(PageHandler):
    _channel = None

    @LogUsageCPU
    def __init__(self):
        self._channel = broadcast.ChannelUpdater()
        self._session = get_current_session()

    @LogUsageCPU
    def create_channel(self, client_id=None):
        token = None
        if self._session.has_key('channel_token'):
            token = self._session['channel_token']
        if not client_id and self._session.has_key('channel_client_id'):
            client_id = self._session['channel_client_id']
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
    def show_page_game(self, layout):
        # Create game instance.
        gamekey = self.request.get("game")
        if not gamekey:
            gamekey = 'goldquest'

        game = GoldFrame.create_game(gamekey, memcache.Client())

        values = {
            'gamekey': gamekey,
            'template_charsheet': game.template_charsheet(),
            'template_actionline': game.template_actionline(),
            'actions': game.metadata['actions'],
        }

        # Setup channel if game uses broadcast.
        if game.metadata['broadcast_actions']:
            channel_values = self.create_channel()
            values.update(channel_values)

        # Output page.
        self.show_page('game', values, layout)

    @LogUsageCPU
    def page_game(self):
        self.show_page_game('bare')

    @LogUsageCPU
    def page_mobile(self):
        self.show_page_game('mobile')

    @LogUsageCPU
    def page_createchannel(self):
        client_id = self.request.get('client_id')
        values = self.create_channel(client_id)
        self.show_page('createchannel', values, '')

def main():
    #(r'/game/goldquest/(.*)', goldquest.main.GameWebHandler),
    application = webapp.WSGIApplication([
            (r'/_ah/channel/(connected|disconnected)/', broadcast.ChannelHandler),
            (r'/(.*)', WebHandler),
        ],
        debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
