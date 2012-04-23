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
    apps = 0
    _cfg = None
    metadata = {
        'name': 'Gold Apps',
        'gamekey': 'goldapps',
        'personal_hero': False,
        'broadcast_actions': [],
        'actions': [
        ],
        'stats_img': 'images/icon-goldapps.png',
        'stats': [
            {
                'key': 'apps',
                'name': 'Apps',
                'description': 'The total number of available apps.',
                'type': 'integer',
            },
        ],
        'templates': {
            'appicon': """
    <div class="appIconDiv">
        <a href="#" title="[[ gameKey ]]">
            <img src="images/[[ gameKey ]]/icon-[[ gameKey ]].png" class="appIcon" alt="[[ gameKey ]]" title="[[ gameKey ]]" /><br />
            <p class="appIconText">[[ gameName ]]</p>
        </a>
    </div>
            """
        }
    }

    def template_charsheet(self):
        return """
        <h1 style="padding-top: 6px">Total Apps: <span id="appsValue" class="appsValue">[[ apps ]]</span></h1>
        """

