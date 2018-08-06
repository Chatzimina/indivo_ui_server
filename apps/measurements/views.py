"""
Views for the measurements app
Chatzimina Maria
"""

from utils import *
import uuid
import requests
import urllib2
import urllib
from urllib2 import HTTPError
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

    ##if not request.session.has_key('measurements_access_token'):
        # request a request token
    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
    request.session['request_token'] = req_token

    return HttpResponseRedirect(client.auth_redirect_url)
    if 1==2:
       if datetime.datetime.now() > request.session['measurements_time'] + datetime.timedelta(minutes=5):

         req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
         request.session['request_token'] = req_token

         return HttpResponseRedirect(client.auth_redirect_url)
       else:
         access_token=request.session['measurements_access_token']
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
         return HttpResponseRedirect(reverse(measurement_list))



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
        return HttpResponse("oh oh bad token")

    # get the indivo client and use the request token as the token for the exchange
    client = get_indivo_client(request, with_session_token=False)
    client.update_token(token_in_session)
    access_token = client.exchange_token(oauth_verifier)
    request.session['measurements_access_token']=access_token
    request.session['measurements_time']=datetime.datetime.now()
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
    return HttpResponseRedirect(reverse(measurement_list))


def test_message_send(request):
    """
    testing message send with attachments assumes record-level share
    """
    client = get_indivo_client(request)

    record_id = request.session['record_id']

    message_id = str(uuid.uuid4())
    client.record_send_message(record_id=record_id, message_id=message_id, body={'subject':'testing', 'body':'testing! [a link](http://indivohealth.org/)', 'num_attachments':'1', 'body_type': 'markdown'})

    # an XML doc to send
    problem_xml = render_raw('measurement', {'date_onset': '2010-04-26T19:37:05.000Z', 'date_resolution': '2010-04-26T19:37:05.000Z', 'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/', 'code': '37796009', 'code_fullname':'Migraine (disorder)', 'comments': 'I\'ve had a headache waiting for alpha3.', 'diagnosed_by': 'Dr. Ken'}, type='xml')

    client.record_message_attach(record_id=record_id, message_id=message_id, attachment_num="1", body=problem_xml)

    return HttpResponseRedirect(reverse(measurement_list))

def measurement_list(request):
    limit=int(request.GET.get('limit', 100))
    offset = int(request.GET.get('offset', 0))
    query_params = {
           'limit': limit,
           'offset': offset, 
           'status': 'active',
           }
    # Get the webserviced information
    jsonData = " " 
    client = get_indivo_client(request)
    #s = self.request.get('s') 
    in_carenet = request.session.has_key('carenet_id')
    if not in_carenet:
        # get record info
        record_id = request.session['record_id']
   
        INDIVO_IP = settings.INDIVO_IP
        jsonData = " "
        r = " "
#        try:
#           r = requests.get(INDIVO_IP+"/ProfilingServer/getPatientResults?clinicianKey=clinician12.&patientId="+record_id,timeout=20)
#           r.text
#           jsonData = json.loads(r.text)
#        except Exception,e:
#           pass
#        except requests.exceptions.ConnectionError as e:    # This is the correct syntax
#           pass
#        charCount = {}
#        if r != " ":

 #        text = r.text
 #        for char in r.text:
 #           charCount[char] = charCount.get(char, 0) + 1
 #        characters = len(text) - text.count(' ')
 #        if characters < 60:
 #          jsonData = " "
        resp, content = client.record(record_id=record_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)
        
        # read problems
        resp, content = client.generic_list(record_id=record_id, data_model="Measurements", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems: %s"%content)
        measurements = simplejson.loads(content)

    else:
        # get record info
        record_id = ""
        carenet_id = request.session['carenet_id']
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)

        # read problems from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Measurements", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content)
        measurements = simplejson.loads(content)
        
    measurements = map(process_problem, measurements)
    measurements2 = json.dumps(measurements)
    record_label = record.attrib['label']
    num_measurements = len(measurements)
    ids = ''    
    surl_credentials = client.get_surl_credentials()
    for i in measurements:
       ids+=i['id']+","
   

    return render_template('list', {'record_label': record_label, 'num_measurements' : num_measurements, 
                                     'measurements': measurements, 'in_carenet':in_carenet, 'jsonData':jsonData,'record_id':record_id,'surl_credentials':surl_credentials,'ids':ids ,'measurements2':measurements2})


def new_measurement(request):
    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP
    jsonData = " "
    r = " "
    if request.method == "GET":
        return render_template('newmeasurement',{ 'jsonData': jsonData,'record_id':record_id})
    else:

        # Fix dates formatted by JQuery into xs:dateTime                                        
        date = request.POST['measurementDate'].replace(' A','T')
