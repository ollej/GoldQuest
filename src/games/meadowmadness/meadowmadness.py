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

import random
import logging

from GoldFrame import GoldFrame
from decorators import *

class Game(GoldFrame.GamePlugin):
    _cfg = None
    hero = None
    level = None
    _datafile = 'meadowmadness.dat'
    metadata = {
        'name': 'Meadow Madness',
        'gamekey': 'meadowmadness',
        'personal_hero': True,
        'broadcast_actions': ['go', 'use', 'look'],
        'actions': [
            {
                'key': 'go',
                'name': 'Go',
                'description': 'Go to another area.',
                'img': 'images/meadowmadness/icon-go.png',
                'tinyimg': 'images/meadowmadness/tiny-icon-go.png',
                'color': '#C30017',
                'button': 'active',
            },
            {
                'key': 'use',
                'name': 'Use',
                'description': 'Use an item.',
                'img': 'images/meadowmadness/icon-use.png',
                'tinyimg': 'images/meadowmadness/tiny-icon-use.png',
                'color': '#004C7B',
                'button': 'active',
            },
            {
                'key': 'examine',
                'name': 'Examine',
                'description': 'Search current area.',
                'img': 'images/meadowmadness/icon-examine.png',
                'tinyimg': 'images/meadowmadness/tiny-icon-examine.png',
                'color': '#E9B700',
                'button': 'active',
            },
            {
                'key': 'grab',
                'name': 'Grab',
                'description': 'Grab something.',
                'img': 'images/meadowmadness/icon-grab.png',
                'tinyimg': 'images/meadowmadness/tiny-icon-grab.png',
                'color': '#E9B700',
                'button': 'active',
            },
        ],
        'stats_img': 'images/meadowmadness/icon-stats.png',
        'stats': [
            {
                'key': 'name',
                'name': 'Name',
                'description': '',
                'type': 'string',
            },
        ],
        'extra_info': {
            'look': {
                'name': 'look',
                'style': 'color: teal',
            },
        },
    }

    def setup(self):
        # Configure datahandler backend.
        #self.setup_database()

        # Read saved hero.
        self.get_hero()

    def template_charsheet(self):
        return """
        <img src="images/meadowmadness/icon-stats.png" class="statsImage" style="float: left" width="32" height="32" alt="Stats" title="Stats" />
        <h1 id="nameValue" class="nameValue">[[ name ]]</h1>
        <ul class="charsheetList">
          <li class="statItem" id="goldStatDiv"><img src="images/meadowmadness/tiny-icon-gold.png" width="16" height="16" alt="Gold" title="Gold" /><span class="statValue" id="goldValue">[[ gold ]]</span></li>
        </ul>
        """

    def template_actionline(self):
        return "<li class='actionLine [[ cls ]]' id='action_[[ id ]]'>[[ line ]][[ extraInfo ]]</li>"

    @LogUsageCPU
    def setup_database(self):
        """
        Sets up either a sqlite database or a GAE DataStore depending on configuration.
        """
        datahandler = self._cfg.get('LOCAL', 'datahandler')
        if datahandler == 'sqlite':
            from SqlDataHandler import SqlDataHandler
            self._dh = SqlDataHandler(self._debug)
        elif datahandler == 'datastore':
            from MMDSHandler import GQDSHandler
            self._dh = GQDSHandler(self._debug)
        else:
            raise GoldFrameConfigException, "Unknown datahandler: %s" % datahandler

    @LogUsageCPU
    def get_hero(self):
        self.hero = self._dh.get_alive_hero()

    def action_stats(self):
        msg = self.get_text('charsheet')
        attribs = self.hero.get_attributes()
        msg = msg % attribs
        response = {
            'message': msg,
            'data': {
                'hero': attribs,
            }
        }
        return response



