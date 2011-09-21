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

#import setup_django_version

import os
import logging

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from gaesessions import get_current_session

from decorators import *
import broadcast
from datastorehelpers import *
import goldenweb
from GoldFrame import GoldFrame
from GoldFrame.DataStoreDataHandler import *
from GoldFrame.games.goldquest.GQDSHandler import *

class GameWebHandler(goldenweb.PageHandler):

    def get(self, page):
        self.get_page(page)

    @LogUsageCPU
    def page_heroes(self):
        heroes = DSHero.all().order("-gold").fetch(10)
        gold = get_value('gold')
        kills = get_value('kills')
        hero_count = get_value('heroes')
        level = 0
        high_level_hero = DSHero.all().order("-level").get()
        if high_level_hero:
            level = high_level_hero.level
        values = {
            'heroes': heroes,
            'gold': gold,
            'kills': kills,
            'level': level,
            'hero_count': hero_count,
        }
        self.show_page('heroes', values)


def main():
    application = webapp.WSGIApplication([
            (r'/game/goldquest/(.*)', GameWebHandler),
        ],
        debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
