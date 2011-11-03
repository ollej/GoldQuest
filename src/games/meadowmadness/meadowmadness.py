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

changed_items = {}

class Game(GoldFrame.GamePlugin):
    _cfg = None
    hero = None
    room = None
    _datafile = 'meadowmadness.dat'
    metadata = {
        'name': 'Meadow Madness',
        'gamekey': 'meadowmadness',
        'personal_hero': True,
        'broadcast_actions': [],
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
                'description': 'Examine an item',
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
        ],
        'extra_info': {
        },
    }

    def setup(self):
        # Configure datahandler backend.
        #self.setup_database()

        # read room
        self.room = self.get_a_room("meadow")

        # Read saved hero.
        self.get_hero()

    def template_charsheet(self):
        return """
        <h1 class="nameValue">Meadow Madness</h1>
        """

    def template_actionline(self):
        return "<li class='actionLine [[ cls ]]' id='action_[[ id ]]'>[[ line ]][[ extraInfo ]]</li>"

    @LogUsageCPU
    def setup_database(self):
        """
        Sets up either a sqlite database or a GAE DataStore depending on configuration.
        """
        if self._cfg:
            datahandler = self._cfg.get('LOCAL', 'datahandler')
        else:
            datahandler = 'datastore'
        if datahandler == 'sqlite':
            from SqlDataHandler import SqlDataHandler
            self._dh = SqlDataHandler(self._debug)
        elif datahandler == 'datastore':
            from MMDSHandler import MMDSHandler
            self._dh = MMDSHandler(self._debug)
        else:
            raise GoldFrameConfigException, "Unknown datahandler: %s" % datahandler

    @LogUsageCPU
    def get_hero(self):
        self.hero = self._dh.get_alive_hero()

    def action_stats(self, arguments):
        msg = self.get_text('charsheet')
        response = {
            'message': msg,
            'data': {
            }
        }
        return response

    def trigger_room(self, roomName):
        next_room = roomName
        roomdata = self.get_a_room(next_room)
        if roomdata: self.room = roomdata

    def trigger_say(self, text):
        pass

    def trigger_show(self, itemName):
        item = self.get_item(self.room, itemName)
        if item:
            item['visible'] = True

    def trigger_hide(self, itemName):
        item = self.get_item(self.room, itemName)
        if item:
            item['visible'] = False

    def trigger_take(self, itemName):
        pass

    def trigger_disable(self, itemName):
        item = self.get_item(self.room, itemName)
        if item:
            item['actions'] = []

    def trigger_item(self, actionName, itemName):
        items = self.get_items(self.room, ['visible'], [actionName])
        if not items: return None

        item = next((item for item in items if item['key'] == itemName), None)
        if not item: return None

        old_room = self.room

        result = []

        triggers = item['actions'][actionName]
        for trigger in triggers:
            # FIXME: Cleaner dispatch.
            if 'room' in trigger:    result.append(self.trigger_room(trigger['room'])) # 'room' must be the action's last trigger
            if 'say' in trigger:     result.append(self.trigger_say(trigger['say']))
            if 'show' in trigger:    result.append(self.trigger_show(trigger['show']))
            if 'hide' in trigger:    result.append(self.trigger_hide(trigger['hide']))
            if 'take' in trigger:    result.append(self.trigger_take(trigger['take']))
            if 'disable' in trigger: result.append(self.trigger_disable(trigger['disable']))

        changed_items[old_room['key']] = old_room['items'] # FIXME: Store properly.

        return result

    def change_all_action_arguments(self):
        go_items = self.get_items(self.room, ['visible'], ['go'])
        self.change_action_arguments('go', go_items, 'Go', 'Where do you want to go?')

        examine_items = self.get_items(self.room, ['visible'], ['examine'])
        self.change_action_arguments('examine', examine_items, 'Examine', 'What do you want to examine?')

        grab_items = self.get_items(self.room, ['visible'], ['grab'])
        self.change_action_arguments('grab', grab_items, 'Grab', 'What do you want to grab?')

        grab_items = self.get_items(self.room, ['visible'], ['use'])
        self.change_action_arguments('use', grab_items, 'Use', 'What do you want to use?')

    def action_go(self, arguments):
        if 'item' in arguments:
            self.trigger_item('go', arguments['item'])

        self.change_all_action_arguments()

        msg = self.describe_room(self.room, True)

        response = {
            'message': msg,
            'metadata': self._updated_metadata,
            'data': {
            }
        }
        return response

    def action_use(self, arguments):
        if 'item' in arguments:
            self.trigger_item('use', arguments['item'])
            self.change_all_action_arguments()

        response = {
            'message': 'used', #item['description'],
            'metadata': self._updated_metadata,
            'data': {
            }
        }
        return response

    def action_examine(self, arguments):
        logging.info('action examine')
        logging.info(arguments)

        if 'item' in arguments:
            self.trigger_item('examine', arguments['item'])
            self.change_all_action_arguments()

        response = {
            'message': 'examined', #item['description'],
            'metadata': self._updated_metadata,
            'data': {
            }
        }
        return response

    def action_grab(self, arguments):
        if 'item' in arguments:
            self.trigger_item('grab', arguments['item'])
            self.change_all_action_arguments()

        #    msg = self.get_text('grabbed_item') % item
        response = {
            'message': 'grabbed',#msg,
            'metadata': self._updated_metadata,
            'data': {
            }
        }
        return response

    def describe_room(self, room, include_items):
        text = room['description']
        if include_items and 'items' in room:
            items = self.get_items(room, ['visible'])
            if items:
                text += " You see:<br/>"
                text += "<br/>".join(item['name'] for item in items)
        return text

    def get_a_room(self, key):
        logging.info('get_a_room: %s', key)
        room = self._gamedata['rooms'][key]
        room['key'] = key
        # items = self._dh.get_items(room)
        # if items: room['items'] = items
        if key in changed_items:
            room['items'] = changed_items[key]
        return room

    def get_items(self, room, filters, actions=None):
        items = None
        if 'items' in room:
            for filter in filters:
                items = [item for item in room['items'] if item[filter]]
            if actions:
                for trigger in actions:
                    items = [item for item in items if trigger in item['actions']]
        return items

    def get_item(self, room, key):
        logging.info('get_item: %s', key)
        for itm in room['items']:
            if itm['key'] == key:
                return itm

    def change_action_arguments(self, action, items, title, desc):
        if items:
            self.change_action(action, 'arguments', [ {
                'type': 'list',
                'key': 'item',
                'name': title,
                'description': desc,
                'items': items
                }, ]);
            self.change_action(action, 'button', 'active')
        else:
            self.change_action(action, 'arguments', [])
            self.change_action(action, 'button', 'disabled')

