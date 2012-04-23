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

# FIXME: Use persistent storage.
changed_items = {}
heroes = {}

class Game(GoldFrame.GamePlugin):
    _cfg = None
    room = None
    inv = None
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
        pass

    def template_charsheet(self):
        return """
        <h1 class="nameValue">Meadow Madness</h1>
        """

    def template_actionline(self):
        return "<li class='actionLine {{ cls }}' id='action_{{ id }}'>{{ line }}{{ extraInfo }}</li>"

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

    def action_stats(self, arguments):
        msg = self.get_text('charsheet')
        response = {
            'message': msg,
            'data': {
            }
        }
        return response

    def trigger_room(self, roomName, result):
        next_room = roomName
        roomdata = self.get_a_room(next_room)
        if roomdata: self.room = roomdata

    def trigger_say(self, text, result):
        result.append(text)

    def trigger_list(self, itemName, result):
        item = self.get_item(self.room, itemName)
        if item:
            result.append(item['description'])

    def trigger_show(self, itemName, result):
        item = self.get_item(self.room, itemName)
        if item:
            item['visible'] = True

    def trigger_hide(self, itemName, result):
        item = self.get_item(self.room, itemName)
        if item:
            item['visible'] = False

    def trigger_take(self, itemName, result):
        index = None
        for i in range(0, len(self.room['items'])):
            if self.room['items'][i]['key'] == itemName:
                index = i
                break

        if index != None:
            self.inv.append(self.room['items'][index])
            #self.inv[itemName] = self.room['items'][index]
            del self.room['items'][index]

    def trigger_drop(self, itemName, result):
        index = None
        for i in range(0, len(self.inv)):
            if self.inv[i]['key'] == itemName:
                index = i
                break

        if index != None:
            del self.inv[index]

    def trigger_disable(self, itemName, result):
        item = self.get_item(self.room, itemName)
        if item:
            item['actions'] = []

    def trigger_item(self, actionName, itemName):
        items = self.get_items(self.room['items'] + self.inv, ['visible'], [actionName])
        if not items: return None

        item = None
        for i in items:
            if i['key'] == itemName: item = i
        if not item: return None

        old_room = self.room

        result = []

        triggers = self.get_action(item, actionName) #item['actions'][actionName]
        for trigger in triggers:
            # FIXME: Cleaner dispatch.
            if 'room' in trigger:    self.trigger_room(trigger['room'], result) # 'room' must be the action's last trigger
            if 'say' in trigger:     self.trigger_say(trigger['say'], result)
            if 'list' in trigger:    self.trigger_list(trigger['list'], result)
            if 'show' in trigger:    self.trigger_show(trigger['show'], result)
            if 'hide' in trigger:    self.trigger_hide(trigger['hide'], result)
            if 'take' in trigger:    self.trigger_take(trigger['take'], result)
            if 'drop' in trigger:    self.trigger_drop(trigger['drop'], result)
            if 'disable' in trigger: self.trigger_disable(trigger['disable'], result)

        changed_items[self._userid][old_room['key']] = old_room['items'] # FIXME: Store properly.
        changed_items[self._userid][''] = self.inv # FIXME: Store properly.

        return "<br/>".join(result)

    def change_all_action_arguments(self):
        go_items = self.get_items(self.room['items'], ['visible'], ['go'])
        self.change_action_arguments('go', go_items, 'Go', 'Where do you want to go?')

        examine_items = self.get_items(self.room['items'] + self.inv, ['visible'], ['examine'])
        self.change_action_arguments('examine', examine_items, 'Examine', 'What do you want to examine?')

        grab_items = self.get_items(self.room['items'], ['visible'], ['grab'])
        self.change_action_arguments('grab', grab_items, 'Grab', 'What do you want to grab?')

        use_items = self.get_items(self.room['items'] + self.inv, ['visible'], ['use'])
        self.change_action_arguments('use', use_items, 'Use', 'What do you want to use?')

    def play(self, command, asdict=False, arguments=None):

        self.load()

        response = GoldFrame.GamePlugin.play(self, command, asdict, arguments)

        self.save()

        response['metadata'] = self._updated_metadata

        return self.return_response(response, asdict)

    def load(self):
        # read hero location
        roomId = heroes[self._userid] if (self._userid and self._userid in heroes) else "meadow"

        if not self._userid in changed_items: changed_items[self._userid] = {}

        # read room
        self.room = self.get_a_room(roomId)

        # read inventory
        self.inv = self.get_inventory()

    def save(self):
        if self._userid and self.room and'key' in self.room:
            heroes[self._userid] = self.room['key']

    def action_go(self, arguments):
        msg = ''
        if 'item' in arguments:
            msg = self.trigger_item('go', arguments['item'])

        self.change_all_action_arguments()

        desc = self.describe_room(self.room, True)

        if msg == None or msg == '': msg = desc
        else:
            msg = msg + '<br>' + desc

        response = {
            'message': msg,
            'data': {
            }
        }
        return response

    def action_use(self, arguments):
        msg = ''
        if 'item' in arguments:
            msg = self.trigger_item('use', arguments['item'])
            self.change_all_action_arguments()

        if msg == None or msg == '': msg = 'You attempt to use the item.'

        response = {
            'message': msg,
            'data': {
            }
        }
        return response

    def action_examine(self, arguments):
        msg = ''
        if 'item' in arguments:
            msg = self.trigger_item('examine', arguments['item'])
            self.change_all_action_arguments()

        if msg == None or msg == '': msg = 'You examine the item.'

        response = {
            'message': msg,
            'data': {
            }
        }
        return response

    def action_grab(self, arguments):
        msg = ''
        if 'item' in arguments:
            msg = self.trigger_item('grab', arguments['item'])
            self.change_all_action_arguments()

        if msg == None or msg == '': msg = 'You reach for the item.'

        #    msg = self.get_text('grabbed_item') % item
        response = {
            'message': msg,
            'data': {
            }
        }
        return response

    def describe_room(self, room, include_items):
        text = room['description']
        if include_items and 'items' in room:
            items = self.get_items(room['items'], ['visible'])
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
        if key in changed_items[self._userid]:
            room['items'] = changed_items[self._userid][key]
        if not 'items' in room: room['items'] = [ ]
        return room

    def get_inventory(self):
        if '' in changed_items[self._userid]:
            return changed_items[self._userid]['']
        return []

    def get_action(self, item, actionName):
        if not 'actions' in item:
            return None

        for action in item['actions']:
            #if not actionName in action: continue
            ok = 1
            if 'requires' in action:
                for req in action['requires']:
                    if not self.get_inv_item(req):
                        ok = 0
                        break
            if ok == 1: return action[actionName] if actionName in action else None

        return None

    def get_items(self, roomItems, filters, actions=None):
        items = None
        for filter in filters:
            items = [item for item in roomItems if item[filter]]
        if actions:
            for action in actions:
                items = [item for item in items if self.get_action(item, action)]
        return items

    def get_item(self, room, key):
        logging.info('get_item: %s', key)
        for itm in room['items']:
            if itm['key'] == key:
                return itm

    def get_inv_item(self, key):
        logging.info('get_inv_item: %s', key)
        for itm in self.inv:
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