#        date = date.replace(' P','T')
        date = date.replace('F','Z')
        # get the variables and create a problem XML
        params = {'name': request.POST['name'], 
                  'name_value': request.POST['name_value'], 
                  'name_abbrev':'http://purl.bioontology.org/ontology/SNOMEDCT/', 
                  'number': request.POST['number'], 
                  'kind': request.POST['kind'], 
                  'value': request.POST['value'], 
                  'unit' : request.POST['unit'],
                  'measurementDate' : date#request.POST['measurementDate']
               }

        procedure_xml = render_raw('measurement', params, type='xml')

        # add the problem
        client = get_indivo_client(request)
        procedure_xml=procedure_xml.encode('ascii', 'xmlcharrefreplace')
#        resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml, content_type='application/xml')


        limit=int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        query_params = {
         'limit': limit,
         'offset': offset,
         #'order_by': 'startDate',
         'status': 'active',
        }
        carenet_list =[]
        resp, content = client.generic_list(record_id=record_id, data_model="Measurements", body=query_params)

        if resp['status'] == '200':
           probs = simplejson.loads(content)
           if probs:
            resp, content = client.document_carenets(record_id=record_id, document_id=str(probs[0]['__documentid__']))

            if resp['status'] =='200':
               tree = ET.fromstring(content)
#               for elem in tree.iter():
 #                   test +=str(elem.tag)

               Document = tree.findall(".//Carenet")

               for e in Document:
                   carenet_list.append( e.attrib.get('id'))


        resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml, content_type='application/xml')

        tree = ET.fromstring(content)
        Document = tree.find("Document")
        new_document_id = str(tree.attrib.get('id'))

        if carenet_list:
               carenet_list2 = json.dumps(carenet_list)
               carenet_list = simplejson.loads(carenet_list2)
            #for i in carenet_list:
               client = get_indivo_client(request)
               surl_credentials = client.get_surl_credentials()
               return render_template('share_step', {'record_id':record_id,'carenet_list':carenet_list,'document_id':str(new_document_id),'surl_credentials':surl_credentials})

        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error creating new measurement: %s"%content)
        
        # add a notification
        # let's not do this anymore because it's polluting the healthfeed
        client.record_notify(record_id=request.session['record_id'], 
                              body={'content':'a new measurement has been added to your procedures list'})
        
        return HttpResponseRedirect(reverse(measurement_list))


def code_lookup(request):
    client = get_indivo_client(request)
    
    query = request.GET['query']
    
    # reformat this for the jQuery autocompleter
    resp, content = client.coding_system_query(system_short_name='procedures', body={'q':query}) 
    #resp, content = client.coding_system_query(system_short_name='snomed', body={'q':query})
    if resp['status'] != '200':
        # TODO: handle errors
        # But this Indivo instance might not support codingsystem lookup, so let's pass
        pass
    codes = simplejson.loads(content)
    formatted_codes = {'query': query, 'suggestions': [c['consumer_value'] for c in codes], 'data': codes}
    
    return HttpResponse(simplejson.dumps(formatted_codes), mimetype="text/plain")

