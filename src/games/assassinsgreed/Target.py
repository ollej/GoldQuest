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

class Target(object):
    name = None
    strength = None
    health = None
    level = None
    boss = None
    _original_health = None

    def __init__(self, level=None, name=None, boss=False):
        if not level:
            level = 1
        self.strength = random.randint(1, level)
        self.health = random.randint(1, level)
        self._original_health = self.health
        self.boss = boss
        if boss:
            self.strength = self.strength + level
            self.health = self.health + level
        if name:
            self.name = name
        else:
            self.name = self.random_name()

    def injure(self, hurt):
        """
        Injure the target with hurt points. Returns True if the target died.
        """
        self.health = self.health - hurt
        if self.health <= 0:
            return True
        else:
            return False

    def drop_loot(self):
        gold = 0
        max_gold = int(self._original_health / 10)
        if max_gold > 0:
            gold = random.randint(1, max_gold)
        return gold
