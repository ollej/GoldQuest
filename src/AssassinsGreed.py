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
import yaml
import os
import logging

import GoldFrame

from decorators import *

from Assassin import Assassin
from Target import Target

class AssassinsGreed(GoldFrame.GamePlugin):
    _gamedata = None
    _basepath = None
    _datafile = None
    cfg = None
    assassin = None
    _datafile = 'assassinsgreed.dat'
    metadata = {
        'name': "Assassin's Greed",
        'gamekey': 'assassinsgreed',
        'broadcast_actions': ['assassinate', 'heal', 'collect', 'climb', 'reroll'],
        'actions': [
            {
                'key': 'assassinate',
                'name': 'Assassinate',
                'description': 'Find a villain to assassinate.',
                'img': 'images/icon-fight.png',
                'tinyimg': 'images/tiny-icon-fight.png',
                'color': '#C30017',
            },
            {
                'key': 'heal',
                'name': 'Heal',
                'description': 'Heal to regain some health.',
                'img': 'images/icon-rest.png',
                'tinyimg': 'images/tiny-icon-health.png',
                'color': '#004C7B',
            },
            {
                'key': 'collect',
                'name': 'Collect Feathers',
                'description': 'Search for feathers.',
                'img': 'images/icon-loot.png',
                'tinyimg': 'images/tiny-icon-gold.png',
                'color': '#E9B700',
            },
            {
                'key': 'climb',
                'name': 'Climb',
                'description': 'Climb a tower in the city.',
                'img': 'images/icon-deeper.png',
                'tinyimg': 'images/tiny-icon-level.png',
                'color': '#351E00',
            },
            {
                'key': 'reroll',
                'name': 'Reroll',
                'description': 'Reroll a new assassin if the current is dead.',
                'img': 'images/icon-reroll.png',
                'tinyimg': 'images/tiny-icon-reroll.png',
            },
            {
                'key': 'stats',
                'name': 'Stats',
                'description': 'Update character sheet.',
            },
        ],
        'stats_img': 'images/icon-stats.png',
        'stats': [
            {
                'key': 'name',
                'name': 'Name',
                'description': '',
                'type': 'string',
            },
            {
                'key': 'strength',
                'name': 'Strength',
                'description': '',
                'type': 'integer',
                'img': 'images/tiny-icon-strength.png',
            },
            {
                'key': 'health',
                'name': 'Health',
                'description': '',
                'type': 'integer',
                'img': 'images/tiny-icon-health.png',
            },
            {
                'key': 'hurt',
                'name': 'Hurt',
                'description': '',
                'type': 'integer',
                'img': 'images/tiny-icon-hurt.png',
            },
            {
                'key': 'towers',
                'name': 'Towers',
                'description': '',
                'type': 'integer',
                'img': 'images/tiny-icon-level.png',
            },
            {
                'key': 'assassinations',
                'name': 'Assassinations',
                'description': '',
                'type': 'integer',
                'img': 'images/tiny-icon-kills.png',
            },
            {
                'key': 'feathers',
                'name': 'Feathers',
                'description': '',
                'type': 'integer',
                'img': 'images/tiny-icon-gold.png',
            },
            {
                'key': 'alive',
                'name': 'Alive',
                'type': 'boolean',
                'description': '',
            },
        ],
    }

    def setup(self):
        # Configure datahandler backend.
        self.setup_database()

        # Read saved assassin.
        self.get_assassin()

    @LogUsageCPU
    def setup_database(self):
        """
        Sets up either a sqlite database or a GAE DataStore depending on configuration.
        """
        datahandler = self._cfg.get('LOCAL', 'datahandler')
        if datahandler == 'sqlite':
            from AGSQLHandler import AGSQLHandler
            self._dh = AGSQLHandler(self._debug)
        elif datahandler == 'datastore':
            from AGDSHandler import AGDSHandler
            self._dh = AGDSHandler(self._debug)
        else:
            raise GoldFrameConfigException, "Unknown datahandler: %s" % datahandler

    @LogUsageCPU
    def get_assassin(self):
        self.assassin = self._dh.get_alive_assassin()

    def get_target(self, lvl=None):
        if not lvl:
            lvl = self.assassin.towers or 1
        targets = []
        for target in self._gamedata['target']:
            if lvl >= target['lowlevel'] and (target['highlevel'] == 0 or lvl <= target['highlevel']):
                targets.append(target['name'])
        if targets:
            name = random.choice(targets)
        else:
            name = None
        # TODO: Bosses need to be supported.
        target = Target(self.assassin.towers, name)
        return target

    def play(self, command, asdict=False):
        # Handle action command.
        response = None
        if command in ['reroll']:
            response = self.action_reroll()
        elif not self.assassin or not self.assassin.alive:
            msg = self.get_text('nochampion')
            response = {
                'message': msg,
                'success': 0,
            }
        else:
            try:
                func = getattr(self, 'action_%s' % command)
            except AttributeError:
                return None
            else:
                response = func()

        self.save_data()

        return self.return_response(response, asdict)

    def save_data(self):
        if self.assassin:
            self._dh.save_data(self.assassin)

    def get_alive_assassin(self):
        assassin = self._dh.get_alive_assassin()
        return assassin

    def action_reroll(self):
        if self.assassin and self.assassin.alive:
            response = {
                'message': self.get_text('noreroll') % self.assassin.get_attributes(),
                'success': 0,
            }
            return response
        else:
            # Reroll new assassin.
            self.assassin = Assassin(self._gamedata['assassin'])
            self.assassin.reroll()
            attribs = self.assassin.get_attributes()
            msg = self.get_text('newassassin')
            try:
                msg = msg % attribs
            except KeyError, e:
                logging.error("Couldn't find a given text replacement: %s" % str(e))
            response = {
                'message': msg,
                'data': {
                    'assassin': attribs,
                }
            }
            return response

    def action_collect(self):
        msg = ''
        response = {
            'message': msg,
            'data': {
                'feathers': feathers,
                'assassin': {
                }
            }
        }
        attribs = self.assassin.get_attributes()
        luck = self.roll(10)
        if luck > 4:
            msg = self.get_text('foundfeathers')
            # Should be a method on assassin
            self.assassin.collect()
            self.assassin.feathers = self.assassin.feathers + 1
            response['data']['feathers'] = 1
            attribs['feathers'] = self.assassin.feathers
            response['data']['assassin']['feathers'] = self.assassin.feathers
        elif luck > 1:
            msg = self.get_text('nofeathers')
        else:
            return self.sneak_attack()
        msg = msg % attribs
        response['message'] = msg
        return response

    def action_heal(self):
        healed = self.assassin.heal()
        if healed:
            if self.assassin.hurt:
                restmsg = self.get_text('heals')
            else:
                restmsg = self.get_text('healed')
        else:
            restmsg = self.get_text('alreadyhealed')
        attribs = self.assassin.get_attributes()
        attribs['healed'] = healed
        msg = restmsg % attribs
        response = {
            'message': msg,
            'data': {
                'healed': attribs['healed'],
                'assassin': {
                    'health': attribs['health'],
                    'hurt': attribs['hurt'],
                    'alive': attribs['alive'],
                }
            }
        }
        return response

    def action_climb(self):
        towers = self.assassin.climb()
        msg = self.get_text('climb')
        attribs = self.assassin.get_attributes()
        msg = msg % attribs
        response = {
            'message': msg,
            'data': {
                'assassin': {
                    'towers': attribs['towers'],
                }
            }
        }
        return response

    def action_assassinate(self):
        target = self.get_target(self.assassin.towers)
        if not target:
            msg = self.get_text('notargets')
            response = {
                'message': msg % self.assassin.get_attributes(),
                'success': 0,
            }
            return response
        target_health = target.health
        (won, hurt_in_fight) = self.assassin.assassinate(target)
        attribs = self.assassin.get_attributes()
        if won:
            msg = self.get_text('killed')
            attribs['slayed'] = self.get_text('slayed')
        else:
            msg = self.get_text('died')
        attribs['target'] = target.name
        msg = msg % attribs
        msg = self.firstupper(msg)
        response = {
            'message': msg,
            'data': {
                'hurt_in_fight': hurt_in_fight,
                'assassin': {
                    'health': attribs['health'],
                    'hurt': attribs['hurt'],
                    'hurt_in_fight': hurt_in_fight,
                    'assassinations': attribs['assassinations'],
                    'alive': attribs['alive'],
                },
                'target': {
                    'name': target.name,
                    'strength': target.strength,
                    'health': target_health,
                    'hurt': target_health - target.health,
                    'boss': target.boss,
                    'count': 1,
                }
            }
        }
        return response

    def action_stats(self):
        msg = self.get_text('charsheet')
        attribs = self.assassin.get_attributes()
        msg = msg % attribs
        response = {
            'message': msg,
            'data': {
                'assassin': attribs,
            }
        }
        return response

    def sneak_attack(self):
        target = self.get_target(self.assassin.towers)
        target_health = target.health
        (won, hurt_in_fight) = self.assassin.assassinate(target)
        if won:
            msg = self.get_text('sneak_attack_won')
        else:
            msg = self.get_text('sneak_attack_lost')
        attribs = self.assassin.get_attributes()
        attribs['target_name'] = target.name
        msg = msg % attribs
        # FIXME: the assassin.fight() method should return needed info.
        response = {
            'message': msg,
            'success': 0,
            'data': {
                'hurt_in_fight': hurt_in_fight,
                'assassin': {
                    'hurt': attribs['hurt'],
                    'health': attribs['health'],
                    'assassinations': attribs['assassinations'],
                    'alive': attribs['alive'],
                    'rested': 0,
                },
                'target': {
                    'name': target.name,
                    'strength': target.strength,
                    'health': target_health,
                    'hurt': target_health - target.health,
                    'boss': target.boss,
                    'count': 1,
                },
            }
        }
        return response


