#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The MIT License

Copyright (c) 2011 Mikael Holmström

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

import time
import random

from GoldFrame import GoldFrame

class Goat:
    name   = 'Powerhead Nancy Scuttles'
    clicks = 0
    time   = 0

    def __init__(self):
        self.name = self.gen_name()

    def gen_name(self):
        first = [
            'Powerhead',
            'Fluffy',
            'Mushy',
            'Mittens',
            'Lucy',
            'Jake',
            'Josh',
            'Rainbow',
            'Bubbles',
            'Dakota',
            'Mr',
            'Ms',
            'Mrs',
        ]

        middle = [
            'Nancy',
            'Lando',
            'Loop',
            'Rosalinda',
            'Arnold',
        ]

        last = [
            'Scuttles',
            'Wise',
            'Long',
            'Droop-ear',
            'Jackson',
            'Cooper',
            'Tail-wind',
        ]

        return '%s %s %s' % (random.choice(first), random.choice(middle), random.choice(last))


class Game(GoldFrame.GamePlugin):
    _cfg = None
    goat = None
    metadata = {
        'name': 'GoatClicker',
        'gamekey': 'goatclicker',
        'personal_hero': True,
        'broadcast_actions': [ 'click' ],
        'actions': [
            {
                'key': 'click',
                'name': 'Click goat',
                'description': 'Click goat',
                'img': 'images/goatclicker/icon-goat.png',
                'tinyimg': 'images/goatclicker/icon-goat.png',
                'color': '#C30017',
            },
            {
                'key': 'stats',
                'name': 'Goat stats',
                'description': 'Goat stats',
            },
            {
                'key': 'highscores',
                'name': 'Happy goats',
                'description': 'Happy goats',
            },
        ],
        'stats_img': 'images/goatclicker/icon-goatclicker.png',
        'stats': [
            {
                'key': 'name',
                'name': 'Name',
                'description': '',
                'type': 'string',
            },
            {
                'key': 'clicks',
                'name': 'Goat Clicks',
                'description': '',
                'type': 'integer',
            },
        ],
    }

    def setup(self):
        import DAO
        self._dh = DAO.DAO(self._debug)
        self.load()

        #self._dh.clear()

    def template_charsheet(self):
        return """
        <h1 id="nameValue" class="nameValue">{{ name }}</h1>
        <ul class="charsheetList">
          <li class="clicksItem" id="clicksStatDiv"><img src="images/tiny-icon-clicks.png" width="16" height="16" alt="Clicks" title="Goat clicks" /><span class="statValue" id="clicksValue">{{ clicks }}</span></li>
        </ul>
        """

    def template_actionline(self):
        return "<li class='actionLine {{ cls }}' id='action_{{ id }}'>{{ line }}{{ extraInfo }}</li>"

    def play(self, command, asdict=False, arguments=None):

        self.load()

        response = ''

        if command == 'click':
            response = self.click()
        elif command == 'stats':
            response = self.stats()
        elif command == 'highscores':
            return self.return_response(self.highscores(), asdict)
        else:
            return None

        self.save()

        response['data']['hero'] = {
            'name'  : self.goat.name,
            'clicks': self.goat.clicks,
        }

        return self.return_response(response, asdict)

    def load(self):
        if self._userid: self.goat = self._dh.load_goat(self._userid, Goat())

    def save(self):
        self._dh.save_goat(self._userid, self.goat)

    def highscores(self):
        hs = self._dh.get_highscores(10)
        response = {
            'message': 'Highscores',
            'data': {
                'highscores': hs,
            }
        }
        return response

    def stats(self):
        response = {
            'message': '',
            'data': {
            }
        }
        return response

    def click(self):
        msg = ''
        data =  { }
        success = 0

        min_time = self.goat.clicks + 1

        cur_time = time.time()
        time_diff = cur_time - self.goat.time

        if time_diff < min_time:
            msg = '%s is tired. Try again in %i seconds.' % (self.goat.name, int(min_time - time_diff)+1)
        else:
            self.goat.clicks += 1
            self.goat.time = cur_time
            msg = '%s is a lucky goat to have been clicked %i times.' % (self.goat.name, self.goat.clicks)
            data['Clicks'] = 1
            success = 1

        response = {
            'message': msg,
            'data': data
        }

        if not success:
            response['personal'] = 1

        return response
