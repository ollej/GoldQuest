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

from Hero import Hero
from Monster import Monster
from Level import Level

class Game(GoldFrame.GamePlugin):
    _cfg = None
    hero = None
    level = None
    _datafile = 'goldquest.dat'
    _alive_actions = {
        'hidden': ['reroll'],
        'active': ['fight', 'deeper', 'loot', 'rest'],
    }
    _dead_actions = {
        'active': ['reroll'],
        'hidden': ['fight', 'deeper', 'loot', 'rest'],
    }
    metadata = {
        'name': 'Gold Quest',
        'gamekey': 'goldquest',
        'personal_hero': False,
        'broadcast_actions': ['fight', 'rest', 'loot', 'deeper', 'reroll'],
        'actions': [
            {
                'key': 'fight',
                'name': 'Fight',
                'description': 'Find a monster and fight it.',
                'img': 'images/goldquest/icon-fight.png',
                'tinyimg': 'images/goldquest/tiny-icon-fight.png',
                'color': '#C30017',
                'button': 'active',
            },
            {
                'key': 'rest',
                'name': 'Rest',
                'description': 'Rest to regain some health.',
                'img': 'images/goldquest/icon-rest.png',
                'tinyimg': 'images/goldquest/tiny-icon-health.png',
                'color': '#004C7B',
                'button': 'active',
            },
            {
                'key': 'loot',
                'name': 'Loot',
                'description': 'Search for gold.',
                'img': 'images/goldquest/icon-loot.png',
                'tinyimg': 'images/goldquest/tiny-icon-gold.png',
                'color': '#E9B700',
                'button': 'active',
            },
            {
                'key': 'deeper',
                'name': 'Deeper',
                'description': 'Descend deeper into the dungeon.',
                'img': 'images/goldquest/icon-deeper.png',
                'tinyimg': 'images/goldquest/tiny-icon-level.png',
                'color': '#351E00',
                'button': 'active',
            },
            {
                'key': 'reroll',
                'name': 'Reroll',
                'description': 'Reroll a new hero if the current is dead..',
                'img': 'images/goldquest/icon-reroll.png',
                'tinyimg': 'images/goldquest/tiny-icon-reroll.png',
                'button': 'hidden',
            },
            {
                'key': 'stats',
                'name': 'Stats',
                'description': 'Update character sheet.',
                'button': 'hidden',
            },
        ],
        'stats_img': 'images/goldquest/icon-stats.png',
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
                'img': 'images/goldquest/tiny-icon-strength.png',
            },
            {
                'key': 'health',
                'name': 'Health',
                'description': '',
                'type': 'integer',
                'img': 'images/goldquest/tiny-icon-health.png',
            },
            {
                'key': 'hurt',
                'name': 'Hurt',
                'description': '',
                'type': 'integer',
                'img': 'images/goldquest/tiny-icon-hurt.png',
            },
            {
                'key': 'level',
                'name': 'Level',
                'description': '',
                'type': 'integer',
                'img': 'images/goldquest/tiny-icon-level.png',
            },
            {
                'key': 'kills',
                'name': 'Kills',
                'description': '',
                'type': 'integer',
                'img': 'images/goldquest/tiny-icon-kills.png',
            },
            {
                'key': 'gold',
                'name': 'Gold',
                'description': '',
                'type': 'integer',
                'img': 'images/goldquest/tiny-icon-gold.png',
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
            'hurt_by_trap': {
                'name': 'Hurt',
                'cls': 'hurtInfo',
            },
            'rested': {
                'name': 'Rested',
                'cls': 'restInfo',
            },
            'loot': {
                'name': 'Loot',
                'cls': 'lootInfo',
            },
            'level': {
                'name': 'Level',
                'cls': 'levelInfo',
            },
            'dinged': {
                'name': 'Dinged',
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
        #path = os.path.join(os.path.dirname(__file__), 'extras', 'goldquest_template_charsheet.html')
        #return file(path,'r').read()
        return """
        <img src="images/goldquest/icon-stats.png" class="statsImage" style="float: left" width="32" height="32" alt="Stats" title="Stats" />
        <h1 id="nameValue" class="nameValue">{{ name }}</h1>
        <ul class="charsheetList">
          <li class="statItem" id="strengthStatDiv"><img src="images/goldquest/tiny-icon-strength.png" width="16" height="16" alt="Strength" title="Strength" /><span class="statValue" id="strengthValue">{{ strength }}</span></li>
          <li class="statItem" id="healthStatDiv"><img src="images/goldquest/tiny-icon-health.png" width="16" height="16" alt="Health" title="Health" /><span class="statValue" id="hurthealthValue">{{ current_health }}/{{ health }}</span></li>
          <li class="statItem" id="levelStatDiv"><img src="images/goldquest/tiny-icon-level.png" width="16" height="16" alt="Level" title="Level" /><span class="statValue" id="levelValue">{{ level }}</span></li>
          <li class="statItem" id="killsStatDiv"><img src="images/goldquest/tiny-icon-kills.png" width="16" height="16" alt="Kills" title="Kills" /><span class="statValue" id="killsValue">{{ kills }}</span></li>
          <li class="statItem" id="goldStatDiv"><img src="images/goldquest/tiny-icon-gold.png" width="16" height="16" alt="Gold" title="Gold" /><span class="statValue" id="goldValue">{{ gold }}</span></li>
        </ul>
        """

    def template_actionline(self):
        return "<li class='actionLine {{ cls }}' id='action_{{ id }}'>{{ line }}{{ extraInfo }}</li>"

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
            from GQDSHandler import GQDSHandler
            self._dh = GQDSHandler(self._debug)
        else:
            raise GoldFrameConfigException, "Unknown datahandler: %s" % datahandler

    @LogUsageCPU
    def get_hero(self):
        self.hero = self._dh.get_alive_hero()
        if self.hero and not self.level:
            self.level = self.get_level(self.hero.level)

    def get_level_texts(self, depth):
        for lvl in self._gamedata['level']:
            if lvl['level'] == depth:
                return lvl

    def get_monster(self, lvl=None):
        if not lvl:
            lvl = self.level.depth or 1
        monsters = []
        for monster in self._gamedata['monster']:
            if lvl >= monster['lowlevel'] and monster['highlevel'] == 0 or lvl <= monster['highlevel']:
                monsters.append(monster['name'])
        if monsters:
            name = random.choice(monsters)
        else:
            name = None
        return self.level.get_monster(name)

    def play(self, command, asdict=False, arguments=None):
        response = ""
        command = command.strip().lower()
        try:
            (command, rest) = command.split(' ')
        except ValueError:
            rest = ""
        rest = rest.strip()
        if command in ['reroll']:
            response = self.action_reroll()
            return self.return_response(response, asdict, self._alive_actions)
        if not self.hero or not self.hero.alive:
            msg = self.get_text('nochampion')
            response = {
                'message': msg,
                'success': 0,
            }
            return self.return_response(response, asdict, self._dead_actions)
        if command in ['rest', 'vila']:
            response = self.action_rest()
        elif command in ['fight', 'kill', 'slay', u'slåss']:
            response = self.action_fight()
        elif command in ['deeper', 'down', 'descend', 'vidare']:
            response = self.action_deeper(rest)
        elif command in ['loot', 'search', u'sök', 'finna']:
            response = self.action_loot()
        elif command in ['charsheet', 'stats', u'formulär']:
            response = self.action_stats()
        else:
            return None
        self.save_data()
        change_buttons = None
        if not self.hero.alive:
            change_buttons = self._dead_actions
        return self.return_response(response, asdict, change_buttons)

    def save_data(self):
        self._dh.save_data(self.hero, self.level)

    def get_alive_hero(self):
        hero = self._dh.get_alive_hero()
        return hero

    def get_level(self, lvl):
        level = self._dh.get_level(lvl)
        if not level:
            level = Level(lvl)
        texts = self.get_level_texts(lvl)
        if texts:
            for k, v in texts.items():
                if v:
                    setattr(level, '_%s' % k , v)
        if not level._boss:
            level._boss = random.choice(self._gamedata['boss'])
        return level

    def action_reroll(self):
        if self.hero and self.hero.alive:
            response = {
                'message': self.get_text('noreroll') % self.hero.get_attributes(),
                'success': 0,
            }
            return response
        else:
            # Clear all old level data.
            self._dh.clear_levels()
            # Reroll new hero.
            #logging.info('Rerolling hero.')
            #logging.info(self._gamedata['hero'])
            self.hero = Hero(self._gamedata['hero'])
            self.hero.reroll()
            self.level = self.get_level(self.hero.level)
            attribs = self.hero.get_attributes()
            self.save_data()
            msg = self.get_text('newhero')
            try:
                msg = msg % attribs
            except KeyError, e:
                #print "Key not found in hero attribs:", e, attribs
                logging.error("Couldn't find a given text replacement: %s" % str(e))
            if self.level._text:
                msg = "%s %s" % (msg, self.level._text)
            response = {
                'message': msg,
                'data': {
                    'hero': attribs,
                }
            }
            return response

    def action_loot(self):
        #loot = self.hero.search_treasure()
        loot = 0
        msg = ''
        response = {
            'message': msg,
            'data': {
                'extra_info': {
                    'loot': loot,
                },
                'hero': {
                }
            }
        }
        attribs = self.hero.get_attributes()
        if self.level.can_loot():
            loot = self.level.get_loot()
            if loot > 0:
                msg = self.get_text('foundloot')
                # Should be a method on Hero
                self.hero.gold = self.hero.gold + loot
                response['data']['extra_info']['loot'] = loot
                attribs['loot'] = loot
                attribs['gold'] = self.hero.gold
                response['data']['hero']['gold'] = self.hero.gold
            elif loot < 0:
                attribs['hurt_by_trap'] = abs(loot)
                self.hero.injure(attribs['hurt_by_trap'])
                msg = self.get_text('foundtrap')
                response['data']['extra_info']['hurt_by_trap'] = attribs['hurt_by_trap']
                response['data']['hero']['hurt'] = self.hero.hurt
                response['data']['hero']['health'] = self.hero.health
            else:
                msg = self.get_text('nogold')
        else:
            msg = self.get_text('noloot')
            response['success'] = 0
        msg = msg % attribs
        response['message'] = msg
        return response

    def sneak_attack(self):
        if self.level.has_monsters():
            #self.logprint("Monsters are available to sneak attack.")
            unlucky = self.roll(100)
            #self.logprint("unlucky:", unlucky)
            if unlucky < 20:
                #self.logprint("Sneak attack!")
                monster = self.get_monster(self.level.depth)
                monster_health = monster.health
                (won, hurt_in_fight) = self.hero.fight(monster)
                if won:
                    msg = self.get_text('rest_attack_won')
                else:
                    msg = self.get_text('rest_attack_lost')
                attribs = self.hero.get_attributes()
                attribs['monster_name'] = monster.name
                msg = msg % attribs
                # FIXME: the hero.fight() method should return needed info.
                response = {
                    'message': msg,
                    'success': 0,
                    'data': {
                        'extra_info': {
                            'hurt_in_fight': hurt_in_fight,
                            'rested': 0,
                        },
                        'hero': {
                            'hurt': attribs['hurt'],
                            'health': attribs['health'],
                            'kills': attribs['kills'],
                            'alive': attribs['alive'],
                        },
                        'monster': {
                            'name': monster.name,
                            'strength': monster.strength,
                            'health': monster_health,
                            'hurt': monster_health - monster.health,
                            'boss': monster.boss,
                            'count': 1,
                        },
                    }
                }
                return response

    def action_rest(self):
        # If there are monsters alive on the level, there is a
        # risk of a sneak attack while resting.
        response = self.sneak_attack()
        if response:
            return response
        rested = self.hero.rest()
        if rested:
            if self.hero.hurt:
                restmsg = self.get_text('rests')
            else:
                restmsg = self.get_text('healed')
        else:
            restmsg = self.get_text('alreadyhealed')
        attribs = self.hero.get_attributes()
        attribs['rested'] = rested
        msg = restmsg % attribs
        response = {
            'message': msg,
            'data': {
                'extra_info': {
                    'rested': attribs['rested'],
                },
                'hero': {
                    'health': attribs['health'],
                    'hurt': attribs['hurt'],
                    'alive': attribs['alive'],
                }
            }
        }
        return response

    def action_deeper(self, levels=1):
        try:
            levels = int(levels)
        except ValueError:
            levels = 1
        if levels > 10:
            levels = 10
        if self.level.has_monsters():
            response = {
                'message': self.get_text('level_not_cleared') % self.hero.get_attributes(),
                'success': 0,
            }
            return response
        depth = self.hero.go_deeper(levels)
        self.level = self.get_level(depth)
        msg = self.level._text or self.get_text('deeper')
        attribs = self.hero.get_attributes()
        msg = msg % attribs
        response = {
            'message': msg,
            'data': {
                'extra_info': {
                    'level': attribs['level'],
                },
                'hero': {
                    'level': attribs['level'],
                }
            }
        }
        return response

    def action_fight(self):
        monster = self.get_monster(self.level.depth)
        return self.fight_monster(monster)

    def fight_monster(self, monster):
        if not monster:
            msg = self.get_text('nomonsters')
            response = {
                'message': msg % self.hero.get_attributes(),
                'success': 0,
            }
            return response
        monster_health = monster.health
        (won, hurt_in_fight) = self.hero.fight(monster)
        attribs = self.hero.get_attributes()
        if won:
            msg = self.get_text('killed')
            attribs['slayed'] = self.get_text('slayed')
        else:
            msg = self.get_text('died')
        attribs['monster'] = monster.name
        msg = msg % attribs
        msg = self.firstupper(msg)
        response = {
            'message': msg,
            'data': {
                'extra_info': {
                    'hurt_in_fight': hurt_in_fight,
                },
                'hero': {
                    'health': attribs['health'],
                    'hurt': attribs['hurt'],
                    'hurt_in_fight': hurt_in_fight,
                    'kills': attribs['kills'],
                    'alive': attribs['alive'],
                },
                'monster': {
                    'name': monster.name,
                    'strength': monster.strength,
                    'health': monster_health,
                    'hurt': monster_health - monster.health,
                    'boss': monster.boss,
                    'count': 1,
                }
            }
        }
        return response

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



