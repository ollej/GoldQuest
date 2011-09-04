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

from Hero import Hero
from Monster import Monster
from Level import Level

class GoldQuestException(Exception):
    pass

class GoldQuestConfigException(GoldQuestException):
    pass

class GoldQuest(object):
    _gamedata = None
    cfg = None
    hero = None
    level = None

    def __init__(self, cfg):
        """
        Setup Sqlite SQL tables and start a db session.

        The database will be saved in C{extras/goldquest.db}

        Calls L{setup_tables} to setup table metadata and L{setup_session}
        to instantiate the db session.
        """
        self._cfg = cfg
        try:
            debug = self._cfg.getboolan('LOCAL', 'debug')
        except AttributeError:
            debug = False

        path = os.path.abspath(__file__)
        self.basepath = os.path.dirname(path)

        # Read text data
        self.read_texts()

        # Configure datahandler backend.
        datahandler = self._cfg.get('LOCAL', 'datahandler')
        if datahandler == 'sqlite':
            from SqlDataHandler import SqlDataHandler
            self._dh = SqlDataHandler(debug)
        elif datahandler == 'datastore':
            from DataStoreDataHandler import DataStoreDataHandler
            self._dh = DataStoreDataHandler(debug)
        else:
            raise GoldQuestConfigException, "Unknown datahandler: %s" % datahandler

        self.hero = self._dh.get_alive_hero()
        if self.hero and not self.level:
            self.level = self.get_level(self.hero.level) #Level(self.hero.level)

    def read_texts(self):
        f = open('%s/extras/goldquest.dat' % self.basepath)
        self._gamedata = yaml.load(f)
        f.close()

    def get_text(self, text):
        texts = self._gamedata['texts'][text]
        if not texts:
            return None
        elif isinstance(texts, basestring):
            return texts
        else:
            return random.choice(texts)

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

    def return_response(self, response, asdict):
        if asdict:
            if not 'success' in response:
                response['success'] = 1
            return response
        else:
            return response['message']


    def play(self, command, asdict=False):
        response = ""
        command = command.strip().lower()
        try:
            (command, rest) = command.split(' ')
        except ValueError:
            rest = ""
        rest = rest.strip()
        if command in ['reroll']:
            response = self.reroll()
            return self.return_response(response, asdict)
        if not self.hero or not self.hero.alive:
            msg = self.get_text('nochampion')
            response = {
                'message': msg,
                'success': 0,
            }
            return self.return_response(response, asdict)
        if command in ['rest', 'vila']:
            response = self.rest()
        elif command in ['fight', 'kill', 'slay', u'slåss']:
            response = self.fight()
        elif command in ['deeper', 'down', 'descend', 'vidare']:
            response = self.go_deeper(rest)
        elif command in ['loot', 'search', u'sök', 'finna']:
            response = self.search_treasure()
        elif command in ['charsheet', 'stats', u'formulär']:
            response = self.show_charsheet()
        else:
            return None
        self.save_data()
        return self.return_response(response, asdict)

    def save_data(self):
        self._dh.save_data(self.hero, self.level)

    def get_alive_hero(self):
        hero = self._dh.get_alive_hero()
        return hero

    def get_level(self, lvl):
        level = self._dh.get_level(lvl)
        logging.info('read level:', level)
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

    def reroll(self):
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
            self.hero = Hero()
            self.hero.reroll()
            self.level = self.get_level(self.hero.level)
            attribs = self.hero.get_attributes()
            self.save_data()
            msg = self.get_text('newhero')
            try:
                msg = msg % attribs
            except KeyError, e:
                #print "Key not found in hero attribs:", e, attribs
                logging.info("Couldn't find a given text replacement:", e)
            if self.level._text:
                msg = "%s %s" % (msg, self.level._text)
            response = {
                'message': msg,
                'data': {
                    'hero': attribs,
                }
            }
            return response

    def search_treasure(self):
        #loot = self.hero.search_treasure()
        loot = 0
        msg = ''
        response = {
            'message': msg,
            'data': {
                'loot': loot,
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
                response['data']['loot'] = loot
                attribs['loot'] = loot
                attribs['gold'] = self.hero.gold
                response['data']['hero']['gold'] = self.hero.gold
            elif loot < 0:
                attribs['trap_hurt'] = abs(loot)
                self.hero.injure(attribs['trap_hurt'])
                msg = self.get_text('foundtrap')
                response['data']['hero']['trap_hurt'] = attribs['trap_hurt']
                response['data']['hero']['hurt'] = self.hero.hurt
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
                won = self.hero.fight(monster)
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
                        'hero': {
                            'hurt': attribs['hurt'],
                            'health': attribs['health'],
                            'kills': attribs['kills'],
                            'alive': attribs['alive'],
                            'rested': 0,
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

    def rest(self):
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
                'rested': attribs['rested'],
                'hero': {
                    'health': attribs['health'],
                    'hurt': attribs['hurt'],
                    'alive': attribs['alive'],
                }
            }
        }
        return response

    def go_deeper(self, levels=1):
        try:
            levels = int(levels)
        except ValueError:
            levels = 1
        if levels > 10:
            levels = 10
        depth = self.hero.go_deeper(levels)
        self.level = self.get_level(depth)
        msg = self.level._text or self.get_text('deeper')
        attribs = self.hero.get_attributes()
        msg = msg % attribs
        response = {
            'message': msg,
            'data': {
                'hero': {
                    'level': attribs['level'],
                }
            }
        }
        return response

    def fight(self):
        monster = self.get_monster(self.level.depth)
        if not monster:
            msg = self.get_text('nomonsters')
            response = {
                'message': msg % self.hero.get_attributes(),
                'success': 0,
            }
            return response
        monster_health = monster.health
        won = self.hero.fight(monster)
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
                'hero': {
                    'health': attribs['health'],
                    'hurt': attribs['hurt'],
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

    def show_charsheet(self):
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

    def roll(self, sides, times=1):
        total = 0
        for i in range(times):
            total = total + random.randint(1, sides)
        return total

    def firstupper(self, text):
        first = text[0].upper()
        return first + text[1:]


