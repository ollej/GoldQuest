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

from sqlalchemy import Table, Column, Integer, Boolean, String, MetaData, ForeignKey, Sequence, create_engine
from sqlalchemy.orm import mapper, sessionmaker
import random
import yaml

from utils.Conf import *
from Hero import Hero
from Monster import Monster
from Level import Level

class GoldQuest(BridgeClass):
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
        self.cfg = cfg
        try:
            debug = self.cfg.getboolan('LOCAL', 'debug')
        except AttributeError:
            debug = False
        self.read_texts()
        self.engine = create_engine('sqlite:///extras/quest.db', echo=debug)
        self.setup_tables()
        self.setup_session()
        self.hero = self.get_alive_hero()
        if self.hero and not self.level:
            self.level = Level(self.hero.level)

    def setup_session(self):
        """
        Start a SQLAlchemy db session.

        Saves the session instance in C{self.session}
        """
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def setup_tables(self):
        """
        Defines the tables to use for L{Hero}
        The Metadata instance is saved to C{self.metadata}
        """
        self.metadata = MetaData()
        hero_table = Table('hero', self.metadata,
            Column('id', Integer, Sequence('hero_id_seq'), primary_key=True),
            Column('name', String(100)),
            Column('health', Integer),
            Column('strength', Integer),
            Column('hurt', Integer),
            Column('kills', Integer),
            Column('gold', Integer),
            Column('level', Integer),
            Column('alive', Boolean),
        )
        mapper(Hero, hero_table)
        level_table = Table('level', self.metadata,
            Column('id', Integer, Sequence('hero_id_seq'), primary_key=True),
            Column('depth', Integer),
            Column('killed', Integer),
            Column('looted', Integer),
        )
        mapper(Level, level_table)
        self.metadata.create_all(self.engine)

    def read_texts(self):
        f = open('extras/goldquest.dat')
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

    def play(self, command):
        msg = ""
        command = command.strip().lower()
        try:
            (command, rest) = command.split(' ')
        except ValueError:
            rest = ""
        rest = rest.strip()
        if command in ['reroll']:
            return self.reroll()
        if not self.hero or not self.hero.alive:
            return self.get_text('nochampion')
        if command in ['rest', 'vila']:
            msg = self.rest()
        elif command in ['fight', 'kill', 'slay', u'slåss']:
            msg = self.fight()
        elif command in ['deeper', 'descend', 'vidare']:
            msg = self.go_deeper(rest)
        elif command in ['loot', 'search', u'sök', 'finna']:
            msg = self.search_treasure()
        elif command in ['charsheet', 'stats', u'formulär']:
            msg = self.show_charsheet()
        else:
            return None
        self.save_data()
        return msg

    def save_data(self):
        self.session.add(self.hero)
        self.session.add(self.level)
        self.session.commit()

    def get_alive_hero(self):
        hero = self.session.query(Hero).filter_by(alive=True).first()
        return hero

    def get_level(self, lvl):
        level = self.session.query(Level).filter_by(depth=lvl).first()
        if not level:
            level = Level(lvl)
        texts = self.get_level_texts(lvl)
        if texts:
            for k, v in texts.items():
                if v:
                    setattr(level, k , v)
        if not level.boss:
            level.boss = random.choice(self._gamedata['boss'])
        return level

    def reroll(self):
        if self.hero and self.hero.alive:
            msg = self.get_text('noreroll') % self.hero.get_attributes()
            return msg
        else:
            # Delete all old Level data.
            self.session.query(Level).delete()
            # Reroll new hero.
            self.hero = Hero()
            self.hero.reroll()
            self.level = self.get_level(self.hero.level)
            self.save_data()
            msg = self.get_text('newhero')
            msg = msg % self.hero.get_attributes()
            msg = msg + " " + self.level.text
            return msg

    def search_treasure(self):
        #loot = self.hero.search_treasure()
        attribs = self.hero.get_attributes()
        if self.level.can_loot():
            loot = self.level.get_loot()
            attribs['loot'] = loot
            if loot > 0:
                msg = self.get_text('foundloot')
            elif loot < 0:
                attribs['trap_hurt'] = abs(loot)
                self.hero.injure(attribs['trap_hurt'])
                msg = self.get_text('foundtrap')
            else:
                msg = self.get_text('nogold')
        else:
            msg = self.get_text('noloot')
        msg = msg % attribs
        return msg

    def sneak_attack(self):
        if self.level.has_monsters():
            #self.logprint("Monsters are available to sneak attack.")
            unlucky = self.roll(100)
            #self.logprint("unlucky:", unlucky)
            if unlucky < 20:
                #self.logprint("Sneak attack!")
                monster = self.get_monster(self.level.depth)
                won = self.hero.fight(monster)
                if won:
                    msg = self.get_text('rest_attack_won')
                else:
                    msg = self.get_text('rest_attack_lost')
                attribs = self.hero.get_attributes()
                attribs['monster_name'] = monster.name
                msg = msg % attribs
                return msg

    def rest(self):
        # If there are monsters alive on the level, there is a
        # risk of a sneak attack while resting.
        msg = self.sneak_attack()
        if msg:
            return msg
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
        return msg

    def go_deeper(self, levels=1):
        try:
            levels = int(levels)
        except ValueError:
            levels = 1
        if levels > 10:
            levels = 10
        depth = self.hero.go_deeper(levels)
        self.level = self.get_level(depth)
        msg = self.level.text or self.get_text('deeper')
        msg = msg % self.hero.get_attributes()
        return msg

    def fight(self):
        monster = self.get_monster(self.level.depth)
        attribs = self.hero.get_attributes()
        if not monster:
            msg = self.get_text('nomonsters')
            return msg % attribs
        won = self.hero.fight(monster)
        if won:
            msg = self.get_text('killed')
            attribs['slayed'] = self.get_text('slayed')
        else:
            msg = self.get_text('died')
        attribs['monster'] = monster.name
        msg = msg % attribs
        msg = self.firstupper(msg)
        return msg

    def roll(self, sides, times=1):
        total = 0
        for i in range(times):
            total = total + random.randint(1, sides)
        return total

    def show_charsheet(self):
        msg = self.get_text('charsheet')
        return msg % self.hero.get_attributes()

    def firstupper(self, text):
        first = text[0].upper()
        return first + text[1:]


