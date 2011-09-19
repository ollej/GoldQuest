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

def broadcast(message, list='channels', skip_clients=None):
    """
    Broadcast message to all connected clients.
    """
    channels = simplejson.loads(memcache.get(list) or '{}')
    encoded_message = simplejson.dumps(message)
    for channel_id in channels.iterkeys():
        if not skip_clients or channel_id not in skip_clients:
            channel.send_message(channel_id, encoded_message)

class ChannelUpdater(object):
    _instance = None
    _session = None
    _broadcast_id = None
    _listname = 'channels'

    def __init__(self, id=None):
        #self._channels = self.get_channels()
        self._session = get_current_session()

        if id:
            self._listname = 'channels_%s' % id
            self._broadcast_id = id

    @LogUsageCPU
    def get_channels(self):
        return simplejson.loads(memcache.get(self._listname) or '{}')

    def set_channels(self, channels):
        """
        Set the channel list in memcache to channels.
        Note: Not safe, will overwrite old value without checking.
        """
        memcache.set(self._listname, simplejson.dumps(channels))

    def create_id(self):
        return uuid.uuid4().hex

    def create_channel(self, client_id=None):
        if not client_id:
            client_id = self.create_id()
        token = channel.create_channel(client_id)
        self.connect(client_id, self._broadcast_id)
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
        key = 'channel_client_id'
        if self._broadcast_id:
            key = '%s_channel_client_id' % self._broadcast_id
        if self._session.has_key(key):
            skip_client = [self._session[key]]
        deferred.defer(broadcast, message, self._listname, skip_client)

    def update_memcache_key(self, list, key, value=None):
        """
        Update key/value in memcached dict list or add if it doesn't exist.
        If value is not truthy, the key will be removed.
        """
        mc = memcache.Client()
        counter = 0
        while True:
            channels = simplejson.loads(mc.gets(list) or '{}')
            if value and hasattr(channels, key):
                # No need to add key if client_id already exists.
                break
            elif not value and not hasattr(channels, key):
                # No need to remove key if client_id doesn't exist.
                break
            else:
                logging.debug("Adding new client: %s" % key)
                if value:
                    channels[key] = value
                else:
                    del channels[key]
                channelsjson = simplejson.dumps(channels)
                if mc.cas(list, channelsjson):
                    logging.debug('Set new clientid in memcache: %s', key)
                    break
                elif counter > 2:
                    mc.add(list, channelsjson)
                    break
                else:
                    counter += 1

    def get_listname(self, client_id):
        """
        Returns name of broadcast channel client_id is in.
        """
        channels = simplejson.loads(memcache.gets('clients') or '{}')
        if hasattr(channels, client_id):
            return channels[client_id]

    def connect(self, client_id, id=None):
        """
        Add client_id to list of active clients.
        """
        self.update_memcache_key(self._listname, client_id, str(datetime.now()))
        if id:
            self.update_memcache_key('clients', client_id, id)

    def disconnect(self, client_id):
        """
        Remove client_id from list of active clients.
        """
        listname = self.get_listname(client_id)
        if listname:
            self.update_memcache_key(listname, client_id)
            self.update_memcache_key('clients', client_id)

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

