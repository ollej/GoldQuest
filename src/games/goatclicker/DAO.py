#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The MIT License

Copyright (c) 2011 Mikael Holmström

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

from GoldFrame.DataStoreDataHandler import DataStoreDataHandler

class KeyValue(db.Model):
    value = db.StringProperty()

class DSGoat(db.Model):
    name = db.StringProperty()
    clicks = db.IntegerProperty()
    time = db.FloatProperty()

class DAO(DataStoreDataHandler):
    def save_goat(self, userid, goat):
        dsgoat = DSGoat(key_name = userid)
        dsgoat.name   = goat.name
        dsgoat.clicks = goat.clicks
        dsgoat.time   = goat.time
        dsgoat.put()

    def load_goat(self, userid, goat):
        dsgoat = DSGoat.get_by_key_name(userid)
        if dsgoat:
            goat.name   = dsgoat.name
            goat.clicks = dsgoat.clicks
            goat.time   = dsgoat.time

        return goat

    def get_highscores(self, limit=10):
        query = DSGoat.all()
        query.order('-clicks')
        results = query.fetch(limit)
        return map(lambda goat: { 'name': goat.name, 'clicks': goat.clicks }, results)

    def set_value(self, name, value):
        kv = KeyValue(key_name = name)
        kv.value = value
        kv.put()

    def get_value(self, name):
        kv = KeyValue.get_by_key_name(name)
        if kv: return kv.value
        else: return ''

    def clear(self):
        db.delete(KeyValue.all())
        db.delete(DSGoat.all())

