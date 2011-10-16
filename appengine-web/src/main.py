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

import setup_django_version

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
            #GAME[game].setup()
        else:
            logging.info('Using cached game instance')
            GAME[game]._userid = userid

        self._game = GAME[game]
        self._game.setup()

        # Setup channel if necessary.
        if self._game.metadata['broadcast_actions']:
            self._channel = broadcast.ChannelUpdater()

        return self._game

    def output_html(self, page, template_values=None, layout='default', basepath=None):
        """
        Override the html output to print data.
        """
        values = {
            'command': page,
            'content': dumpdict.dumpdict(template_values, br='<br/>', html=1),
        }
        return super(GameHandler, self).output_html('api_response', values, layout)

    def get_arguments(self):
        args = self.request.arguments()
        arguments = {}
        for arg in args:
            if arg != u'format':
                arguments[arg] = self.request.get(arg)
        return arguments

    def parse_command(self, *args):
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

    def get(self, *args):
        # Read arguments
        (gamekey, command) = self.parse_command(*args)

        # Setup the game.
        game = self.setup_game(gamekey)

        if command == 'metadata':
            response = game.get_metadata()
            self.show_page(command, response, 'default')
        elif command == 'applist':
            self.show_apps()
        else:
            self.play(game, command)

    def show_apps(self):
        #gamepath = os.path.join(basepath, 'games', game)
        games = GoldFrame.get_games()
        response = { 'games': games }
        self.show_page('applist', response, layout='default')

    def play(self, game, command):
        logging.info('game: %s command: %s', game, command)

        # Call the action handler in the game.
        arguments = self.get_arguments()
        response = game.play(command, True, arguments=arguments)

        # Handle the game response.
        if response and response['message']:
            logging.debug(response)
            # Add some default values to all responses.
            response['id'] = uuid.uuid4().hex
            response['command'] = command

            metadata = game.get_metadata()

            # Gold Quest needs some extra tracking for the moment.
            # TODO: Define tracking in game metadata.
            if metadata['gamekey'] == 'goldquest':
                self.track_values(response)

            # Broadcast response to all players.
            if command in metadata['broadcast_actions'] and not 'personal' in response:
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
