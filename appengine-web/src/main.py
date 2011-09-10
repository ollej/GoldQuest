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
import uuid
from datetime import datetime
import dumpdict

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache

from decorators import *
import broadcast
from datastorehelpers import *
from goldenweb import *
from web import *
from GoldQuest import GoldQuest
from GoldQuest.DataStoreDataHandler import *

# TODO: Move into own file.
class GameHandler(PageHandler):
    _cfg = None
    _game = None
    _channel = None
    _basepath = os.path.dirname(__file__)

    @LogUsageCPU
    def __init__(self):
        # Read configuration.
        self._cfg = ConfigParser.ConfigParser()
        config_path = os.path.join(self._basepath, 'config.ini')
        self._cfg.read(config_path)

        # Initialize game class.
        self._memcache = memcache.Client()
        self._game = GoldQuest.GoldQuest(self._cfg, self._memcache)
        self._game.setup()

        # Setup channel if necessary.
        if self._game.metadata['broadcast_actions']:
            self._channel = broadcast.ChannelUpdater()

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
        response = self._game.play(command, True)
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
        """
        Tracks some extra values for GoldQuest.
        TODO: Should be handled by GoldQuest class.
        """
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
        elif command == 'reroll' and response['success']:
            inc_value('heroes')


@LogUsageCPU
def main():
    application = webapp.WSGIApplication([
            (r'/api/(.*)', GameHandler),
        ],
        debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
