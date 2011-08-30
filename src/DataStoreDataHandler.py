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

from Hero import Hero
from Level import Level

class DSHero(db.Model):
    name = db.StringProperty()
    health = db.IntegerProperty()
    strength = db.IntegerProperty()
    hurt = db.IntegerProperty()
    kills = db.IntegerProperty()
    gold = db.IntegerProperty()
    level = db.IntegerProperty()
    alive = db.BooleanProperty()

class DSLevel(db.Model):
    depth = db.IntegerProperty()
    killed = db.IntegerProperty()
    looted = db.IntegerProperty()

class DataStoreDataHandler(object):
    def __init__(self, debug):
        pass

    def create_object(self, obj, ds, Class):
        if not ds:
            ds = Class()
        obj._ds = ds
        #for attr, v in obj.__dict__.iteritems():
        for attr in ds.properties():
            if attr[0] != '_':
                value = getattr(ds, attr)
                #logging.info("setting value - attr: %s value: %s" % (attr, value))
                setattr(obj, attr, value)
        return obj

    def prepare_object(self, obj, Class):
        if not hasattr(obj, '_ds') or not obj._ds:
            obj._ds = Class()
        #for attr, value in obj.__dict__.iteritems():
        for attr in obj._ds.properties():
            value = getattr(obj, attr)
            #logging.info("attr: %s value: %s" % (attr, value))
            if attr[0] != '_': # and hasattr(obj.ds, attr):
                setattr(obj._ds, attr, value)
        return obj

    def save_data(self, hero, level):
        hero = self.prepare_object(hero, DSHero)
        hero._ds.put()
        level = self.prepare_object(level, DSLevel)
        level._ds.put()

    def get_alive_hero(self):
        query = DSHero.all()
        query.filter('alive =', True)
        herods = query.get()
        if herods:
            return self.create_object(Hero(), herods, DSHero)

    def get_level(self, lvl):
        query = DSLevel.all()
        query.filter('depth =', lvl)
        levelds = query.get()
        if levelds:
            #logging.info('Read level %d from database.' % lvl)
            return self.create_object(Level(), levelds, DSLevel)
        #logging.info('No saved level at %d' % lvl)

    def clear_levels(self):
        # Delete all old Level data.
        db.delete(DSLevel.all())

