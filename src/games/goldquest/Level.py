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

from Monster import Monster

class Level(object):
    depth = None
    killed = None
    looted = None
    _boss = None
    _text = None

    def __init__(self, depth=None):
        self.killed = 0
        self.looted = 0
        if depth:
            self.depth = depth
        else:
            self.depth = 1

    def get_monster(self, name):
        if self.killed == self.depth - 1:
            boss = True
            if self._boss:
                name = self._boss
        else:
            boss = False
        if self.has_monsters():
            monster = Monster(self.depth, name, boss)
            monster.level = self
            return monster

    def get_loot(self):
        loot = 0
        if self.can_loot():
            self.looted = self.looted + 1
            luck = random.randint(1, 100)
            if luck > 20:
                loot = random.randint(1, self.depth)
            elif luck < 5:
                loot = 0 - luck
        return loot

    def kill_monster(self):
        if self.has_monsters():
            self.killed = self.killed + 1
            return True
        return False

    def has_monsters(self):
        if self.killed < self.depth:
            return True
        return False

    def can_loot(self):
        if self.looted < self.killed:
            return True
        return False

