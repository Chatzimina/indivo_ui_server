#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Views for the Indivo Problems app

Ben Adida
ben.adida@childrens.harvard.edu
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
#    return HttpResponse(request.session['clinicianquestions_access_token']['oauth_token'])
    if not request.session.has_key('clinicianquestions_access_token'):
        # request a request token
       req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
       request.session['request_token'] = req_token

       return HttpResponseRedirect(client.auth_redirect_url)
    else:
       if datetime.datetime.now() > request.session['clinicianquestions_time'] + datetime.timedelta(minutes=5):

         req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
         request.session['request_token'] = req_token
  
         return HttpResponseRedirect(client.auth_redirect_url)
       else:
         access_token=request.session['clinicianquestions_access_token']
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

    # go to list of clinicianquestions
         return HttpResponseRedirect(reverse(clinicianquestion_list))
   

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
    request.session['clinicianquestions_access_token']=access_token
    request.session['clinicianquestions_time']=datetime.datetime.now()
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
    
    # go to list of clinicianquestions
    return HttpResponseRedirect(reverse(clinicianquestion_list))

def test_message_send(request):
    """
    testing message send with attachments assumes record-level share
    """
    client = get_indivo_client(request)

    record_id = request.session['record_id']

    message_id = str(uuid.uuid4())
    client.record_send_message(record_id=record_id, message_id=message_id, body={'subject':'testing', 'body':'testing! [a link](http://indivohealth.org/)', 'num_attachments':'1', 'body_type': 'markdown'})

    # an XML doc to send
    clinicianquestion_xml = render_raw('clinicianquestion', {'startDate': '2010-04-26T19:37:05.000Z', 'endDate': '2010-04-26T19:37:05.000Z', 'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/', 'code': '37796009', 'code_fullname':'Migraine (disorder)', 'comments': 'I\'ve had a headache waiting for alpha3.', 'diagnosed_by': 'Dr. Ken'}, type='xml')

    client.record_message_attach(record_id=record_id, message_id=message_id, attachment_num="1", body=clinicianquestion_xml)

    return HttpResponseRedirect(reverse(clinicianquestion_list))

