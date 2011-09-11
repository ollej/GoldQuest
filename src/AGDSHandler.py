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

from google.appengine.ext import db

import logging

from DataStoreDataHandler import DataStoreDataHandler
from Assassin import Assassin

class DSAssassin(db.Model):
    name = db.StringProperty()
    health = db.IntegerProperty()
    strength = db.IntegerProperty()
    hurt = db.IntegerProperty()
    assassinations = db.IntegerProperty()
    feathers = db.IntegerProperty()
    towers = db.IntegerProperty()
    alive = db.BooleanProperty()

    def get_current_health(self):
        return (self.health - self.hurt)

    current_health = property(get_current_health)

class AGDSHandler(DataStoreDataHandler):
    def save_data(self, assassin):
        assassin = self.prepare_object(assassin, DSAssassin)
        assassin._ds.put()

    def get_alive_assassin(self):
        query = DSAssassin.all()
        query.filter('alive =', True)
        assassinds = query.get()
        if assassinds:
            return self.create_object(Assassin(), assassinds, DSAssassin)

