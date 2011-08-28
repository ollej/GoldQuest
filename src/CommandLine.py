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

import ConfigParser
import cmd

import GoldQuest

class CommandLine(cmd.Cmd):
    prompt = 'GoldQuest> '
    intro = "Welcome to GoldQuest!"
    game = None

    def preloop(self):
        cfg = ConfigParser.ConfigParser()
        cfg.read('../config.ini')
        self.game = GoldQuest.GoldQuest(cfg)

    def default(self, line):
        ret = self.game.play(line)
        if ret:
            print ret

    def do_fight(self, line):
        "Find a new monster and fight it to the death!"
        print self.game.play('fight')

    def do_charsheet(self, line):
        "Show the character sheet for the current hero."
        print self.game.play('charsheet')

    def do_reroll(self, line):
        "Reroll a new hero if the village doesn't have one already."
        print self.game.play('reroll')

    def do_rest(self, line):
        "Makes the hero rest for a while to regain hurt."
        print self.game.play('rest')

    def do_loot(self, line):
        "The hero will search for loot in the hope to find gold."
        print self.game.play('loot')

    def do_deeper(self, line):
        "Tells the hero to go deeper into the dungeon."
        if line:
            cmd = 'deeper %s' % line
        else:
            cmd = 'deeper'
        print self.game.play(cmd)

    def do_quit(self, line):
        "Quit Game"
        print "A strange game. The only winning move is not to play."
        return True

if __name__ == '__main__':
    CommandLine().cmdloop()

