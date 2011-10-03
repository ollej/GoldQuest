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

class DataStoreDataHandler(object):
    def __init__(self, cfg):
        self._cfg = cfg

    def create_object(self, obj, ds, Class):
        if not ds:
            ds = Class()
        obj._ds = ds
        props = ds.properties()
        for attr in props:
            if attr[0] != '_':
                value = getattr(ds, attr)
                if value is None:
                    if isinstance(props[attr], db.IntegerProperty):
                        value = 0
                    elif isinstance(props[attr], db.StringProerty):
                        value = ""
                setattr(obj, attr, value)
        return obj

    def prepare_object(self, obj, Class):
        if not hasattr(obj, '_ds') or not obj._ds:
            obj._ds = Class()
        for attr in obj._ds.properties():
            value = getattr(obj, attr)
            if attr[0] != '_':
                setattr(obj._ds, attr, value)
        return obj

