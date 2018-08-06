"""
Views for the Indivo Problems app

Ben Adida
ben.adida@childrens.harvard.edu
Update:
Chatzimina Maria
"""

from utils import *
import uuid

from django.utils import simplejson
import requests
import urllib
import urllib2

import json
from django.shortcuts import render_to_response


import os
from os import listdir
from os.path import isfile, join
import re
import requests
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

  ##  if not request.session.has_key('allergiess_access_token'):
        # request a request token
    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
    request.session['request_token'] = req_token

    return HttpResponseRedirect(client.auth_redirect_url)
    if 1==2:
       if datetime.datetime.now() > request.session['allergiess_time'] + datetime.timedelta(minutes=5):

         req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
         request.session['request_token'] = req_token

         return HttpResponseRedirect(client.auth_redirect_url)
       else:
         access_token=request.session['allergiess_access_token']
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
         return HttpResponseRedirect(reverse(allergies_list))



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
    request.session['allergiess_access_token']=access_token
    request.session['allergiess_time']=datetime.datetime.now()
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
    return HttpResponseRedirect(reverse(allergies_list))





def test_message_send(request):
    """
    testing message send with attachments assumes record-level share
    """
    client = get_indivo_client(request)

    record_id = request.session['record_id']

    message_id = str(uuid.uuid4())
    client.record_send_message(record_id=record_id, message_id=message_id, body={'subject':'testing', 'body':'testing! [a link](http://indivohealth.org/)', 'num_attachments':'1', 'body_type': 'markdown'})

    # an XML doc to send
    problem_xml = render_raw('problem', {'date_onset': '2010-04-26T19:37:05.000Z', 'date_resolution': '2010-04-26T19:37:05.000Z', 'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/', 'code': '37796009', 'code_fullname':'Migraine (disorder)', 'comments': 'I\'ve had a headache waiting for alpha3.', 'diagnosed_by': 'Dr. Ken'}, type='xml')

    client.record_message_attach(record_id=record_id, message_id=message_id, attachment_num="1", body=problem_xml)

    return HttpResponseRedirect(reverse(allergies_list))


def index(request):
    """pass the record_id to JMVC and use the JSON/REST api from there"""

    return render_to_response(
        settings.JS_HOME+'/'+settings.SUBMODULE_NAME+'.html',
        {'SUBMODULE_NAME': settings.SUBMODULE_NAME,
         'INDIVO_UI_APP_CSS': settings.INDIVO_UI_SERVER_BASE+'/jmvc/ui/resources/css/ui.css'}
    )



def allergies_list(request):
    limit=int(request.GET.get('limit', 100))
    offset = int(request.GET.get('offset', 0))
    #status = int(request.GET.get('status', 'active'))
    query_params = {
        'limit': limit,
        'offset': offset,
        'order_by': 'severity_title',
	'status': 'active',
        }
         
    # Get the webserviced information
    #r = requests.get("http://thor.ics.forth.gr:8580/ProfilingServer/getPatientResults?clinicianKey=clinician12.&patientId=396i@gqr!a")
    #r.text  
    #jsonData = json.loads(r.text)

    client = get_indivo_client(request)
    jsonData = " "
    r = " " 
    in_carenet = request.session.has_key('carenet_id')
    if not in_carenet:
        # get record info
        record_id = request.session['record_id']

        INDIVO_IP = settings.INDIVO_IP
        jsonData = " "
