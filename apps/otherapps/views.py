#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Views for the Indivo Other app
Chatzimina Maria ICS-FORTH
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
#    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
#    request.session['request_token'] = req_token

    # redirect to the UI server
#    return HttpResponse(request.session['problems_access_token']['oauth_token'])
    ##if not request.session.has_key('problems_access_token'):
        # request a request token
    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
    request.session['request_token'] = req_token

    return HttpResponseRedirect(client.auth_redirect_url)
    if 1==2:
       if datetime.datetime.now() > request.session['problems_time'] + datetime.timedelta(minutes=5):

         req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
         request.session['request_token'] = req_token

         return HttpResponseRedirect(client.auth_redirect_url)
       else:
         access_token=request.session['problems_access_token']
         request.session['access_token'] = access_token
  #    return HttpResponse(access_token)
         if access_token.has_key('xoauth_indivo_record_id'):
           request.session['record_id'] = access_token['xoauth_indivo_record_id']
           if request.session.has_key('carenet_id'):
              del request.session['carenet_id']
         else:
           if request.session.has_key('record_id'):
               del request.session['record_id']
           request.session['carenet_id'] = access_token['xoauth_indivo_carenet_id']

    # go to list of problems
         return HttpResponseRedirect(reverse(otherapps_list))
   

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
    request.session['problems_access_token']=access_token
    request.session['problems_time']=datetime.datetime.now()
#    access_token={}

#    access_token['oauth_token_secret']='vJksj0IFx8RVVf6oSqf2'
#    access_token['oauth_token']='7DVzSfG7SU6ZERg1Zk3I'
#    access_token['xoauth_indivo_record_id']='21241813-9fe8-47c2-ad16-197c204be62e'
    # store stuff in the session
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
    return HttpResponseRedirect(reverse(otherapps_list))

def test_message_send(request):
    """
    testing message send with attachments assumes record-level share
    """
    client = get_indivo_client(request)

    record_id = request.session['record_id']

    message_id = str(uuid.uuid4())
    client.record_send_message(record_id=record_id, message_id=message_id, body={'subject':'testing', 'body':'testing! [a link](http://indivohealth.org/)', 'num_attachments':'1', 'body_type': 'markdown'})

    # an XML doc to send
    problem_xml = render_raw('problem', {'startDate': '2010-04-26T19:37:05.000Z', 'endDate': '2010-04-26T19:37:05.000Z', 'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/', 'code': '37796009', 'code_fullname':'Migraine (disorder)', 'comments': 'I\'ve had a headache waiting for alpha3.', 'diagnosed_by': 'Dr. Ken'}, type='xml')

    client.record_message_attach(record_id=record_id, message_id=message_id, attachment_num="1", body=problem_xml)

    return HttpResponseRedirect(reverse(otherapps_list))
def otherapps_list(request):
    
 
    client = get_indivo_client(request)
    
    in_carenet = request.session.has_key('carenet_id')
    if not in_carenet:
        record_id = request.session['record_id']
        INDIVO_IP = settings.INDIVO_IP
        jsonData = None
        r = " "
        limit=int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        query_params = {
         'limit': limit,
         'offset': offset,
         #'order_by': 'startDate',
         'status': 'active',
        }
        resp, content = client.record(record_id=record_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)


    else:
        record_id = "" #request.session['record_id']
        INDIVO_IP = settings.INDIVO_IP
        jsonData = None
        r = " "

        # get record info
        limit=int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
    #status = request.GET.get('status', 'archived')
        query_params = {
         'limit': limit,
         'offset': offset,
         #'order_by': 'startDate',
         'status': 'active',
        }
        jsonData = None
        carenet_id = request.session['carenet_id']
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)

       # resp2, content2 = client.carenet_document_list(carenet_id=carenet_id)
    record_label = record.attrib['label']
    surl_credentials = client.get_surl_credentials()   


    return render_template('list', {'record_label': record_label,'in_carenet':in_carenet,'record_id':record_id,'surl_credentials':surl_credentials})

