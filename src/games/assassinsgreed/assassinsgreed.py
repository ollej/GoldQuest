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

from GoldFrame import GoldFrame

from decorators import *

from Assassin import Assassin
from Target import Target

class Game(GoldFrame.GamePlugin):
    _gamedata = None
    _basepath = None
    _datafile = None
    _cfg = None
    assassin = None
    _datafile = 'assassinsgreed.dat'
    _alive_actions = {
        'hidden': ['reroll'],
        'active': ['assassinate', 'fight', 'heal', 'buy', 'collect', 'climb'],
    }
    _dead_actions = {
        'active': ['reroll'],
        'hidden': ['assassinate', 'fight', 'heal', 'buy', 'collect', 'climb'],
    }
    metadata = {
        'name': "Assassin's Greed",
        'gamekey': 'assassinsgreed',
        'personal_hero': True,
        'broadcast_actions': [],
        'actions': [
            {
                'key': 'assassinate',
                'name': 'Assassinate',
                'description': 'Find a villain to assassinate.',
                'img': '/images/assassinsgreed/icon-assassinate.png',
                'tinyimg': '/images/assassinsgreed/tiny-icon-assassination.png',
                'color': '#C30017',
                'button': 'active',
            },
            {
                'key': 'fight',
                'name': 'Fight',
                'description': 'Find a villain to assassinate.',
                'img': '/images/assassinsgreed/icon-fight.png',
                'tinyimg': '/images/assassinsgreed/tiny-icon-fight.png',
                'color': '#C30017',
                'button': 'active',
            },
            {
                'key': 'heal',
                'name': 'Heal',
                'description': 'Heal to regain some health.',
                'img': '/images/assassinsgreed/icon-rest.png',
                'tinyimg': '/images/assassinsgreed/tiny-icon-health.png',
                'color': '#004C7B',
                'button': 'active',
            },
            {
                'key': 'buy',
                'name': 'Buy',
                'description': 'Buy items from a local merchant.',
                'img': '/images/assassinsgreed/icon-buy.png',
                'tinyimg': '/images/assassinsgreed/tiny-icon-buy.png',
                'color': '#C30017',
                'button': 'active',
                'arguments': [
                    {
                        'type': 'list',
                        'key': 'item',
                        'name': 'Item',
                        'description': 'Item to buy',
                        'items': ['Potion', 'Smokebomb', 'Splinterbomb', 'Dagger'],
                    },
                    {
                        'type': 'input',
                        'key': 'amount',
                        'name': 'Amount',
                        'description': 'Amount of items to buy',
                    },
                ]
            },
            {
                'key': 'collect',
                'name': 'Collect Feathers',
                'description': 'Search for feathers.',
                'img': '/images/assassinsgreed/icon-collect.png',
                'tinyimg': '/images/assassinsgreed/tiny-icon-feathers.png',
                'color': '#E9B700',
                'button': 'active',
            },
            {
                'key': 'climb',
                'name': 'Climb',
                'description': 'Climb a tower in the city.',
                'img': '/images/assassinsgreed/icon-climb.png',
                'tinyimg': '/images/assassinsgreed/tiny-icon-towers.png',
                'color': '#351E00',
                'button': 'active',
            },
            {
                'key': 'reroll',
                'name': 'Reroll',
                'description': 'Reroll a new assassin if the current is dead.',
                'img': '/images/assassinsgreed/icon-reroll.png',
                'tinyimg': '/images/assassinsgreed/tiny-icon-reroll.png',
                'button': 'button',
            },
            {
                'key': 'stats',
                'name': 'Stats',
                'description': 'Update character sheet.',
                'button': 'hidden',
            },
        ],
        'stats_img': '/images/assassinsgreed/icon-stats.png',
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
                'img': '/images/assassinsgreed/tiny-icon-strength.png',
            },
            {
                'key': 'health',
                'name': 'Health',
                'description': '',
                'type': 'integer',
                'img': '/images/assassinsgreed/tiny-icon-health.png',
            },
            {
                'key': 'hurt',
                'name': 'Hurt',
                'description': '',
                'type': 'integer',
                'img': '/images/assassinsgreed/tiny-icon-hurt.png',
            },
            {
                'key': 'towers',
                'name': 'Towers',
                'description': '',
                'type': 'integer',
                'img': '/images/assassinsgreed/tiny-icon-towers.png',
            },
            {
                'key': 'kills',
                'name': 'Kills',
                'description': '',
                'type': 'integer',
                'img': '/images/assassinsgreed/tiny-icon-kills.png',
            },
            {
                'key': 'assassinations',
                'name': 'Assassinations',
                'description': '',
                'type': 'integer',
                'img': '/images/assassinsgreed/tiny-icon-assassinations.png',
            },
            {
                'key': 'feathers',
                'name': 'Feathers',
                'description': '',
                'type': 'integer',
                'img': '/images/assassinsgreed/tiny-icon-feathers.png',
            },
            {
                'key': 'potions',
                'name': 'Potions',
                'description': 'Health potions.',
                'type': 'integer',
                'img': '/images/assassinsgreed/tiny-icon-potions.png',
            },
            {
                'key': 'smokebombs',
                'name': 'Smokebombs',
                'description': 'Smokebombs',
                'type': 'integer',
                'img': '/images/assassinsgreed/tiny-icon-smokebombs.png',
            },
            {
                'key': 'splinterbombs',
                'name': 'Splinterbombs',
                'description': 'Splinterbombs',
                'type': 'integer',
                'img': '/images/assassinsgreed/tiny-icon-splinterbombs.png',
            },
            {
                'key': 'daggers',
                'name': 'Daggers',
                'description': 'Daggers',
                'type': 'integer',
                'img': '/images/assassinsgreed/tiny-icon-daggers.png',
            },
            {
                'key': 'alive',
                'name': 'Alive',
                'type': 'boolean',
                'description': '',
            },
        ],
        'extra_info': {
            'hurt_in_fight': {
                'name': 'Hurt',
                'cls': 'hurtInfo',
            },
            'hurt_by_action': {
                'name': 'Hurt',
                'cls': 'hurtInfo',
            },
            'healed': {
                'name': 'Healed',
                'cls': 'restInfo',
            },
            'gold': {
                'name': 'Gold',
                'cls': 'lootInfo',
            },
            'towers': {
                'name': 'Towers',
                'style': 'color: #351E00',
            },
            'feathers': {
                'name': 'Feathers',
                'style': 'color: #666',
            },
            'dinged': {
                'name': 'Dinged',
                'style': 'color: teal',
            },
            'item': {
                'name': 'Item',
                'style': 'color: green',
            },
            'total_price': {
                'name': 'Price',
                'style': 'color: mediumorchid',
            },
        },
    }
    _items = {
        'Potion': { 'key': 'potions', 'price': 10 },
        'Smokebomb': { 'key': 'smokebombs', 'price': 25 },
        'Splinterbomb': { 'key': 'splinterbombs', 'price': 15 },
        'Dagger': { 'key': 'daggers', 'price': 10 },
    }

    def template_charsheet(self):
        return """
        <h1 id="nameValue" class="nameValue">{{ name }}</h1>
        <ul class="charsheetList">
          <li class="statItem" id="strengthStatDiv"><img src="/images/assassinsgreed/tiny-icon-strength.png" width="16" height="16" alt="Strength" title="Strength" /><span class="statValue" id="strengthValue">{{ strength }}</span></li>
          <li class="statItem" id="healthStatDiv"><img src="/images/assassinsgreed/tiny-icon-health.png" width="16" height="16" alt="Health" title="Health" /><span class="statValue" id="hurthealthValue">{{ current_health }}/{{ health }}</span></li>
          <li class="statItem" id="towersStatDiv"><img src="/images/assassinsgreed/tiny-icon-towers.png" width="16" height="16" alt="Towers" title="Towers" /><span class="statValue" id="towersValue">{{ towers }}</span></li>
          <li class="statItem" id="assassinationsStatDiv"><img src="/images/assassinsgreed/tiny-icon-assassinations.png" width="16" height="16" alt="Assassinations" title="Assassinations" /><span class="statValue" id="assassinationsValue">{{ assassinations }}</span></li>
          <li class="statItem" id="killsStatDiv"><img src="/images/assassinsgreed/tiny-icon-kills.png" width="16" height="16" alt="Kills" title="Kills" /><span class="statValue" id="killsValue">{{ kills }}</span></li>
          <li class="statItem" id="feathersStatDiv"><img src="/images/assassinsgreed/tiny-icon-feathers.png" width="16" height="16" alt="Feathers" title="Feathers" /><span class="statValue" id="feathersValue">{{ feathers }}</span></li>
          <li class="statItem" id="goldStatDiv"><img src="/images/assassinsgreed/tiny-icon-gold.png" width="16" height="16" alt="Gold" title="Gold" /><span class="statValue" id="lootValue">{{ gold }}</span></li>
        </ul>
        """

    def template_actionline(self):
        return "<li class='actionLine {{ cls }}' id='action_{{ id }}'>{{ line }}{{ extraInfo }}</li>"

    def setup(self):
        # Configure datahandler backend.
        #self.setup_database()

        # Read saved assassin.
        self.get_assassin(self._userid)

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
    def get_assassin(self, userid=None):
        self.assassin = self._dh.get_alive_assassin(userid)

    def get_boss(self, lvl=None):
        if not lvl:
            lvl = self.assassin.towers or 1
        boss = random.choice(self._gamedata['boss'])
        target = Target(lvl, boss, True)
        return target

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

    def play(self, command, asdict=False, arguments=None):
        # Load user assassin if needed.
        if self.assassin == None or self.assassin.userid != self._userid:
            self.get_assassin(self._userid)

        logging.info(arguments)

        # Handle action command.
        response = None
        actionbuttons = None
        if command in ['reroll']:
            response = self.action_reroll(arguments)
            actionbuttons = self._alive_actions
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
                response = func(arguments)

        self.save_data()

        if not self.assassin or not self.assassin.alive:
            actionbuttons = self._dead_actions

        return self.return_response(response, asdict, actionbuttons)

    def save_data(self):
        if self.assassin:
            self._dh.save_data(self.assassin)

    def get_alive_assassin(self):
        assassin = self._dh.get_alive_assassin()
        return assassin

    def action_reroll(self, aguments):
        if self.assassin and self.assassin.alive:
            response = {
                'message': self.get_text('noreroll') % self.assassin.get_attributes(),
                'success': 0,
            }
            return response
        else:
            # Reroll new assassin.
            self.assassin = Assassin(self._gamedata['assassin'], userid=self._userid)
            self.assassin.reroll()
            attribs = self.assassin.get_attributes()
            logging.info(attribs)
            msg = self.get_text('newassassin')
            try:
                msg = msg % attribs
            except KeyError, e:
                logging.error("Couldn't find a given text replacement: %s" % str(e))
            response = {
                'message': msg,
                'data': {
                    'hero': attribs,
                }
            }
            return response

    def action_buy(self, arguments):
        try:
            item = arguments['item']
            logging.info('item: %s' % item)
            amount = int(arguments['amount'])
            logging.info('amount: %d' % amount)
            itemobj = self._items[item]
        except KeyError, ValueError:
            response = {
                'message': 'Merchant has closed.',
                'success': 0,
            }
            return response
        item_text = item.lower()
        if amount > 1:
            item_text = "%ss" % item_text
        total_price = self.assassin.buy(itemobj, amount)
        attribs = self.assassin.get_attributes()
        attribs['amount'] = amount
        attribs['item'] = item_text
        attribs['total_price'] = total_price
        if total_price == 0:
            response = {
                'message': self.get_text('no_money') % attribs,
                'success': 0,
            }
            return response
        msg = self.get_text('buy_item') % attribs
        response = {
            'message': msg,
            'data': {
                'extra_info': {
                    'item': item,
                    'total_price': total_price,
                },
                'hero': self.assassin.get_attributes(),
            }
        }
        return response

    def action_collect(self, arguments):
        msg = ''
        response = {
            'message': msg,
            'data': {
                'extra_info': {
                    'feathers': 0,
                },
                'hero': {
                    'feathers': self.assassin.feathers,
                }
            }
        }
        attribs = self.assassin.get_attributes()
        luck = self.roll(20)
        if luck > 8:
            msg = self.get_text('foundfeathers')
            # Should be a method on assassin
            feathers = self.assassin.collect()
            response['data']['hero']['feathers'] = feathers
            response['data']['extra_info']['feathers'] = feathers
            response['data']['extra_info']['collected'] = 1
            attribs['feathers'] = 1
        elif luck > 3:
            msg = self.get_text('nofeathers')
        else:
            return self.sneak_attack()
        msg = msg % attribs
        response['message'] = msg
        return response

    def action_heal(self, arguments):
        healed = self.assassin.heal()
        if healed > 0:
            if self.assassin.hurt:
                healmsg = self.get_text('heals')
            else:
                healmsg = self.get_text('healed')
        elif healed == -1:
            healmsg = self.get_text('no_potions')
            healed = 0
        else:
            healmsg = self.get_text('already_healed')
        attribs = self.assassin.get_attributes()
        attribs['healed'] = healed
        msg = healmsg % attribs
        response = {
            'message': msg,
            'data': {
                'extra_info': {
                    'healed': attribs['healed'],
                },
                'hero': {
                    'health': attribs['health'],
                    'hurt': attribs['hurt'],
                    'alive': attribs['alive'],
                    'potions': attribs['potions'],
                }
            }
        }
        return response

    def action_climb(self, arguments):
        hurt_by_action = 0
        climbed = 0
        msg = ''
        luck = self.roll(20)
        if luck > 4:
            towers = self.assassin.climb()
            msg = self.get_text('climbs')
            climbed = 1
        else:
            (msg, hurt_by_action) = self.fall()
        attribs = self.assassin.get_attributes()
        attribs['hurt_by_action'] = hurt_by_action
        msg = msg % attribs
        response = {
            'message': msg,
            'data': {
                'extra_info': {
                    'climbed': climbed,
                    'towers': attribs['towers'],
                    'hurt_by_action': hurt_by_action,
                },
                'hero': {
                    'towers': attribs['towers'],
                    'hurt': attribs['hurt'],
                    'alive': attribs['alive'],
                    'health': attribs['health'],
                }
            }
        }
        return response

    def action_assassinate(self, arguments):
        target = None
        if self.assassin.assassinations < self.assassin.towers:
            target = self.get_boss()
        return self.fight_target(target)

    def action_fight(self, arguments):
        target = self.get_target(self.assassin.towers)
        return self.fight_target(target)

    def action_stats(self, arguments):
        msg = self.get_text('charsheet')
        attribs = self.assassin.get_attributes()
        msg = msg % attribs
        response = {
            'message': msg,
            'data': {
                'hero': attribs,
            }
        }
        return response

    def fall(self):
        msg = ''
        hurt_by_action = self.roll(self.assassin.towers + 1)
        if self.assassin.feathers > 0:
            saved = self.roll(self.assassin.feathers)
            logging.info('saved by feathers: %d, hurt_before: %d', saved, hurt_by_action)
            hurt_by_action -= saved
        if hurt_by_action > 0:
            (alive, hurt) = self.assassin.injure(hurt_by_action)
            if alive:
                msg = self.get_text('fallen')
            else:
                msg = self.get_text('fallen_to_death')
        else:
            msg = self.get_text('fallen_feather_save')
        return (msg, hurt_by_action)

    def fight_target(self, target):
        if not target:
            msg = self.get_text('notargets')
            response = {
                'message': msg % self.assassin.get_attributes(),
                'success': 0,
            }
            return response
        dinged = False
        target_health = target.health
        gold = 0
        (won, hurt_in_fight) = self.assassin.fight(target)
        attribs = self.assassin.get_attributes()
        if won:
            msg = self.get_text('killed')
            attribs['slayed'] = self.get_text('slayed')
            dinged = self.assassin.ding(target.strength)
            gold = target.drop_loot()
            self.assassin.gold += gold
        else:
            msg = self.get_text('died')
        attribs['target'] = target.name
        msg = msg % attribs
        msg = self.firstupper(msg)
        response = {
            'message': msg,
            'data': {
                'extra_info': {
                    'hurt_in_fight': hurt_in_fight,
                    'dinged': dinged,
                    'gold': gold,
                },
                'hero': {
                    'strength': attribs['strength'],
                    'health': attribs['health'],
                    'hurt': attribs['hurt'],
                    'kills': attribs['kills'],
                    'assassinations': attribs['assassinations'],
                    'alive': attribs['alive'],
                    'gold': self.assassin.gold,
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

    def sneak_attack(self):
        target = self.get_target(self.assassin.towers)
        target_health = target.health
        (won, hurt_in_fight) = self.assassin.fight(target)
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
                'extra_info': {
                    'hurt_in_fight': hurt_in_fight,
                },
                'hero': {
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


