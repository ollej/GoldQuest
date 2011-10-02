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
from datastorehelpers import *

class Game(GoldFrame.GamePlugin):
    predictions = 0
    _cfg = None
    metadata = {
        'name': 'Magic 8-ball',
        'gamekey': '8ball',
        'personal_hero': False,
        'broadcast_actions': [],
        'actions': [
            {
                'key': 'ask',
                'name': 'Ask',
                'description': 'Ask the magic 8-ball',
                'img': 'images/icon-8ball.png',
                'tinyimg': 'images/icon-8ball.png',
                'color': '#C30017',
            },
        ],
        'stats_img': 'images/icon-8ball.png',
        'stats': [
            {
                'key': 'predictions',
                'name': 'Predictions',
                'description': 'The number of predictions the magic 8-ball has done.',
                'type': 'integer',
            },
        ],
    }

    def template_charsheet(self):
        return """
        <h1 style="padding-top: 6px">Predictions: <span id="predictionsValue" class="predictionsValue">[[ predictions ]]</span></h1>
        """

    def template_actionline(self):
        return "<li class='actionLine [[ cls ]]' id='action_[[ id ]]'>[[ line ]][[ extraInfo ]]</li>"

    def setup(self):
        self.predictions = get_value('8ball_predictions')

    #def play(self, command, asdict=False, arguments=None):
    def action_stats(self, arguments=None):
        """
        Returns stats
        """
        response = {
            'message': 'Statistics',
            'data': { 'hero': { 'predictions': self.predictions } },
        }
        return response

    def action_ask(self, arguments=None):
        """
        Make a prediction.
        """
        # Handle action command.
        inc_value('8ball_predictions')
        msg = random.choice([
            "As I see it, yes",
            "It is certain",
            "It is decidedly so",
            "Most likely",
            "Outlook good",
            "Signs point to yes",
            "Without a doubt",
            "Yes",
            "Yes – definitely",
            "You may rely on it",
            "Reply hazy, try again",
            "Ask again later",
            "Better not tell you now",
            "Cannot predict now",
            "Concentrate and ask again",
            "Don't count on it",
            "My reply is no",
            "My sources say no",
            "Outlook not so good",
            "Very doubtful",
        ])
        response = {
            'message': msg,
            'data': { 'hero': { 'predictions': self.predictions + 1 } },
        }

        return response

