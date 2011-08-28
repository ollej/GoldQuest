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

class Monster(object):
    name = None
    strength = None
    health = None
    level = None

    def __init__(self, level=None, name=None, boss=False):
        if not level:
            level = 1
        self.strength = random.randint(1, level)
        self.health = random.randint(1, level)
        if boss:
            self.strength = self.strength + level
            self.health = self.health + level
        if name:
            self.name = name
        else:
            self.name = self.random_name()

    def injure(self, hurt):
        """
        Injure the monster with hurt points. Returns True if the monster died.
        """
        self.health = self.health - hurt
        if self.health <= 0:
            self.level.kill_monster()
            return True
        else:
            return False

    def random_name(self):
        return random.choice([
            "an orc", "an ogre", "a bunch of goblins", "a giant spider",
            "a cyclops", "a minotaur", "a horde of kobolds",
            "a rattling skeleton", "a large troll", "a moaning zombie",
            "a swarm of vampire bats", "a baby hydra", "a giant monster ant",
            "a slithering lizard", "an angry lion", "three hungry bears",
            "a hell hound", "a pack of rabid dogs", "a werewolf",
            "an ice demon", "a fire wraith", "a groaning ghoul",
            "two goblins", "a three-headed hyena", "a giant monster worm",
            "a slobbering were-pig"
        ])

