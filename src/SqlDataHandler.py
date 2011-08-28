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

from sqlalchemy import Table, Column, Integer, Boolean, String, MetaData, ForeignKey, Sequence, create_engine
from sqlalchemy.orm import mapper, sessionmaker

from Hero import Hero
from Monster import Monster
from Level import Level

class SqlDataHandler(object):
    def __init__(self, debug):
        self.engine = create_engine('sqlite:///extras/quest.db', echo=debug)
        self.setup_tables()
        self.setup_session()

    def setup_session(self):
        """
        Start a SQLAlchemy db session.

        Saves the session instance in C{self.session}
        """
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def setup_tables(self):
        """
        Defines the tables to use for L{Hero}
        The Metadata instance is saved to C{self.metadata}
        """
        self.metadata = MetaData()
        hero_table = Table('hero', self.metadata,
            Column('id', Integer, Sequence('hero_id_seq'), primary_key=True),
            Column('name', String(100)),
            Column('health', Integer),
            Column('strength', Integer),
            Column('hurt', Integer),
            Column('kills', Integer),
            Column('gold', Integer),
            Column('level', Integer),
            Column('alive', Boolean),
        )
        mapper(Hero, hero_table)
        level_table = Table('level', self.metadata,
            Column('id', Integer, Sequence('hero_id_seq'), primary_key=True),
            Column('depth', Integer),
            Column('killed', Integer),
            Column('looted', Integer),
        )
        mapper(Level, level_table)
        self.metadata.create_all(self.engine)

    def save_data(self, hero, level):
        self.session.add(hero)
        self.session.add(level)
        self.session.commit()

    def get_alive_hero(self):
        hero = self.session.query(Hero).filter_by(alive=True).first()
        return hero

    def get_level(self, lvl):
        level = self.session.query(Level).filter_by(depth=lvl).first()
        return level

    def clear_levels(self):
        # Delete all old Level data.
        self.session.query(Level).delete()

