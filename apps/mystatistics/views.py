#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Views for the myStatistics
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
#    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
#    request.session['request_token'] = req_token
    
    # redirect to the UI server
#    return HttpResponse(request.session['mystatistics_access_token']['oauth_token'])
    ##if not request.session.has_key('mystatistics_access_token'):
        # request a request token
    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
    request.session['request_token'] = req_token

    return HttpResponseRedirect(client.auth_redirect_url)
    if 1==2:
       if datetime.datetime.now() > request.session['mystatistics_time'] + datetime.timedelta(minutes=5):

         req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
         request.session['request_token'] = req_token
  
         return HttpResponseRedirect(client.auth_redirect_url)
       else:
         access_token=request.session['mystatistics_access_token']
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

    # go to list of mystatistics
         return HttpResponseRedirect(reverse(mystatistics_list))
   

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
    request.session['mystatistics_access_token']=access_token
    request.session['mystatistics_time']=datetime.datetime.now()
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
    
    # go to list of mystatistics
    return HttpResponseRedirect(reverse(mystatistics_list))

def mystatistics_list(request):
    
 
    client = get_indivo_client(request)
    
    in_carenet = request.session.has_key('carenet_id')
    
  
    if not in_carenet:
        record_id = request.session['record_id']
        INDIVO_IP = settings.INDIVO_IP
        jsonData = None
        r = " "
        

       # try:
       #     r = requests.get(INDIVO_IP+"/ProfilingServer/getPatientResults?clinicianKey=clinician12.&patientId="+record_id,timeout=20)
       #     r.text
       #     jsonData = json.loads(r.text)
       # except Exception,e:
       #     pass
       # except requests.exceptions.ConnectionError as e:    # This is the correct syntax
       #     pass
       # charCount = {}
       # if  r != " ":
       #   text = r.text
       #   for char in r.text:
       #     charCount[char] = charCount.get(char, 0) + 1
       #   characters = len(text) - text.count(' ')
       #   if characters < 60:
       #      jsonData = None
    
    #status = request.GET.get('status', 'void')
        limit=int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
    #status = request.GET.get('status', 'archived')
        query_params = {
         'limit': limit,
         'offset': offset,
         #'order_by': 'startDate',
         'status': 'active',
        }
        # get record info
        record_id = request.session['record_id']
        resp, content = client.record(record_id=record_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)


        # read mystatistics
        resp, content = client.generic_list(record_id=record_id, data_model="Problem", body=query_params)
        resp2, content2 = client.generic_list(record_id=record_id, data_model="Measurements", body=query_params) 
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading mystatistics: %s"%content)
        content = content.encode('latin-1')
        
        probs = simplejson.loads(content)

	if resp2['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading mystatistics: %s"%content2)
        content2 = content2.encode('latin-1')
        measurements = simplejson.loads(content2)


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
       # resp2, content2 = client.carenet_document_list(carenet_id=carenet_id)
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)
        #record2 = parse_xml(content2)
        # read mystatistics from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Problem", body=query_params)
 
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading mystatistics from carenet: %s"%content)
        probs = simplejson.loads(content)
	resp2, content2 = client.carenet_generic_list(carenet_id=carenet_id, data_model="Measurements", body=query_params)
        if resp2['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content2)
        measurements = simplejson.loads(content2)


#    probs = probs.decode('iso-8859-1').encode('utf8')        
    probs = map(process_problem, probs)

    measurements = map(process_problem, measurements)
    probs = json.dumps(probs)         
    probs = probs.replace('\\"', '')
    probs = probs.replace("\\'", "")
    measurements = json.dumps(measurements)

    return render_template('list', {'problems': probs, 'in_carenet':in_carenet,'measurements':measurements})