def one_measurement(request, measurement_id):
    client = get_indivo_client(request)
    record_id = request.session.get('record_id', None)
    INDIVO_IP = settings.INDIVO_IP
    jsonData = " "
    r = " "

    if record_id:
        # get record info
        resp, content = client.record(record_id=record_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)
        
        # read the document
        resp, content = client.record_specific_document(record_id=record_id, document_id=measurement_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching document: %s"%content)
        doc_xml = content

        # read the document's metadata
        resp, content = client.record_document_meta(record_id=record_id, document_id=measurement_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching document metadata: %s"%content)
        doc_meta_xml = content

    else:
        # get record info
        carenet_id = request.session['carenet_id']
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)
        
        # read the document
        resp, content = client.carenet_document(carenet_id=carenet_id, document_id=measurement_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching document from carenet: %s"%content)
        doc_xml = content

        # read the document's metadata
        resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=measurement_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching document metadata from carenet: %s"%content)
        doc_meta_xml = content
    
    doc = parse_xml(doc_xml)    
    measurement = parse_sdmx_problem(doc, ns=True)
    
    if doc_meta_xml:
        doc_meta = parse_xml(doc_meta_xml)
        meta = parse_meta(doc_meta)
    else:
        meta = None
    
    record_label = record.attrib['label']
    surl_credentials = client.get_surl_credentials()
    
    return render_template('one', {'measurement':measurement, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'measurement_id': measurement_id, 'surl_credentials': surl_credentials,'jsonData':jsonData})


def edit_measurement(request, measurement_id):
    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP
    jsonData = " "
    r = " "
    if request.method == "GET":
      
       client = get_indivo_client(request)
       record_id = request.session.get('record_id', None)

       if record_id:
           # get record info
           resp, content = client.record(record_id=record_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error reading Record info: %s"%content)
           record = parse_xml(content)
        
           # read the document
           resp, content = client.record_specific_document(record_id=record_id, document_id=measurement_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document: %s"%content)
           doc_xml = content
   
           # read the document's metadata
           resp, content = client.record_document_meta(record_id=record_id, document_id=measurement_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document metadata: %s"%content)
           doc_meta_xml = content

       else:
           # get record info
           carenet_id = request.session['carenet_id']
           resp, content = client.carenet_record(carenet_id=carenet_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error reading Record info: %s"%content)
           record = parse_xml(content)
        
           # read the document
           resp, content = client.carenet_document(carenet_id=carenet_id, document_id=measurement_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document from carenet: %s"%content)
           doc_xml = content

           # read the document's metadata
           resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=measurement_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document metadata from carenet: %s"%content)
           doc_meta_xml = content
    
       doc = parse_xml(doc_xml)    
       measurement = parse_sdmx_problem(doc, ns=True)
    
       if doc_meta_xml:
           doc_meta = parse_xml(doc_meta_xml)
           meta = parse_meta(doc_meta)
       else:
           meta = None
       
       record_label = record.attrib['label']
       surl_credentials = client.get_surl_credentials()
    
       return render_template('one_edit', {'measurement':measurement, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'measurement_id': measurement_id, 'surl_credentials': surl_credentials, 'jsonData': jsonData})
    else:

       # Fix dates formatted by JQuery into xs:dateTime                                        
       date = request.POST['measurementDate'].replace(' A','T')
#        date = date.replace(' P','T')
       date = date.replace('F','Z')
 
       # get the variables and create a problem XML
       params = {
                  'name': request.POST['name'],
                  'name_value': request.POST['name_value'],
                  'name_abbrev':'http://purl.bioontology.org/ontology/SNOMEDCT/',
                  'number': request.POST['number'],
                  'kind': request.POST['kind'],
                  'value': request.POST['value'],
                  'unit' : request.POST['unit'],
                  'measurementDate' : date #request.POST['measurementDate']
		}
#       measurement_xml = render_raw('measurement', params, type='xml')
       procedure_xml = render_raw('measurement', params, type='xml') 
       client = get_indivo_client(request)
       record_id = request.session.get('record_id', None)
       procedure_xml=procedure_xml.encode('ascii', 'xmlcharrefreplace') 
       # add the problem
       #resp, content = client.record_app_document_create_or_update(pha_email="procedures@apps.indivo.org", document_id=procedure_id, body=procedure_xml)
       resp, content = client.document_version(record_id=request.session['record_id'], document_id=measurement_id, body=procedure_xml, headers={}, content_type='application/xml')
       #resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml, content_type='application/xml')

       if resp['status'] != '200':
           # TODO: handle errors
           raise Exception("Error creatiTANM AASASHASKLng new measurement: %s"%content)
        
       # add a notification
       # let's not do this anymore because it's polluting the healthfeed
       # client.record_notify(record_id=request.session['record_id'], 
       #                      body={'content':'a new problem has been added to your problem list'})
        


       return HttpResponseRedirect(reverse(measurement_list))

def delete_measurement(request, measurement_id):
       client = get_indivo_client(request)
       record_id = request.session.get('record_id', None)
       #resp, content = client.document_set_status(record_id=request.session['record_id'], document_id=procedure_id)	
       resp, content = client.document_set_status(record_id=record_id, document_id=measurement_id,body={'status':'archived', 'reason':'removed by user'})	
       return HttpResponseRedirect(reverse(measurement_list))


def archived_measurements(request):
    limit=int(request.GET.get('limit', 100))
    offset = int(request.GET.get('offset', 0))
    query_params = {
           'limit': limit,
           'offset': offset,
           'status': 'archived',
           }
    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP
    jsonData = " "
    r = " "

    client = get_indivo_client(request)
    #s = self.request.get('s')
    in_carenet = request.session.has_key('carenet_id')
    if not in_carenet:
        # get record info
        record_id = request.session['record_id']
        resp, content = client.record(record_id=record_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)

        # read problems
        resp, content = client.generic_list(record_id=record_id, data_model="Measurements", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading measurements: %s"%content)
        probs = simplejson.loads(content)

    else:
        # get record info
        carenet_id = request.session['carenet_id']
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)

        # read problems from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Measurement", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading measurements from carenet: %s"%content)
        measurements = simplejson.loads(content)

    measurements = map(process_problem, probs)
    record_label = record.attrib['label']
    num_measurements = len(measurements)

    return render_template('archived_list', {'record_label': record_label, 'num_measurements' : num_measurements,
                                     'measurements': measurements, 'in_carenet':in_carenet, 'jsonData': jsonData })



def restore_measurement(request,measurement_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=measurement_id, body={'status':'active', 'reason':'restored by user'})
        return HttpResponseRedirect(reverse(archived_measurements))