#        try:
#          r = requests.get(INDIVO_IP+"/ProfilingServer/getPatientResults?clinicianKey=clinician12.&patientId="+record_id,timeout=20)
#          r.text
#          jsonData = json.loads(r.text)
#        except Exception,e:
#          pass
#        except requests.exceptions.ConnectionError as e:    # This is the correct syntax
#          pass
#        charCount = {}
#        if r != " ":
#          text = r.text
#          for char in r.text:
#            charCount[char] = charCount.get(char, 0) + 1
#          characters = len(text) - text.count(' ')
#          if characters < 60:
#             jsonData = " "

        resp, content = client.record(record_id=record_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)
        #read alergies        
        resp, content = client.generic_list(record_id=record_id, data_model="Allergy", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading allergies: %s"%content)
        allergies = simplejson.loads(content)

        resp, content = client.generic_list(record_id=record_id, data_model="AllergyExclusion")
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading allergy exclusions: %s"%content)
        exclusions = simplejson.loads(content)

        # read allergies
        #resp, content = client.generic_list(record_id=record_id, data_model="Allergy")
        #if resp['status'] != '200':
            # TODO: handle errors
        #    raise Exception("Error reading allergies: %s"%content)
        #allegs = simplejson.loads(content)

    else:
        record_id=""
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

        carenet_id = request.session['carenet_id']
        resp2, content2 = client.carenet_document_list(carenet_id=carenet_id)
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)
        record2 = parse_xml(content2)
        # read problems from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Allergy", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content)
        allergies = simplejson.loads(content)
        
       
     
      
    

    allergies = map(process_problem, allergies)
    record_label = record.attrib['label']
    num_allergies = len(allergies)
    currentpath = os.path.dirname(os.path.abspath(__file__))
    mypath = currentpath + '/static/images/images_allergies'
    staticPath = '/images/images_allergies'
    folders = listdir(mypath)
    test = folders
    if  xrange(len(allergies)) > 0:
     allergiesImage = ['/images/images_allergies/allergy-treatments.png' for x in xrange(len(allergies))]    
     for i in xrange(0,len(allergies)):
        allerg = allergies[i]['allergic_reaction_title']
        regex = re.compile('\(.+?\)')
        rawAllergy = regex.sub('', allerg)
        allergyLower = rawAllergy.lower()
        for f in folders:
            cond=(f.replace('_',' '))
            condition = (str(cond)).rstrip()
            allergyLow =((allergyLower)).rstrip() 
	    if condition == allergyLow:
               allerg = 'maria'
               newpath = mypath +"/" + f +'/'
               files = listdir(newpath)
               test = newpath
               for fil in files:
                   if 'jpg' in fil or 'jpeg' in fil or 'JPG' in fil or 'JPEG' in fil or 'gif' in fil or 'GIF' in fil or 'png' in fil or 'PNG' in fil:
                      image = fil
                      allergiesImage[i] = staticPath + '/' + f +'/'+image 
    
     allergiesWithImages = zip(allergies,allergiesImage)
    else:
     allergiesWithImages = " "
    record_label = record.attrib['label']
    num_allergies = len(allergies)
    surl_credentials =  client.get_surl_credentials()
    ids = ""

    for i in allergies:

       ids+=i['id']+","
    return render_template('list', {'record_label': record_label, 'num_allergies' : num_allergies, 
                                    'allergies': allergies, 'in_carenet':in_carenet, 'jsonData': jsonData,'allergiesWithImages' : allergiesWithImages,'record_id':record_id,'surl_credentials':surl_credentials,'ids':ids})

def new_allergy(request):
    
    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP
    jsonData = " "
    r = " "
