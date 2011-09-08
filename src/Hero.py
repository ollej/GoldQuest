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

class Hero(object):
    id = 0
    name = ''
    health = None
    strength = None
    hurt = None
    kills = None
    gold = None
    level = None
    alive = None

    def __init__(self, texts=None):
        self.hurt = 0
        self.kills = 0
        self.gold = 0
        self.level = 1
        self.alive = True
        self._texts = texts

    def reroll(self, name=None):
        self.health = self.roll(20, 5)
        self.strength = self.roll(20, 5)
        self.hurt = 0
        self.kills = 0
        self.gold = 0
        self.level = 1
        self.alive = True
        if name:
            self.name = name
        else:
            self.name = self.random_name()

    def search_treasure(self):
        luck = self.roll(100)
        if luck > 50:
            found_gold = self.roll(self.level)
            self.gold = self.gold + found_gold
            return found_gold
        return 0

    def injure(self, hurt):
        self.hurt = self.hurt + hurt
        if self.hurt > self.health:
            self.alive = False

    def fight(self, monster):
        #print("Monster:", monster.health, monster.strength)
        while monster.health >= 0 and self.hurt <= self.health:
            hit = self.roll(self.strength)
            killed = monster.injure(hit)
            #print("Hit:", hit, "Monster Health:", monster.health)
            if not killed:
                monster_hit = self.roll(monster.strength)
                self.injure(monster_hit)
                #print("Monster Hits:", monster_hit, "Hero Hurt:", self.hurt)
        if self.hurt > self.health:
            self.alive = False
        else:
            self.kills = self.kills + 1
        return self.alive

    def rest(self):
        if self.hurt > 0:
            heal = self.roll(10)
            if heal > self.hurt:
                heal = self.hurt
            self.hurt = self.hurt - heal
            return heal
        return 0

    def go_deeper(self, depth=None):
        if not depth:
            depth = 1
        self.level = self.level + depth
        return self.level

    def roll(self, sides, times=1):
        total = 0
        for i in range(times):
            total = total + random.randint(1, sides)
        return total

    def random_name(self):
        #name = random.choice(['Conan', 'Canon', 'Hercules', 'Robin', 'Dante', 'Legolas', 'Buffy', 'Xena'])
        #epithet = random.choice(['Barbarian', 'Invincible', 'Mighty', 'Hairy', 'Bastard', 'Slayer'])
        #return '%s the %s' % (name, epithet)
        name = random.choice(self._texts['name'])
        epithet = random.choice(self._texts['epithet'])
        logging.info("Name: %s Epithet: %s", name, epithet)
        values = { 'name': name }
        full_name = epithet % values
        return full_name

    def get_attributes(self):
        #logging.info(self.__dict__)
        #attribs = self.__dict__
        attribs = dict()
        for k, v in self.__dict__.items():
            #logging.info('%s = %s' % (k, v))
            #print 'k', k, 'v', v
            if k[0:1] != '_':
                attribs[k] = v
        attribs['status'] = ""
        if not self.alive:
            attribs['status'] = " (Deceased)"
        #for k, v in attribs.items():
        #    print k, v
        return attribs
        #return self.__dict__

    def get_charsheet(self):
        msg = "%(name)s%(status)s - Strength: %(strength)d Health: %(health)d Hurt: %(hurt)d Kills: %(kills)d Gold: %(gold)d Level: %(level)d"
        msg = msg % self.get_attributes()
        return msg

