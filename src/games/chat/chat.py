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
    users = 0
    _cfg = None
    metadata = {
        'name': 'Chat',
        'gamekey': 'chat',
        'personal_hero': False,
        'broadcast_actions': ['chat'],
        'actions': [
            {
                'key': 'chat',
                'name': 'Chat',
                'description': 'Send a chat message.',
                'img': 'images/chat/icon-chat.png',
                'tinyimg': 'images/chat/icon-chat.png',
                'color': '#C30017',
                'arguments': [
                    {
                        'type': 'input',
                        'key': 'chatmessage',
                        'name': 'Chat Message',
                        'description': 'Enter a message to send out to all visitors.',
                    },
                ],
            },
        ],
        'stats_img': 'images/chat/icon-chat.png',
        'stats': [
            {
                'key': 'users',
                'name': 'users',
                'description': 'The number of recent users in the chat.',
                'type': 'integer',
            },
        ],
    }

    def template_charsheet(self):
        return """
        <h1 style="padding-top: 6px">Online Users: <span id="usersValue" class="usersValue">{{ users }}</span></h1>
        """

    def action_chat(self, arguments=None):
        """
        Make a prediction.
        """
        return "<%s> %s" % (self._userid, arguments['chatmessage'])

