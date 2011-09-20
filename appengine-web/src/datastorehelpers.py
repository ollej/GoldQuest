#!/usr/bin/env python
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
from decorators import *

class KeyValueInt(db.Model):
    """A simple Key/Value db store."""
    name = db.StringProperty(required=True, default='')
    value = db.IntegerProperty(required=True, default=0)

@LogUsageCPU
def get_value(name):
    """Retrieve the value for a given key."""
    # TODO: Read from memcache first. If not in memcache, read from db and update memcache.
    k = db.Key.from_path('KeyValueInt', name)
    val = db.get(k)
    #val = KeyValueInt.all().filter('name =', name).get()
    if not val:
        val = KeyValueInt(key_name=name, name=name, value=0)
    return val

@LogUsageCPU
def set_value(name, value):
    """Update the value for a given name."""
    # TODO: Update memcache value as well.
    k = db.Key.from_path('KeyValueInt', name)
    val = db.get(k)
    if not val:
        val = KeyValueInt(key_name=name, name=name, value=value)
    else:
        val.value = value
    val.put()

@LogUsageCPU
def inc_value(name, inc=1):
    """Increment the value for a given sharded counter."""
    # TODO: Update memcache value as well.
    def txn(name, inc):
        val = get_value(name)
        val.value += inc
        val.put()
    db.run_in_transaction(txn, name, inc)

