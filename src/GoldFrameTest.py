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

import GoldFrame
import unittest
from minimock import *
import random
import yaml

class GamePluginTest(unittest.TestCase):
    def setUp(self):
        self.game = GoldFrame.GamePlugin(None)
        self.game.action_test = self._action_test

    def tearDown(self):
        restore()

    def _action_test(self, arguments):
        msg = "."
        if arguments is not None:
            msg = " with arguments:"
            for k, v in arguments.iteritems():
                msg += " %s=%s" % (k, v)
        return "Test command called%s" % msg

    def mock_load_file(self, d):
        """
        Setup all mocks needed for load_file()
        """
        f = Mock("file", tracker=None)
        mock("open", returns=f, tracker=None)
        mock("yaml.load", returns=d, tracker=None)

    def test_roll_10(self):
        """
        Test roll one 10-sided die.
        """
        mock('random.randint', returns=10, tracker=None)
        self.assertEqual(self.game.roll(10), 10)

    def test_roll_10_twice(self):
        """
        Test roll on 10-sided die twice.
        """
        mock('random.randint', returns=10, tracker=None)
        self.assertEqual(self.game.roll(10, 2), 20)

    def test_roll_100(self):
        """
        Test roll one 100-sided die.
        """
        mock('random.randint', returns=100, tracker=None)
        self.assertEqual(self.game.roll(100), 100)

    def test_roll_100_twice(self):
        """
        Test roll one 100-sided die twice.
        """
        mock('random.randint', returns=100, tracker=None)
        self.assertEqual(self.game.roll(100, 2), 200)

    def test_firstupper(self):
        """
        firstupper() should return string with first letter in upper case.
        """
        self.assertEqual(self.game.firstupper("hello"), "Hello")

    def test_firstupper_capitalized(self):
        """
        firstupper() shouldn't change string if first letter is already in uppercase.
        """
        self.assertEqual(self.game.firstupper("Hello"), "Hello")

    def test_firstupper_allupper(self):
        """
        firstupper() shouldn't change any other letters than the first.
        """
        self.assertEqual(self.game.firstupper("hELLo"), "HELLo")

    def test_play(self):
        """
        The play() method should not fail if command doesn't exist.
        """
        self.assertEqual(self.game.play("foo"), None)

    def test_play_testcommand(self):
        """
        The play() method should call a method with name action_<command>
        """
        self.assertEqual(self.game.play("test"), "Test command called.")

    def test_play_testcommand_witharguments(self):
        """
        The play() method should call a method with name action_<command>
        """
        ret = self.game.play("test", False, {'foo': 'bar', 'baz': 'qux'})
        self.assertEqual(ret, "Test command called with arguments: foo=bar baz=qux")

    def test_play_testcommand_asdict(self):
        """
        The play() method should call a method with name action_<command>
        """
        ret = self.game.play("test", True)
        expected = {
            'message': "Test command called.",
            'success': 1,
        }
        self.assertEqual(ret, expected)

    def test_get_metadata(self):
        """
        Test return of metadata.
        """
        md = self.game.get_metadata()
        self.assertEqual(md, self.game.metadata)

    def test_load_file(self):
        """
        Test loading text file.
        """
        d = { 'foo': 'bar' }
        self.mock_load_file(d)
        self.assertEqual(self.game.load_file('foo'), d)

    def test_read_texts(self):
        """
        Test reading of game texts.
        """
        d = { 'foo': 'bar' }
        self.mock_load_file(d)
        self.assertEquals(self.game.read_texts('foo'), d)

if __name__ == "__main__":
    unittest.main()

