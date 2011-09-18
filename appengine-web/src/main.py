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
import sys
import uuid
import string
import logging
import dumpdict
import simplejson
from datetime import datetime

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from google.appengine.api import users
from gaesessions import get_current_session

from decorators import *
import broadcast
from datastorehelpers import *
from goldenweb import *
from web import *

GAME = {}

class GameHandler(PageHandler):
    default_game = 'goldquest'
    _cfg = None
    _game = None
    _channel = None

    @LogUsageCPU
    def __init__(self):
        self._session = get_current_session()

    def setup_game(self, game=None):
        # Initialize game class.
        userid = self.get_userid()
        logging.info('game: %s user: %s', game, userid)
        if game not in GAME:
            logging.info('Creating new game instance.')
            GAME[game] = GoldFrame.create_game(game, memcache=memcache.Client(), userid=userid)

            # Call game setup code.
            GAME[game].setup()
        else:
            logging.info('Using cached game instance')
            GAME[game]._userid = userid
        self._game = GAME[game]

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
        return super(GameHandler, self).output_html('api_response', values, layout)

    def parse_arguments(self, *args):
        game = self.default_game
        command = args[0]
        if len(args) == 2:
            game = args[0]
            command = args[1]
        return (game, command)

    def get_userid(self):
        """
        TODO: If userid in session has a hero, but not the logged in user, connect
        the hero with the user instead and remove the session cookie.
        """
        user = users.get_current_user()
        userid = None
        if user:
            userid = user.user_id()
        else:
            try:
                userid = self._session['userid']
            except KeyError:
                userid = uuid.uuid4().hex
                self._session['userid'] = userid

        return userid

    @LogUsageCPU
    def get(self, *args):
        # Read arguments
        (game, command) = self.parse_arguments(*args)

        logging.info('game: %s command: %s', game, command)

        # Setup the game.
        self.setup_game(game)

        # Call the action handler in the game.
        response = self._game.play(command, True)

        # Handle the game response.
        if response and response['message']:
            logging.debug(response)
            # Add some default values to all responses.
            response['id'] = uuid.uuid4().hex
            response['command'] = command

            # Gold Quest needs some extra tracking for the moment.
            # TODO: Define tracking in game metadata.
            if game == 'goldquest':
                self.track_values(response)

            # Broadcast response to all players.
            if command in self._game.metadata['broadcast_actions'] and not 'personal' in response:
                self._channel.send_all_update(response)

            # Show response.
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
        (r'/api/(.*?)/(.*)', GameHandler),
        (r'/api/(.*?)', GameHandler),
        ],
        debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
