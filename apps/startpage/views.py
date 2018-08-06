#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Views for the Indivo start page 
Chatzimina Maria
"""

from utils import *
import uuid
import urllib
import urllib2
import requests
import json

from django.utils import simplejson
import xmltodict
import sys
from xml.dom.minidom import parseString

import xml.etree.ElementTree as ET
import psycopg2
import datetime


def start_auth(request):
    """
    begin the oAuth protocol with the server
    
    expects either a record_id or carenet_id parameter,
    now that we are carenet-aware
    """

    # create the client to Indivo
    client = get_indivo_client(request, with_session_token=False)
    
    # do we have a record_id?
    record_id = request.GET.get('record_id', None)
    carenet_id = request.GET.get('carenet_id', None)
    
    # prepare request token parameters
    params = {'oauth_callback':'oob'}
    if record_id:
        params['indivo_record_id'] = record_id
    if carenet_id:
        params['indivo_carenet_id'] = carenet_id

        # request a request token
    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
    request.session['request_token'] = req_token

    return HttpResponseRedirect(client.auth_redirect_url)
   

def after_auth(request):
    """
    after Indivo authorization, exchange the request token for an access token and store it in the web session.
    """
    # get the token and verifier from the URL parameters
    oauth_token, oauth_verifier = request.GET['oauth_token'], request.GET['oauth_verifier']
    
    # retrieve request token stored in the session
    token_in_session = request.session['request_token']
    
    # is this the right token?
    if token_in_session['oauth_token'] != oauth_token:
        return HttpResponseRedirect(reverse(start_auth))
        return HttpResponse("oh oh bad token")
    
    # get the indivo client and use the request token as the token for the exchange
    client = get_indivo_client(request, with_session_token=False)
    client.update_token(token_in_session)
    access_token = client.exchange_token(oauth_verifier)
    request.session['access_token'] = access_token
    if access_token.has_key('xoauth_indivo_record_id'):
        request.session['record_id'] = access_token['xoauth_indivo_record_id']
        if request.session.has_key('carenet_id'):
            del request.session['carenet_id']
    else:
        if request.session.has_key('record_id'):
            del request.session['record_id']
        request.session['carenet_id'] = access_token['xoauth_indivo_carenet_id']
    
    # go to list of problems
    return HttpResponseRedirect(reverse(startpage))


def startpage(request):
    
 
    client = get_indivo_client(request)
    
    in_carenet = request.session.has_key('carenet_id')
    
  
    if not in_carenet:
        record_id = request.session['record_id']
        INDIVO_IP = settings.INDIVO_IP


    return render_template('list')
