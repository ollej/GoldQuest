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
import simplejson
import uuid
from datetime import datetime

from google.appengine.api import channel
from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext import deferred

from gaesessions import get_current_session

from decorators import *

def broadcast(message, skip_clients=None):
    """
    Broadcast message to all connected clients.
    """
    channels = simplejson.loads(memcache.get('channels') or '{}')
    encoded_message = simplejson.dumps(message)
    for channel_id in channels.iterkeys():
        if not skip_clients or channel_id not in skip_clients:
            channel.send_message(channel_id, encoded_message)

class ChannelUpdater(object):
    _instance = None
    _session = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ChannelUpdater, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        #self._channels = self.get_channels()
        self._session = get_current_session()

    @LogUsageCPU
    def get_channels(self):
        return simplejson.loads(memcache.get('channels') or '{}')

    def set_channels(self, channels):
        """
        Set the channel list in memcache to channels.
        Note: Not safe, will overwrite old value without checking.
        """
        memcache.set('channels', simplejson.dumps(channels))

    def create_id(self):
        return uuid.uuid4().hex

    def create_channel(self, client_id=None):
        if not client_id:
            client_id = self.create_id()
        token = channel.create_channel(client_id)
        return (token, client_id)

    def send_update(self, client_id, message):
        """
        Send a message as JSON to the client identified with client_id.
        """
        message = simplejson.dumps(message)
        logging.debug('Sending message to client: %s - %s' % (client_id, message))
        channel.send_message(client_id, message)

    def send_all_update_now(self, message):
        """
        Send message to all connected clients immediately.
        """
        channels = self.get_channels()
        for client_id in channels.iterkeys():
            if self._session.has_key('channel_client_id') and client_id != self._session['channel_client_id']:
                self.send_update(client_id, message)

    def send_all_update(self, message):
        """
        Send a message to all connected clients in a deferred background task.
        """
        skip_client = None
        if self._session.has_key('channel_client_id'):
            skip_client = [self._session['channel_client_id']]
        deferred.defer(broadcast, message, skip_client)

    def connect(self, client_id):
        """
        Add client_id to list of active clients.
        """
        mc = memcache.Client()
        counter = 0
        while True:
            channels = simplejson.loads(mc.gets('channels') or '{}')
            if hasattr(channels, client_id):
                break
            else:
                logging.debug("Adding new client: %s" % client_id)
                channels[client_id] = str(datetime.now())
                if mc.cas('channels', simplejson.dumps(channels)):
                    logging.debug('Set new clientid in memcache: %s', client_id)
                    break
                elif counter > 2:
                    mc.add('channels', channels)
                    break
                else:
                    counter += 1



    def disconnect(self, client_id):
        """
        Remove client_id from list of active clients.
        """
        mc = memcache.Client()
        counter = 0
        while True:
            channels = simplejson.loads(mc.gets('channels') or '{}')
            if hasattr(channels, client_id):
                del channels[client_id]
                if mc.cas('channels', simplejson.dumps(channels)):
                    logging.debug('Removed clientid from memcache: %s', client_id)
                    break
                elif counter > 2:
                    mc.add('channels', channels)
                    break
                else:
                    counter += 1
            else:
                break

class ChannelHandler(webapp.RequestHandler):
    _channel = None

    def __init__(self):
        self._channel = ChannelUpdater()

    def post(self, action):
        client_id = self.request.get('from')
        logging.debug('Channel client %s %s' % (client_id, action))
        if action == 'connected':
            self._channel.connect(client_id)
        elif action == 'disconnected':
            self._channel.disconnect(client_id)
