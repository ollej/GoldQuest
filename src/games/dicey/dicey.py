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

from GoldFrame import GoldFrame
import Dice
from datastorehelpers import *

class Game(GoldFrame.GamePlugin):
    rolls = 0
    _cfg = None
    metadata = {
        'name': 'Dicey',
        'gamekey': 'dicey',
        'personal_hero': False,
        'broadcast_actions': [],
        'actions': [
            {
                'key': 'd6',
                'name': 'D6',
                'description': 'Roll a D6',
                'img': 'images/dicey/icon-d6.gif',
                'tinyimg': 'images/dicey/icon-d6.gif',
                'color': '#C30017',
            },
            {
                'key': 'd10',
                'name': 'D10',
                'description': 'Roll a D10',
                'img': 'images/dicey/icon-d10.gif',
                'tinyimg': 'images/dicey/icon-d10.gif',
                'color': '#C30017',
            },
            {
                'key': 'd12',
                'name': 'D12',
                'description': 'Roll a D12',
                'img': 'images/dicey/icon-d12.gif',
                'tinyimg': 'images/dicey/icon-d12.gif',
                'color': '#C30017',
            },
            {
                'key': 'd20',
                'name': 'D20',
                'description': 'Roll a D20',
                'img': 'images/dicey/icon-d20.gif',
                'tinyimg': 'images/dicey/icon-d20.gif',
                'color': '#C30017',
            },
            {
                'key': 'd100',
                'name': 'D100',
                'description': 'Roll a D100',
                'img': 'images/dicey/icon-d100.gif',
                'tinyimg': 'images/dicey/icon-d100.gif',
                'color': '#C30017',
            },
            {
                'key': 'stats',
                'name': 'Stats',
                'description': 'Show statistics',
                'button': 'hidden',
            },
        ],
        'stats_img': 'images/dicey/icon-dicey.png',
        'stats': [
            {
                'key': 'rolls',
                'name': 'Dice Rolls',
                'description': '',
                'type': 'integer',
            },
        ],
    }

    def template_charsheet(self):
        return """
        <h1 style="padding-top: 6px">Rolls: <span id="rollsValue" class="rollsValue">{{ rolls }}</span></h1>
        """

    def template_actionline(self):
        return "<li class='actionLine {{ cls }}' id='action_{{ id }}'>{{ line }}{{ extraInfo }}</li>"

    def setup(self):
        self.rolls = get_value('dicey_rolls')

    def play(self, command, asdict=False, arguments=None):
        """
        Roll the given die.
        """
        # Handle action command.
        response = None
        if command == 'stats':
            rolls = self.rolls
            if not rolls:
                rolls = get_value('dicey_rolls')
                self.rolls = rolls
            response = {
                'message': 'Statistics',
                'data': { 'hero': { 'rolls': rolls } },
            }
        else:
            # Roll the selected die.
            sides = int(command[1:])
            die = Dice.Die(sides)
            roll = die.roll(sides)
            msg = "The result of the %s roll was: %d" % (command, roll)

            # Update count of dice rolls.
            inc_value('dicey_rolls')
            self.rolls += 1

            response = {
                'message': msg,
                'data': {
                    'roll': roll,
                    'hero': { 'rolls': self.rolls },
                },
            }

        return self.return_response(response, asdict)