def clinicianquestion_list(request):
    
 
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


        # read clinicianquestions
        resp, content = client.generic_list(record_id=record_id, data_model="Clinicianquestion", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading clinicianquestions: %s"%content)
        content = content.encode('latin-1')
        probs = simplejson.loads(content)

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
        # read clinicianquestions from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Clinicianquestion", body=query_params)
 
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading clinicianquestions from carenet: %s"%content)
        probs = simplejson.loads(content)


#    probs = probs.decode('iso-8859-1').encode('utf8')        
    probs = map(process_problem, probs)

    record_label = record.attrib['label']
    num_clinicianquestions = len(probs)
    surl_credentials = client.get_surl_credentials()   
    ids=''
    for i in probs:
       ids+=i['id']+","
       


    return render_template('list', {'record_label': record_label, 'num_clinicianquestions' : num_clinicianquestions,'record_id':record_id, 
                                    'clinicianquestions': probs, 'in_carenet':in_carenet,'jsonData':jsonData,'record_id':record_id,'surl_credentials':surl_credentials,'ids':ids})

def share_step(request):

     return HttpResponse('tipote')


def new_clinicianquestion(request):
    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP
    jsonData = None
    r = " "
    client = get_indivo_client(request)
    surl_credentials = client.get_surl_credentials()
    account_id = request.POST.get('account_id')

    if request.method == "GET":
        return render_template('newclinicianquestion',{'jsonData': jsonData,'record_id':record_id})
    else:


	patientName = request.POST['patientName']
        patientId = request.POST['patientId']
	diagnosisAge = request.POST['diagnosisAge']
        gender = request.POST['gender']
        diagnosis = request.POST['diagnosis']
        diagnosisExtra = request.POST['diagnosisExtra']
        initialDiagnosis= request.POST['initialDiagnosis']
        treatmentC= request.POST['treatmentC']
        treatmentS= request.POST['treatmentS']
 	treatmentR= request.POST['treatmentR']
	treatmentCI= request.POST['treatmentCI']
	treatmentSI= request.POST['treatmentSI']
	treatmentRI= request.POST['treatmentRI']
	treatmentCD= request.POST['treatmentCD']
	treatmentSD= request.POST['treatmentSD']
	treatmentRD= request.POST['treatmentRD']
	karnovskyIndex= request.POST['karnovskyIndex']
	expectedOutcome= request.POST['expectedOutcome']
	computerSkills= request.POST['computerSkills']
	computerGames= request.POST['computerGames']
        
        # get the variables and create a clinicianquestion XML
        params = {'patientName': patientName,
		  'patientId': patientId,
		  'diagnosisAge': diagnosisAge,
                  'gender': gender,
                  'diagnosis': diagnosis,
                  'diagnosisExtra': diagnosisExtra,
                  'initialDiagnosis':initialDiagnosis,
                  'treatmentC': treatmentC,
		  'treatmentR':treatmentR,
                  'treatmentS' :treatmentS,
		  'treatmentCI' :treatmentCI,
		  'treatmentSI' :treatmentSI,
		  'treatmentRI' :treatmentRI,
		  'treatmentSD' :treatmentSD,
		  'treatmentCD' :treatmentCD,
		  'treatmentRD' :treatmentRD,
		  'karnovskyIndex' :karnovskyIndex,
		  'expectedOutcome' : expectedOutcome,
		  'computerSkills' :computerSkills,
		  'computerGames' :computerGames,
			
		}

        clinicianquestion_xml = render_raw('clinicianquestion', params, type='xml')
        
        # add the clinicianquestion
        client = get_indivo_client(request)


        clinicianquestion_xml= clinicianquestion_xml.encode('ascii', 'xmlcharrefreplace')#encode('utf-8')
        limit=int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        query_params = {
         'limit': limit,
         'offset': offset,
         'status': 'active',
        }
        carenet_list =[]
        resp, content = client.generic_list(record_id=record_id, data_model="Problem", body=query_params)
        if resp['status'] == '200':
           probs = simplejson.loads(content)
           if probs:
            resp, content = client.document_carenets(record_id=record_id, document_id=str(probs[0]['__documentid__']))

            if resp['status'] =='200':
               tree = ET.fromstring(content)
               Document = tree.findall(".//Carenet")

               for e in Document:
                   carenet_list.append( e.attrib.get('id'))
    
        resp, content = client.document_create(record_id=request.session['record_id'], body=clinicianquestion_xml, 
                                               content_type='application/xml')

        tree = ET.ElementTree(ET.fromstring(content))

        tree = ET.fromstring(content)

        Document = tree.find("Document")


        new_document_id = str(tree.attrib.get('id'))


        try:
           conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'");
#           conn.autocommit = True
           conn.set_isolation_level(0)
           conn.commit()
           cursor = conn.cursor()
       
        except  psycopg2.DatabaseError, e:
           return HttpResponse(e) 

        try:

           cursor.execute( "SELECT id  FROM indivo_fact where document_id='"+new_document_id+"'" )
           conn.commit()
           result = cursor.fetchall()

        except  psycopg2.DatabaseError, e:
           return HttpResponse(e)
         

        if carenet_list:
               carenet_list2 = json.dumps(carenet_list)
               carenet_list = simplejson.loads(carenet_list2)
            #for i in carenet_list:
               client = get_indivo_client(request)
               surl_credentials = client.get_surl_credentials()
               return render_template('share_step', {'record_id':record_id,'carenet_list':carenet_list,'document_id':str(new_document_id),'surl_credentials':surl_credentials})
        

        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error creating new clinicianquestion: %s"%content)

        # add a notification
        # let's not do this anymore because it's polluting the healthfeed
        client.record_notify(record_id=request.session['record_id'], 
                              body={'content':'a new clinicianquestion has been added to your clinicianquestion list'})
        #if request.session['carenet_id']:
        #       resp,content = client.carenet_document_placement(record_id=request.session['record_id'],carenet_id=request.session['carenet_id'],document_id=request.session['document_id'])    
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error creating new clinicianquestion: %s"%content)

        return HttpResponseRedirect(reverse(clinicianquestion_list))

def code_lookup(request):
    client = get_indivo_client(request)
    
    query = request.GET['query']

    # reformat this for the jQuery autocompleter
    resp, content = client.coding_system_query(system_short_name='findings', body={'q':query}) 

#    resp, content = client.coding_system_query(system_short_name='snomed', body={'q':query})
    if resp['status'] != '200':
        # TODO: handle errors
        # But this Indivo instance might not support codingsystem lookup, so let's pass
        pass
    codes = simplejson.loads(content)
    formatted_codes = {'query': query, 'suggestions': [c['consumer_value'] for c in codes], 'data': codes}
    
    return HttpResponse(simplejson.dumps(formatted_codes), mimetype="text/plain")

def one_clinicianquestion(request,clinicianquestion_id):
    client = get_indivo_client(request)
    record_id = request.session.get('record_id', None)
    INDIVO_IP = settings.INDIVO_IP
    jsonData = None
    r = " "
    
    if record_id:
        # get record info
         resp, content = client.record(record_id=record_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error reading Record info: %s"%content)
         record = parse_xml(content)
        
        # read the document
         resp, content = client.record_specific_document(record_id=record_id, document_id=clinicianquestion_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error fetching document: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.record_document_meta(record_id=record_id, document_id=clinicianquestion_id)
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
         resp, content = client.carenet_document(carenet_id=carenet_id, document_id=clinicianquestion_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error fetching document from carenet: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=clinicianquestion_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error fetching document metadata from carenet: %s"%content)
         doc_meta_xml = content
    
    doc = parse_xml(doc_xml)    
    clinicianquestion = parse_sdmx_problem(doc, ns=True)
    
    if doc_meta_xml:
        doc_meta = parse_xml(doc_meta_xml)
        meta = parse_meta(doc_meta)
    else:
        meta = None
    
    record_label = record.attrib['label']
    surl_credentials = client.get_surl_credentials()
    
    return render_template('one', {'clinicianquestion':clinicianquestion, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'clinicianquestion_id': clinicianquestion_id, 'surl_credentials': surl_credentials, 'jsonData' : jsonData})

def archived_clinicianquestion(request,clinicianquestion_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=clinicianquestion_id, body={'status':'archived', 'reason':'removed by user'})
        return HttpResponseRedirect(reverse(clinicianquestion_list))

def carenet_share(request,clinicianquestion_id):
        client = get_indivo_client(request)

        in_carenet = request.session.has_key('carenet_id')
        
        client = get_indivo_client(request)

        record_id = request.session['record_id']
        carenet_id = request.session['carenet_id']
        resp, content = client.carenet_document_placement(record_id=record_id, document_id=clinicianquestion_id,carenet_id=carenet_id)
        return HttpResponseRedirect(reverse(clinicianquestion_list))


def edit_clinicianquestion(request, clinicianquestion_id):

    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP
    jsonData = None
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
           resp, content = client.record_specific_document(record_id=record_id, document_id=clinicianquestion_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document: %s"%content)
           doc_xml = content

           # read the document's metadata
           resp, content = client.record_document_meta(record_id=record_id, document_id=clinicianquestion_id)
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
           resp, content = client.carenet_document(carenet_id=carenet_id, document_id=clinicianquestion_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document from carenet: %s"%content)
           doc_xml = content
# read the document's metadata
           resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=clinicianquestion_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document metadata from carenet: %s"%content)
           doc_meta_xml = content

       doc = parse_xml(doc_xml)
       clinicianquestion = parse_sdmx_problem(doc, ns=True)

       if doc_meta_xml:
           doc_meta = parse_xml(doc_meta_xml)
           meta = parse_meta(doc_meta)
       else:
           meta = None

       record_label = record.attrib['label']
       surl_credentials = client.get_surl_credentials()

       return render_template('one_edit', {'clinicianquestion':clinicianquestion, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'clinicianquestion_id': clinicianquestion_id, 'surl_credentials': surl_credentials, 'jsonData': jsonData})
    else:
      
       patientName = request.POST['patientName']
       patientId = request.POST['patientId']
       diagnosisAge = request.POST['diagnosisAge']
       gender = request.POST['gender']
       diagnosis = request.POST['diagnosis']
       diagnosisExtra = request.POST['diagnosisExtra']
       initialDiagnosis= request.POST['initialDiagnosis']
       treatmentC= request.POST['treatmentC']
       treatmentS= request.POST['treatmentS']
       treatmentR= request.POST['treatmentR']
       treatmentCI= request.POST['treatmentCI']
       treatmentSI= request.POST['treatmentSI']
       treatmentRI= request.POST['treatmentRI']
       treatmentCD= request.POST['treatmentCD']
       treatmentSD= request.POST['treatmentSD']
       treatmentRD= request.POST['treatmentRD']
       karnovskyIndex= request.POST['karnovskyIndex']
       expectedOutcome= request.POST['expectedOutcome']
       computerSkills= request.POST['computerSkills']
       computerGames= request.POST['computerGames']

        # get the variables and create a clinicianquestion XML
       params = {'patientName': patientName,
                  'patientId': patientId,
		  'diagnosisAge': diagnosisAge,
                  'gender': gender,
                  'diagnosis': diagnosis,
                  'diagnosisExtra': diagnosisExtra,
                  'initialDiagnosis':initialDiagnosis,
                  'treatmentC': treatmentC,
                  'treatmentR':treatmentR,
                  'treatmentS' :treatmentS,
                  'treatmentCI' :treatmentCI,
                  'treatmentSI' :treatmentSI,
                  'treatmentRI' :treatmentRI,
                  'treatmentSD' :treatmentSD,
                  'treatmentCD' :treatmentCD,
                  'treatmentRD' :treatmentRD,
                  'karnovskyIndex' :karnovskyIndex,
                  'expectedOutcome' : expectedOutcome,
                  'computerSkills' :computerSkills,
                  'computerGames' :computerGames,

                }


 
                            
       clinicianquestion_xml = render_raw('clinicianquestion', params, type='xml')

       client = get_indivo_client(request)
       record_id = request.session.get('record_id', None)
       clinicianquestion_xml= clinicianquestion_xml.encode('ascii', 'xmlcharrefreplace')
       resp, content = client.document_version(record_id=request.session['record_id'], document_id=clinicianquestion_id, body=clinicianquestion_xml, content_type='application/xml')
       #resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml, content_type='application/xml')

       if resp['status'] != '200':
          # TODO: handle errors
            raise Exception("Error creating a new clinicianquestion: %s"%content)

       # add a notification
       # let's not do this anymore because it's polluting the healthfeed
       # client.record_notify(record_id=request.session['record_id'],
       #                      body={'content':'a new clinicianquestion has been added to your clinicianquestion list'})

       return HttpResponseRedirect(reverse(clinicianquestion_list))




def edit_clinicianquestion2(request,clinicianquestion_id):

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
           resp, content = client.record_specific_document(record_id=record_id, document_id=clinicianquestion_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document: %s"%content)
           doc_xml = content

           # read the document's metadata
           resp, content = client.record_document_meta(record_id=record_id, document_id=clinicianquestion_id)
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
           resp, content = client.carenet_document(carenet_id=carenet_id, document_id=clinicianquestion_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document from carenet: %s"%content)
           doc_xml = content


       doc = parse_xml(doc_xml)
       clinicianquestion = parse_sdmx_problem(doc, ns=True)

       if doc_meta_xml:
           doc_meta = parse_xml(doc_meta_xml)
           meta = parse_meta(doc_meta)
       else:
           meta = None

       record_label = record.attrib['label']
       surl_credentials = client.get_surl_credentials()

       #return render_template('one_edit', {'allergy':allergy 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'allergy_id': allergy_id, 'surl_credentials': surl_credentials})
       return render_template('one_edit', {'clinicianquestion':clinicianquestion, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'clinicianquestion_id': clinicianquestion_id, 'surl_credentials': surl_credentials})
    else:
        #formatted by JQuery into xs:dateTime
    
        startDate = request.POST['startDate']
        if startDate.find("T00:00:00Z")== -1:
            startDate = request.POST['startDate'] + 'T00:00:00Z'
        
        endDate = request.POST['endDate']
        if endDate.find("T00:00:00Z")== -1:
            endDate = request.POST['endDate'] + 'T00:00:00'

        # get the variables and create a clinicianquestion XML
        params = {'code_abbrev':'',
                  'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                  'startDate': startDate,
                  'endDate': endDate,
                  'code_fullname': request.POST['code_fullname'],
                  'code': request.POST['code'],
                  'comments' : request.POST['comments']}

        clinicianquestion_xml = render_raw('clinicianquestion', params, type='xml')

        client = get_indivo_client(request)
        record_id = request.session.get('record_id', None)



       # add the clinicianquestion
       #resp, content = client.record_app_document_create_or_update(pha_email="procedures@apps.indivo.org", document_id=procedure_id, body=procedure_xml)
        resp, content = client.document_version(record_id=request.session['record_id'], document_id=clinicianquestion_id, body=clinicianquestion_xml, content_type='application/xml')
       # resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml, content_type='application/xml')

        if resp['status'] != '200':
           # TODO: handle errors
            raise Exception("Error creatiTANM AASASHASKLng  allergy: %s"%content)
 # add a notification
       # let's not do this anymore because it's polluting the healthfeed
       # client.record_notify(record_id=request.session['record_id'],
       #                      body={'content':'a new clinicianquestion has been added to your clinicianquestion list'})



        return HttpResponseRedirect(reverse(clinicianquestion_list))


def archived_clinicianquestions(request):
    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP
    jsonData = None
    r = " "
    limit=int(request.GET.get('limit', 100))
    offset = int(request.GET.get('offset', 0))
    #status = int(request.GET.get('status', 'active'))
    query_params = {
        'limit': limit,
        'offset': offset,
        #'order_by': 'severity_title',
        'status': 'archived',
        }

    client = get_indivo_client(request)

    in_carenet = request.session.has_key('carenet_id')
    if not in_carenet:
        # get record info
        record_id = request.session['record_id']
        resp, content = client.record(record_id=record_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)

        # read clinicianquestions
        resp, content = client.generic_list(record_id=record_id, data_model="Clinicianquestion", body=query_params)
        #resp, content = client.generic_list(record_id=record_id, data_model="Problem", body=query_params))
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading clinicianquestions: %s"%content)
        probs = simplejson.loads(content)

    else:
        # get record info
        carenet_id = request.session['carenet_id']
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)

        # read clinicianquestions from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Clinicianquestion")
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading clinicianquestions from carenet: %s"%content)
        probs = simplejson.loads(content)

    probs = map(process_problem, probs)
    record_label = record.attrib['label']
    num_clinicianquestions = len(probs)

    return render_template('archived_list', {'record_label': record_label, 'num_clinicianquestions' : num_clinicianquestions,
                                    'clinicianquestions': probs, 'in_carenet':in_carenet, 'jsonData': jsonData,'record_id':record_id })


def restore_clinicianquestion(request,clinicianquestion_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=clinicianquestion_id, body={'status':'active', 'reason':'restored by user'})
        return HttpResponseRedirect(reverse(archived_clinicianquestions))
