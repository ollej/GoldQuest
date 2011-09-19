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

class Assassin(object):
    id = 0
    name = ''
    health = None
    strength = None
    hurt = None
    kills = None
    assassinations = None
    feathers = None
    towers = None
    alive = None
    userid = None

    def __init__(self, texts=None, userid=None):
        self.hurt = 0
        self.kills = 0
        self.assassinations = 0
        self.feathers = 0
        self.towers = 0
        self.alive = True
        self.userid = userid
        self._texts = texts

    def reroll(self, name=None):
        self.health = self.roll(20, 5)
        self.strength = self.roll(20, 5)
        self.hurt = 0
        self.kills = 0
        self.assassinations = 0
        self.feathers = 0
        self.towers = 0
        self.alive = True
        if name:
            self.name = name
        else:
            self.name = self.random_name()

    def collect(self):
        self.feathers += 1
        return self.feathers

    def injure(self, hurt):
        self.hurt = self.hurt + hurt
        if self.hurt > self.health:
            self.alive = False
        return (self.alive, self.hurt)

    def fight(self, target):
        hurt_in_fight = 0
        while target.health >= 0 and self.hurt < self.health:
            hit = self.roll(self.strength)
            killed = target.injure(hit)
            if not killed:
                target_hit = self.roll(target.strength)
                hurt_in_fight += target_hit
                self.injure(target_hit)
        if self.hurt >= self.health:
            self.alive = False
        else:
            if target.boss:
                self.assassinations += 1
            else:
                self.kills += 1
        return (self.alive, hurt_in_fight)

    def heal(self):
        if self.hurt > 0:
            heal = self.roll(10)
            if heal > self.hurt:
                heal = self.hurt
            self.hurt = self.hurt - heal
            return heal
        return 0

    def climb(self):
        self.towers += 1
        return self.towers

    def ding(self, strength):
        chance = strength - self.strength
        luck = self.roll(100)
        logging.info('target strength: %d assassin strength: %d ding chance: %d luck: %d', strength, self.strength, chance, luck)
        if luck < chance:
            gain_strength = self.roll(4)
            gain_health = self.roll(4)
            logging.info('strength gain: %d health gain: %d', gain_strength, gain_health)
            self.strength += gain_strength
            self.health += gain_health
            return True
        return False

    def roll(self, sides, times=1):
        total = 0
        for i in range(times):
            total += random.randint(1, sides)
        return total

    def random_name(self):
        name = random.choice(self._texts['name'])
        epithet = random.choice(self._texts['epithet'])
        logging.info("Name: %s Epithet: %s", name, epithet)
        values = { 'name': name }
        full_name = epithet % values
        return full_name

    def get_attributes(self):
        attribs = dict()
        for k, v in self.__dict__.items():
            if k[0:1] != '_':
                attribs[k] = v
        attribs['status'] = ""
        if not self.alive:
            attribs['status'] = " (Deceased)"
        return attribs

    def get_charsheet(self):
        msg = "%(name)s%(status)s - Strength: %(strength)d Health: %(health)d Hurt: %(hurt)d Assassinations: %(assassinations)d Feathers: %(feathers)d Towers: %(towers)d"
        msg = msg % self.get_attributes()
        return msg

