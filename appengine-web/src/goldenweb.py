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

import setup_django_version

import os
import logging
import simplejson
import Py2XML
import httpheader
from httpheader import ParseError

from django.conf import settings
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from django.template import TemplateDoesNotExist

from decorators import *

DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Development')

class PageHandler(webapp.RequestHandler):
    """
    Default page handler, supporting html templates, layouts, output formats etc.
    """

    _basepath = os.path.dirname(__file__)

    @LogUsageCPU
    def get_template(self, page, values, layout='default', basepath=None):
        """
        TODO: use django template include.
        """
        page = "%s.html" % page
        path = ''
        if not values:
            values = {}
        if basepath:
            path = os.path.join(basepath, 'views', page)
        if not basepath or not os.path.exists(path):
            path = os.path.join(self._basepath, 'views', page)
        if layout:
            layout = os.path.join('layouts', '%s.html' % layout)
            values['layout'] = layout
        logging.info('template pathname: %s layout: %s', path, layout)
        template_file = open(path) 
        # TODO: cache compiled template
        compiled_template = template.Template(template_file.read()) 
        template_file.close() 
        content = compiled_template.render(template.Context(values))
        return content

    def parse_pagename(self, page):
        (pagename, ext) = os.path.splitext(page)
        logging.debug("page: %s pagename: %s ext: %s" % (page, pagename, ext))
        # TODO: filter unwanted characters
        return (pagename, ext)

    @LogUsageCPU
    def show_page(self, page, template_values=None, layout='default', default_format=None, basepath=None):
        """
        Select output format based on Accept headers.
        """
        #logging.debug(template_values)
        accept = None
        acceptparams = None
        try:
            accept = self.request.headers['Accept']
        except KeyError, ke:
            logging.debug('Request contained no Accept header.')
        logging.debug('Accept content-type: %s' % accept)
        #(mime, parms, qval, accept_parms) = httpheader.parse_accept_header(accept)
        try:
            if accept:
                acceptparams = httpheader.parse_accept_header(accept)
        except ParseError, e:
            logging.error('Error parsing HTTP Accept header: %s', e)
        logging.debug(acceptparams)
        #logging.debug('mime: %s, parms: %s, qval: %s, accept_parms: %s' % (mime, parms, qval, accept_parms))
        format = self.request.get("format")
        if not format and default_format:
            format = default_format
        logging.debug('selected format: %s' % format)
        if format == 'html' or ((not acceptparams or not accept or accept == '*/*' or httpheader.acceptable_content_type(accept, 'text/html')) and not format):
            self.output_html(page, template_values=template_values, layout=layout, basepath=basepath)
        elif format == 'json' or httpheader.acceptable_content_type(accept, 'application/json'):
            self.output_json(template_values)
        elif format == 'xml' or (httpheader.acceptable_content_type(accept, 'application/xml') and not format):
            self.output_xml(template_values)
        elif format == 'text' or httpheader.acceptable_content_type(accept, 'text/plain'):
            #elif httpheader.acceptable_content_type(accept, 'text/plain'):
            if isinstance(template_values, basestring):
                self.output_text(template_values)
            else:
                try:
                    self.output_text(template_values['message'])
                except KeyError, e:
                    self.output_text(str(template_values))
        else:
            logging.debug('Defaulting output to html.')
            self.output_html(page, template_values, layout=layout, basepath=basepath)

    @LogUsageCPU
    def output_json(self, template_values=None):
        self.response.headers.add_header('Content-Type', 'application/json', charset='utf-8')
        jsondata = simplejson.dumps(template_values)
        self.response.out.write(jsondata)

    @LogUsageCPU
    def output_xml(self, template_values=None):
        self.response.headers.add_header('Content-Type', 'application/xml', charset='utf-8')
        serializer = Py2XML.Py2XML()
        values = { 'response': template_values }
        xmldata = serializer.parse(values)
        self.response.out.write(xmldata)

    @LogUsageCPU
    def output_text(self, content):
        self.response.headers.add_header('Content-Type', 'text/plain', charset='utf-8')
        self.response.out.write(content)

    @LogUsageCPU
    def output_html(self, page, template_values=None, layout='default', basepath=None):
        try:
            content = self.get_template(page, template_values, layout, basepath=basepath)
            self.response.out.write(content)
        except TemplateDoesNotExist:
            self.response.set_status(404)

    @LogUsageCPU
    def get_page(self, page):
        template_values = {}
        (pagename, ext) = self.parse_pagename(page)
        if not pagename or pagename == 'index':
            self.show_page('index')
        else:
            func_name = 'page_%s' % pagename
            logging.debug('loading page: %s' % func_name)
            try:
                func = getattr(self, func_name)
            except AttributeError:
                self.show_page(pagename, None, 'default')
            else:
                func()

