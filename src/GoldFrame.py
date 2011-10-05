#!/usr/bin/python
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

import os
import sys
import yaml
import random
import logging
import ConfigParser

class GoldFrameException(Exception):
    pass

class GoldFrameConfigException(GoldFrameException):
    pass

class GamePlugin(object):
    _memcache = None
    _datafile = None
    _gamedata = None
    _basepath = None
    _userid = None
    _updated_metadata = None
    metadata = {
        'name': 'Game Plugin',
        'gamekey': 'gameplugin',
        'personal_hero': True,
        'broadcast_actions': None,
        'actions': {
        },
        'stats': {
        }
    }

    def __init__(self, cfg, memcache=None, userid=None, basepath=None):
        """
        Send in a ConfigParser object.
        If self._datafile is set, the contents of that file in the extras/ dir will be read, parsed as YAML and saved in self._gamedata
        """
        self._updated_metadata = self.metadata
        self._cfg = cfg
        try:
            self._debug = self._cfg.getboolan('LOCAL', 'debug')
        except AttributeError:
            self._debug = False

        if memcache:
            self._memcache = memcache

        if userid:
            self._userid = userid

        if basepath:
            self._basepath = basepath
        else:
            path = os.path.abspath(__file__)
            self._basepath = os.path.dirname(path)
        logging.info('path: %s', self._basepath)
        if self._datafile:
            self._datafile = os.path.join(self._basepath, self._datafile)
            logging.info('Datafile: %s', self._datafile)
            self._gamedata = self.read_texts(self._datafile)
            #logging.info(self._gamedata)

        if hasattr(self, 'setup_database'):
            self.setup_database()

    def setup(self):
        """
        Override this method in subclass for any additional setup that is needed.
        """
        pass

    def play(self, command, asdict=False, arguments=None):
        """
        Override this method in the game sub-class to handle actions.
        Default functionality is to call methods named "action_<command>" and return the response.

        command = String, name of the action to handle.
        asdict = Boolean, if True return a response dict with data, otherwise a string describing the result of the action.
        arguments = dict with action arguments
        """
        # Handle action command.
        try:
            func = getattr(self, 'action_%s' % command)
        except AttributeError:
            return None
        else:
            response = func(arguments)

        return self.return_response(response, asdict)

    def template_charsheet(self):
        """
        Override this method and return the html to use for the character sheet in the web client.
        Surround field names with "[[ ]]" to output the value of that field.
        """
        #path = os.path.join(os.path.dirname(__file__), 'extras', 'goldquest_template_charsheet.html')
        #return file(path,'r').read()
        return """
        [[ name ]]
        """

    def template_actionline(self):
        """
        Override this method and return the html to use for the action lines in the web client.
        Surround field names with "[[ ]]" to output the value of that field.
        """
        return "<li class='actionLine [[ cls ]]' id='action_[[ id ]]'>[[ line ]][[ extraInfo ]]</li>"
    
    def template_actionbutton(self):
        """
        Override this method and return the html to use to display an action button.
        """
        return """
    <div id="[[ key ]]Div" class="taskDiv [[ button ]]State"><button id="[[ key ]]Btn" name="[[ key ]]" class="commandBtn" style="background: url([[ img ]]) no-repeat center center"><a href="#[[ key ]]Task" class="taskHover"><img src="/images/icon-hover.png" width="32" height="32" alt="[[ name ]]" title="[[ description ]]" style="visibility: hidden" /></a></button></div>
        """

    def get_metadata(self):
        """
        Returns the game metadata.
        TODO: Should keep track of metadata changes.
        """
        return self._updated_metadata

    def roll(self, sides, times=1):
        """
        Roll times dice with sides number of sides.
        Returns the total amount rolled for all dice.
        """
        total = 0
        for i in range(times):
            total = total + random.randint(1, sides)
        return total

    def get_text(self, text):
        """
        Returns the text from 'texts' section in datafile if it is a string.
        If the value is an array, randomize between the elements in the array.
        """
        texts = self._gamedata['texts'][text]
        if not texts:
            return None
        elif isinstance(texts, basestring):
            return texts
        else:
            return random.choice(texts)

    def firstupper(self, text):
        """
        Return text with first letter in upper case.
        """
        first = text[0].upper()
        return first + text[1:]

    def read_texts(self, file):
        """
        Reads and parses file and returns it.
        Saves the data in memcache and uses it if the file hasn't been changed.
        """
        # If memcache isn't available, just load the file immediately.
        if not self._memcache:
            return self.load_file(file)

        # Read data from memcache, unless it has changed.
        texts = self._memcache.get('gamedata', namespace=self.metadata['gamekey'])
        texts_mtime = self._memcache.get('gamedata_mtime', namespace=self.metadata['gamekey'])
        mtime = os.stat(file).st_mtime
        #logging.info('Data file mtime: %s, data_mtime: %s', mtime, texts_mtime)
        if not texts or not texts_mtime or mtime > texts_mtime:
            #logging.info('Updating data file.')
            texts = self.load_file(file)
            self._memcache.set('goldquest_data', texts)
            self._memcache.set('goldquest_data_mtime', mtime)
        return texts

    def load_file(self, file):
        """
        Loads file and parses it as YAML and returns the result.
        """
        f = open(file)
        texts = yaml.load(f)
        f.close()
        return texts

    def change_action(self, action_name, key, value):
        for action in self._updated_metadata['actions']:
            if action['key'] == action_name:
                action[key] = value
                break
        return action

    def change_actions(self, change_buttons):
        actionlist = []
        for method, actions in change_buttons.iteritems():
            for action in actions:
                md = self.change_action(action, 'button', method)
                actionlist.append(md)
        return actionlist

    def return_response(self, response, asdict=False, change_buttons=None):
        if asdict:
            if isinstance(response, basestring):
                response = { 'message': response }
            if not 'success' in response:
                response['success'] = 1
            if change_buttons:
                actions = self.change_actions(change_buttons)
                if actions:
                    try:
                        response['metadata']['actions'] = actions
                    except KeyError:
                        response['metadata'] = { 'actions': actions }
            return response
        else:
            if isinstance(response, basestring):
                return response
            else:
                return response['message']

basepath = os.path.dirname(os.path.abspath(__file__))

def load_game(game, memcache, userid):
    gamepath = os.path.join(basepath, 'games', game)
    sys.path.append(gamepath)

    # Load game config
    cfg = ConfigParser.ConfigParser()
    config_path = os.path.join(gamepath, 'config.ini')
    cfg.read(config_path)

    # Load game module
    gamemodule = __import__(game)
    gamemodule.__file__ = os.path.join(gamepath, '%s.py' % game)
    globals()[game] = gamemodule

    # Create game
    logging.info('gamepath: %s', gamepath)
    return gamemodule.Game(cfg, memcache, userid, gamepath)

def get_games():
    games = []
    gamedir = os.path.join(basepath, 'games')
    for filename in os.listdir(gamedir):
        if filename.find('.') == -1:
            games.append(filename)
    return games


# TODO: Make this dynamic.
def create_game(game, memcache=None, userid=None):
    # Find all games
    games = get_games()

    if game in games:
        return load_game(game, memcache, userid)
    else:
        logging.error('Game not available: %s', game)
        raise GoldFrameException("Game not available: %s" % game)