#    try:
#       r = requests.get(INDIVO_IP+"/ProfilingServer/getPatientResults?clinicianKey=clinician12.&patientId="+record_id,timeout=20)
#       r.text
#       jsonData = json.loads(r.text)
#    except Exception,e:
#       pass
#    except requests.exceptions.ConnectionError as e:    # This is the correct syntax
#       pass
#    charCount = {}
#    if r != " ":
#     text = r.text
#     for char in r.text:
#          charCount[char] = charCount.get(char, 0) + 1
#     characters = len(text) - text.count(' ')
#     if characters < 60:
#       jsonData = " " 

    if request.method == "GET":
        return render_template('newallergy', {'jsonData' : jsonData })
    else:

        # Fix dates formatted by JQuery into xs:dateTime                                        
        #date_onset = request.POST['date_onset'] + 'T00:00:00Z' if request.POST['date_onset'] != '' else ''
        #date_resolution = request.POST['date_resolution'] + 'T00:00:00Z' if request.POST['date_resolution'] != '' else ''

        # get the variables and create a problem XML
        #params = {'code_abbrev':'', 
        #          'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/', 
        #          'date_onset': date_onset, 
        #          'date_resolution': date_resolution, 
        #          'code_fullname': request.POST['code_fullname'], 
        #          'code': request.POST['code'], 
        #          'comments' : request.POST['comments']}
        	
	params = {'allergic_reaction_title': request.POST['allergic_reaction_title'],
	 	  'allergic_reaction_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                  'allergic_reaction_identifier': request.POST['allergic_reaction_identifier'],
		  'category_title': request.POST['category_title'],
                  'category_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                 'category_identifier': request.POST['allergen_id'],
                   'allergen_name' : request.POST['allergen_name'],
	           'drug_class_allergen_title': request.POST['drug_class_allergen_title'],
                  'drug_class_allergen_system': 'http://purl.bioontology.org/ontology/NDFRT/',
                  'drug_class_allergen_identifier': request.POST['drug_class_allergen_identifier'],
		  'severity_title': request.POST['severity_title'],
		  'severity_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                  'severity_identifier': request.POST['severity_identifier']}	  
	# CHARIS:
        #params = {'allergic_reaction_title': 'Anaphylaxis',
    	#	  'allergic_reaction_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
    	#	  'allergic_reaction_identifier': '39579001',
    	#	  'allergen_type': request.POST['allergen_type'],
    	#	  'category_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
    	#	'category_identifier': '416098002',
    	#	'allergen_name': request.POST['allergen_name'],
    	#	'drug_class_allergen_system': 'http://purl.bioontology.org/ontology/NDFRT/',
    	#	'drug_class_allergen_identifier': 'N0000175503',
    	#	'severity_title': 'Severe',
    	#	'severity_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
    	#	'severity_identifier': '24484000'}


	allergy_xml = render_raw('allergy', params, type='xml')

        # add the allergy
	client = get_indivo_client(request)
        allergy_xml = allergy_xml.encode('ascii', 'xmlcharrefreplace')
#	resp, content = client.document_create(record_id=request.session['record_id'], body=allergy_xml, 
#                                               content_type='application/xml')



        limit=int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        query_params = {
         'limit': limit,
         'offset': offset,
         #'order_by': 'startDate',
         'status': 'active',
        }
        carenet_list =[]
        resp, content = client.generic_list(record_id=record_id, data_model="Allergy", body=query_params)

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


        resp, content = client.document_create(record_id=request.session['record_id'], body=allergy_xml,
                                               content_type='application/xml')


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
		raise Exception("Error creating new allergy: %s"%content)
        
        # add a notification
        # let's not do this anymore because it's polluting the healthfeed
        client.record_notify(record_id=request.session['record_id'], 
                              body={'content':'a new allergy has been added to your allergy list'})
        
	return HttpResponseRedirect(reverse(allergies_list))


def archived_allergy(request,allergy_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=allergy_id, body={'status':'archived', 'reason':'removed by user'}) 
	return HttpResponseRedirect(reverse(allergies_list))


def code_lookup(request):
    client = get_indivo_client(request)
    
    query = request.GET['query'] 
    
    # reformat this for the jQuery autocompleter
    resp, content = client.coding_system_query(system_short_name='findings', body={'q':query})
#    resp, content = client.coding_system_query(system_short_name='allergies', body={'q':query})
    if resp['status'] != '200':
        # TODO: handle errors
        # But this Indivo instance might not support codingsystem lookup, so let's pass
        pass
    codes = simplejson.loads(content)
    formatted_codes = {'query': query, 'suggestions': [c['consumer_value'] for c in codes], 'data': codes}
    
    return HttpResponse(simplejson.dumps(formatted_codes), mimetype="text/plain")

def one_allergy(request, allergy_id):
     client = get_indivo_client(request)
     record_id = request.session.get('record_id')
    
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
         resp, content = client.record_specific_document(record_id=record_id, document_id=allergy_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error fetching document: %s"%content)
         doc_xml = content
 
         # read the document's metadata
         resp, content = client.record_document_meta(record_id=record_id, document_id=allergy_id)
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
         resp, content = client.carenet_document(carenet_id=carenet_id, document_id=allergy_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error fetching document from carenet: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=allergy_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error fetching document metadata from carenet: %s"%content)
         doc_meta_xml = content
    
     doc = parse_xml(doc_xml)    
     allergy = parse_sdmx_problem(doc, ns=True)
    
     if doc_meta_xml:
         doc_meta = parse_xml(doc_meta_xml)
         meta = parse_meta(doc_meta)
     else:
         meta = None
     
     record_label = record.attrib['label']
     surl_credentials = client.get_surl_credentials()
    #return render_template('one')
     return render_template('one', {'allergy':allergy, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'allergy_id': allergy_id, 'surl_credentials': surl_credentials, 'jsonData': jsonData})


def edit_allergy(request, allergy_id):
    
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
           resp, content = client.record_specific_document(record_id=record_id, document_id=allergy_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document: %s"%content)
           doc_xml = content

           # read the document's metadata
           resp, content = client.record_document_meta(record_id=record_id, document_id=allergy_id)
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
           resp, content = client.carenet_document(carenet_id=carenet_id, document_id=allergy_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document from carenet: %s"%content)
           doc_xml = content
       doc = parse_xml(doc_xml)
       allergy = parse_sdmx_problem(doc, ns=True)

       if doc_meta_xml:
           doc_meta = parse_xml(doc_meta_xml)
           meta = parse_meta(doc_meta)
       else:
           meta = None

       record_label = record.attrib['label']
       surl_credentials = client.get_surl_credentials()

       #return render_template('one_edit', {'allergy':allergy 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'allergy_id': allergy_id, 'surl_credentials': surl_credentials})
       return render_template('one_edit', {'allergy':allergy, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'allergy_id': allergy_id, 'surl_credentials': surl_credentials, 'jsonData': jsonData})
    else:

       # Fix dates formatted by JQuery into xs:dateTime
       #date_performed = request.POST['date_performed']
       #if date_performed.find("T00:00:00Z")== -1:
       #     date_performed = request.POST['date_performed'] + 'T00:00:00Z'

       # get the variables and create a problem XML
       #params = {'date_performed': date_performed,
       #           'name': request.POST['code_fullname'],
       #           'name_type': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
       #           'name_abbrev':request.POST['code'],
       #           'name_value': request.POST['comments_code'],
       #           'provider_name': request.POST['provider_name'],
       #           'provider_institution': request.POST['provider_institution'],
       #           'location': request.POST['location'],
       #           'comments' : request.POST['comments']}
    

       params = {'allergic_reaction_title': request.POST['allergic_reaction_title'],
                  'allergic_reaction_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                  'allergic_reaction_identifier': request.POST['allergic_reaction_identifier'],
                  'category_title': request.POST['category_title'],
                  'category_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                 'category_identifier': request.POST['allergen_id'],
                   'allergen_name' : request.POST['allergen_name'],
                   'drug_class_allergen_title': request.POST['drug_class_allergen_title'],
                  'drug_class_allergen_system': 'http://purl.bioontology.org/ontology/NDFRT/',
                  'drug_class_allergen_identifier': request.POST['drug_class_allergen_identifier'],
                  'severity_title': request.POST['severity_title'],
                  'severity_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                  'severity_identifier': request.POST['severity_identifier']}

  
 
#       params = {'allergic_reaction_title': request.POST['allergic_reaction_title'],
#                   'allergic_reaction_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
#                   'allergic_reaction_identifier': request.POST['allergic_reaction_identifier'],
#                   'allergen_type': request.POST['allergen_type'],
#                   'category_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
#                  'category_identifier': request.POST['allergen_id'],
#                    'allergen_name': request.POST['allergen_name'],
#                   'drug_class_allergen_system': 'http://purl.bioontology.org/ontology/NDFRT/',
#                   'drug_class_allergen_identifier': request.POST['allergen_name_id'],
#                   'severity_title': request.POST['severity_title'],
#                   'severity_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
#                   'severity_identifier': request.POST['severity_id']}
       allergy_xml = render_raw('allergy', params, type='xml')

       client = get_indivo_client(request)
       record_id = request.session.get('record_id', None)
       allergy_xml = allergy_xml.encode('ascii', 'xmlcharrefreplace')
       # add the problem
       #resp, content = client.record_app_document_create_or_update(pha_email="procedures@apps.indivo.org", document_id=procedure_id, body=procedure_xml)
       resp, content = client.document_version(record_id=request.session['record_id'], document_id=allergy_id, body=allergy_xml, headers={}, content_type='application/xml')
       #resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml, content_type='application/xml')

       if resp['status'] != '200':
           # TODO: handle errors
           raise Exception("Error creatiTANM AASASHASKLng new allergy: %s"%content)
 # add a notification
       # let's not do this anymore because it's polluting the healthfeed
       # client.record_notify(record_id=request.session['record_id'],
       #                      body={'content':'a new problem has been added to your problem list'})



       return HttpResponseRedirect(reverse(allergies_list))


def archived_allergies(request):
  
    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP
    jsonData = " "
    r = " "

    limit=int(request.GET.get('limit', 100))
    offset = int(request.GET.get('offset', 0))
    #status = int(request.GET.get('status', 'active'))
    query_params = {
        'limit': limit,
        'offset': offset,
        'order_by': 'severity_title',
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
        #read alergies
        resp, content = client.generic_list(record_id=record_id, data_model="Allergy", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading allergies: %s"%content)
        allergies = simplejson.loads(content)

        resp, content = client.generic_list(record_id=record_id, data_model="AllergyExclusion")
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading allergy exclusions: %s"%content)
        exclusions = simplejson.loads(content)

        # read allergies
        #resp, content = client.generic_list(record_id=record_id, data_model="Allergy")
        #if resp['status'] != '200':
            # TODO: handle errors
        #    raise Exception("Error reading allergies: %s"%content)
        #allegs = simplejson.loads(content)

    allergies = map(process_problem, allergies)
    record_label = record.attrib['label']
    num_allergies = len(allergies)
    return render_template('archived_list', {'record_label': record_label, 'num_allergies' : num_allergies,
                                    'allergies': allergies, 'in_carenet':in_carenet, 'jsonData': jsonData })


def restore_allergy(request,allergy_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=allergy_id, body={'status':'active', 'reason':'restored by user'})
        return HttpResponseRedirect(reverse(archived_allergies))
