"""
Views for the Indivo Appointments app
Chatzimina MAria
ICS-FORTH
"""

from utils import *
import uuid
import urllib
import urllib2
import requests
import json
import urllib, re, copy
import requests
import psycopg2
import utils
import urlparse


from django.utils import simplejson
import requests
from indivo_client_py import IndivoClient
import xmltodict
import sys
from xml.dom.minidom import parseString
import json
import xml.etree.ElementTree as ET
import psycopg2
import datetime



#INDIVO_SERVER_LOCATION = "http://139.91.190.131:8000"
#INDIVO_UI_SERVER_BASE = "http://139.91.190.131:80"
INDIVO_SERVER_OAUTH = {
  'consumer_key': 'problems@apps.indivo.org',
  'consumer_secret': 'problems'
}
#SERVER_PARAMS = {"api_base":INDIVO_SERVER_LOCATION,
#                 "authorization_base":INDIVO_UI_SERVER_BASE}
#CONSUMER_PARAMS = {"consumer_key": 'chrome',
#                   "consumer_secret": 'chrome'}

#MIME_TYPES = {'html': 'text/html',
#              'xml': 'application/xml'}

greek_alphabet = {
    u'\u0391': 'Alpha',
    u'\u0392': 'Beta',
    u'\u0393': 'Gamma',
    u'\u0394': 'Delta',
    u'\u0395': 'Epsilon',
    u'\u0396': 'Zeta',
    u'\u0397': 'Eta',
    u'\u0398': 'Theta',
    u'\u0399': 'Iota',
    u'\u039A': 'Kappa',
    u'\u039B': 'Lamda',
    u'\u039C': 'Mu',
    u'\u039D': 'Nu',
    u'\u039E': 'Xi',
    u'\u039F': 'Omicron',
    u'\u03A0': 'Pi',
    u'\u03A1': 'Rho',
    u'\u03A3': 'Sigma',
    u'\u03A4': 'Tau',
    u'\u03A5': 'Upsilon',
    u'\u03A6': 'Phi',
    u'\u03A7': 'Chi',
    u'\u03A8': 'Psi',
    u'\u03A9': 'Omega',
    u'\u03B1': 'alpha',
    u'\u03B2': 'beta',
    u'\u03B3': 'gamma',
    u'\u03B4': 'delta',
    u'\u03B5': 'epsilon',
    u'\u03B6': 'zeta',
    u'\u03B7': 'eta',
    u'\u03B8': 'theta',
    u'\u03B9': 'iota',
    u'\u03BA': 'kappa',
    u'\u03BB': 'lamda',
    u'\u03BC': 'mu',
    u'\u03BD': 'nu',
    u'\u03BE': 'xi',
    u'\u03BF': 'omicron',
    u'\u03C0': 'pi',
    u'\u03C1': 'rho',
    u'\u03C3': 'sigma',
    u'\u03C4': 'tau',
    u'\u03C5': 'upsilon',
    u'\u03C6': 'phi',
    u'\u03C7': 'chi',
    u'\u03C8': 'psi',
    u'\u03C9': 'omega',
    u'\u0391': 'alpha',
    u'\u0392': 'beta',
    u'\u0393': 'Gamma',
    u'\u0394': 'Delta',
    u'\u0395': 'Epsilon',
    u'\u0396': 'Zeta',
    u'\u0397': 'Eta',
    u'\u0398': 'Theta',
    u'\u0399': 'Iota',
    u'\u039a': 'Kappa',
    u'\u039b': 'Lamda',
    u'\u039c': 'Mu',
    u'\u039D': 'Nu',
    u'\u039E': 'Xi',
    u'\u039F': 'Omicron',
    u'\u03a0': 'Pi',
    u'\u03a1': 'Rho',
    u'\u03a3': 'Sigma',
    u'\u03a4': 'Tau',
    u'\u03a5': 'Upsilon',
    u'\u03a6': 'Phi',
    u'\u03a7': 'chi',
    u'\u03a8': 'Psi',
    u'\u03a9': 'Omega',
    u'\u03b1': 'alpha',
    u'\u03b2': 'beta',
    u'\u03b3': 'gamma',
    u'\u03b4': 'delta',
    u'\u03b5': 'epsilon',
    u'\u03b6': 'zeta',
    u'\u03b7': 'eta',
    u'\u03b8': 'theta',
    u'\u03b9': 'iota',
    u'\u03ba': 'kappa',
    u'\u03bb': 'lamda',
    u'\u03bc': 'mu',
    u'\u03bD': 'nu',
    u'\u03bE': 'xi',
    u'\u03bF': 'omicron',
    u'\u03c0': 'pi',
    u'\u03c1': 'rho',
    u'\u03c3': 'sigma',
    u'\u03c4': 'tau',
    u'\u03c5': 'upsilon',
    u'\u03c6': 'phi',
    u'\u03c7': 'chi',
    u'\u03c8': 'psi',
    u'\u03c9': 'omega',
}



def get_api(request=None):

    api = IndivoClient(SERVER_PARAMS, CONSUMER_PARAMS)
    if request:
        api.update_token(request.session.get('oauth_token_set'))

    return api


def tokens_get_from_server(request, username, password):
    """
    This method will not catch exceptions raised by create_session, be sure to catch them!
    """
    # hack! re-initing IndivoClient here
    api = get_api()
    resp, content = api.session_create({'username' : username, 'password' : password})
    if resp['status'] == '200':
        params = dict(urlparse.parse_qsl(content))
        request.session['username'] = username
        request.session['oauth_token_set'] = params
        request.session['account_id'] = urllib.unquote(params['account_id'])
    else:
        try:
            request.session.pop('oauth_token_set')
            request.session.pop('account_id')
        except KeyError:
            pass

    if DEBUG:
        utils.log('oauth_token: %(oauth_token)s outh_token_secret: %(oauth_token_secret)s' %
                            request.session['oauth_token_set'])

#    return HttpResponse(request)
    return (resp, content)


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

    ##if not request.session.has_key('appointments_access_token'):
        # request a request token
    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
    request.session['request_token'] = req_token

    return HttpResponseRedirect(client.auth_redirect_url)
    if 1==2:
       if datetime.datetime.now() > request.session['appointments_time'] + datetime.timedelta(minutes=5):

         req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
         request.session['request_token'] = req_token

         return HttpResponseRedirect(client.auth_redirect_url)
       else:
         access_token=request.session['appointments_access_token']
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
         return HttpResponseRedirect(reverse(appointment_list))


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
    request.session['appointments_access_token']=access_token
    request.session['appointments_time']=datetime.datetime.now()
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
    return HttpResponseRedirect(reverse(appointment_list))



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

    return HttpResponseRedirect(reverse(appointment_list))

def appointment_list(request):
    

    client = get_indivo_client(request)

    in_carenet = request.session.has_key('carenet_id')
    if not in_carenet:
        record_id = request.session['record_id']
        INDIVO_IP = settings.INDIVO_IP
        jsonData = None
        r = " "
#        try:
#            r = requests.get(INDIVO_IP+"/ProfilingServer/getPatientResults?clinicianKey=clinician12.&patientId="+record_id,timeout=20)
#            r.text
#            jsonData = json.loads(r.text)
#        except Exception,e:
#            pass
#        except requests.exceptions.ConnectionError as e:    # This is the correct syntax
#            pass
#        charCount = {}
#        if  r != " ":
#          text = r.text
#          for char in r.text:
#            charCount[char] = charCount.get(char, 0) + 1
#          characters = len(text) - text.count(' ')
#          if characters < 60:
#             jsonData = None

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


        # read problems
        resp, content = client.generic_list(record_id=record_id, data_model="Appointment", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading appointments: %s"%content)
        appoints = simplejson.loads(content)

    else:
        # get record info
        record_id = ""
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
        resp2, content2 = client.carenet_document_list(carenet_id=carenet_id)
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)
        record2 = parse_xml(content2)
        # read problems from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Appointment", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content)
        appoints = simplejson.loads(content)
        
    appoints = map(process_problem, appoints)
    record_label = record.attrib['label']
    num_appoints = len(appoints)
    surl_credentials = client.get_surl_credentials()
    ids=''
    for i in appoints:

       ids+=i['id']+","

#    return HttpResponse(probs,content_type="application/json") 
    return render_template('list', {'record_label': record_label, 'num_appointments' : num_appoints, 
                                    'appointments': appoints, 'in_carenet':in_carenet,'jsonData':jsonData, 'ids':ids,'record_id':record_id,'surl_credentials':surl_credentials})

def new_appointment(request):
    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP
    jsonData = None
    r = " "

    if request.method == "GET":
        return render_template('newappointment',{'jsonData': jsonData})
    else:


        # Fix dates formatted by JQuery into xs:dateTime
        date = request.POST['date'] + 'T00:00:00Z' if request.POST['date'] != '' else ''
        #locality = request.POST['locality']#.encode('utf-8').strip()
#	return HttpResponse(locality)
#        name = locality.decode("utf-8")
     #   for k, v in greek_alphabet.iteritems():
     #      test = locality.replace(k, v)
     #      return HttpResponse(test) 
        #return HttpResponse(test)
        #country = request.POST['country']#.encode('utf-8').strip()
    #    date_resolution = request.POST['date_resolution'] + 'T00:00:00Z' if request.POST['date_resolution'] != '' else ''

        # get the variables and create a problem XML
        params = {'date': date,
                  'time': request.POST['time'],
                   'alert': request.POST['alert'],
                  'appointment_title': request.POST['appointment_title'],
                  'lastname': request.POST['lastname'],
		  'name':request.POST['name'],
                  'comments' : request.POST['comments'],
		  'street_number':request.POST['street_number'],
                  'route':request.POST['route'],
		  'locality':request.POST['locality'],
         	  'country':request.POST['country'],
                  'postal_code':request.POST['postal_code'],
			}

        # Fix dates formatted by JQuery into xs:dateTime                                        
        ##startDate = request.POST['startDate'] + 'T00:00:00Z' if request.POST['startDate'] != '' else ''
        ##endDate = request.POST['endDate'] + 'T00:00:00Z' if request.POST['endDate'] != '' else ''

        # get the variables and create a problem XML
        #params = { 
                  #'startDate': startDate,
                  #  'endDate': endDate,
                  #  'name_title': request.POST['name_title'],

                  #  'name_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                  #  'name_identifier': request.POST['name_identifier'],
                  #  'comments' : request.POST['comments']}
		  

	##	 'code_abbrev':'', 
          ##        'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/', 
            ##      'startDate': startDate, 
              ##    'endDate': endDate, 
                ##  'code_fullname': request.POST['code_fullname'], 
                 ## 'code': request.POST['code'], 
                 ## 'comments' : request.POST['comments']}
        appointment_xml = render_raw('appointment', params, type='xml')
        
        # add the problem
        client = get_indivo_client(request)
        #return HttpResponse(str(problem_xml))
        appointment_xml = appointment_xml.encode('ascii', 'xmlcharrefreplace')
#        resp, content = client.document_create(record_id=request.session['record_id'], body=appointment_xml, 
 #                                              content_type='application/xml')



        limit=int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        query_params = {
         'limit': limit,
         'offset': offset,
         #'order_by': 'startDate',
         'status': 'active',
        }
        carenet_list =[]
        resp, content = client.generic_list(record_id=record_id, data_model="Appointment", body=query_params)

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


        resp, content = client.document_create(record_id=request.session['record_id'], body=appointment_xml,
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
            raise Exception("Error creating new appointment: %s"%content)
        
        # add a notification
        # let's not do this anymore because it's polluting the healthfeed
        client.record_notify(record_id=request.session['record_id'], 
                              body={'content':'a new problem has been added to your problem list'})
        #if request.session['carenet_id']:
        #       resp,content = client.carenet_document_placement(record_id=request.session['record_id'],carenet_id=request.session['carenet_id'],document_id=request.session['document_id'])    
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error creating new problem: %s"%content)
	if request.POST['fromcalendar'] == 1:
           return render_template('newproblem',{'jsonData': jsonData,'record_id':record_id,'fromcalendar':fromcalendar})

        return HttpResponseRedirect(reverse(appointment_list))

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

def one_appointment(request,appointment_id):
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
         resp, content = client.record_specific_document(record_id=record_id, document_id=appointment_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error fetching document: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.record_document_meta(record_id=record_id, document_id=appointment_id)
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
         resp, content = client.carenet_document(carenet_id=carenet_id, document_id=appointment_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error fetching document from carenet: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=appointment_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error fetching document metadata from carenet: %s"%content)
         doc_meta_xml = content
    
    doc = parse_xml(doc_xml)    
    appointment = parse_sdmx_problem(doc, ns=True)
    
    if doc_meta_xml:
        doc_meta = parse_xml(doc_meta_xml)
        meta = parse_meta(doc_meta)
    else:
        meta = None
    
    record_label = record.attrib['label']
    surl_credentials = client.get_surl_credentials()
    
    return render_template('one', {'appointment':appointment, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'appointment_id': appointment_id, 'surl_credentials': surl_credentials, 'jsonData' : jsonData})

def archived_appointment(request,appointment_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=appointment_id, body={'status':'archived', 'reason':'removed by user'})
        return HttpResponseRedirect(reverse(appointment_list))

def carenet_share(request,appointment_id):
        client = get_indivo_client(request)

        in_carenet = request.session.has_key('carenet_id')

        client = get_indivo_client(request)
        record_id = request.session['record_id']
        carenet_id = request.session['carenet_id']
        resp, content = client.carenet_document_placement(record_id=record_id, document_id=appointment_id,carenet_id=carenet_id)
        return HttpResponseRedirect(reverse(appointment_list))


def edit_appointment(request, appointment_id):

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
           resp, content = client.record_specific_document(record_id=record_id, document_id=appointment_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document: %s"%content)
           doc_xml = content

           # read the document's metadata
           resp, content = client.record_document_meta(record_id=record_id, document_id=appointment_id)
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
           resp, content = client.carenet_document(carenet_id=carenet_id, document_id=appointment_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document from carenet: %s"%content)
           doc_xml = content
# read the document's metadata
           resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=appointment_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document metadata from carenet: %s"%content)
           doc_meta_xml = content

       doc = parse_xml(doc_xml)
       appointment = parse_sdmx_problem(doc, ns=True)

       if doc_meta_xml:
           doc_meta = parse_xml(doc_meta_xml)
           meta = parse_meta(doc_meta)
       else:
           meta = None

       record_label = record.attrib['label']
       surl_credentials = client.get_surl_credentials()

       return render_template('one_edit', {'appointment':appointment, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'appointment_id': appointment_id, 'surl_credentials': surl_credentials, 'jsonData': jsonData})
    else:

       # Fix dates formatted by JQuery into xs:dateTime
       date = request.POST['date']
       if date.find("T00:00:00Z")== -1:
           date = request.POST['date'] + 'T00:00:00Z'


        # get the variables and create a problem XML
       
       params = { 'date': date,
                  'time': request.POST['time'],
                  'alert': request.POST['alert'],
                  'appointment_title': request.POST['appointment_title'],
                  'lastname': request.POST['lastname'],
                  'name':request.POST['name'],
                  'comments' : request.POST['comments'],
                  'street_number':request.POST['street_number'],
                  'route':request.POST['route'],
                  'locality':request.POST['locality'],
                  'country':request.POST['country'],
                  'postal_code':request.POST['postal_code'],
		}



                  
                 # 'code_abbrev':'',
                 # 'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                 # 'startDate': startDate,
                 # 'endDate': endDate,
                 # 'code_fullname': request.POST['code_fullname'],
                 # 'code': request.POST['code'],
                 # 'comments' : request.POST['comments']}      
                            
       appointment_xml = render_raw('appointment', params, type='xml')

       client = get_indivo_client(request)
       record_id = request.session.get('record_id', None)
       appointment_xml = appointment_xml.encode('ascii', 'xmlcharrefreplace')
       resp, content = client.document_version(record_id=request.session['record_id'], document_id=appointment_id, body=appointment_xml, content_type='application/xml')
       #resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml, content_type='application/xml')

       if resp['status'] != '200':
          # TODO: handle errors
            raise Exception("Error creating a new appointment: %s"%date_resolution)

       # add a notification
       # let's not do this anymore because it's polluting the healthfeed
       # client.record_notify(record_id=request.session['record_id'],
       #                      body={'content':'a new problem has been added to your problem list'})

       return HttpResponseRedirect(reverse(appointment_list))




def archived_appointments(request):
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

        # read problems
        resp, content = client.generic_list(record_id=record_id, data_model="Appointment", body=query_params)
        #resp, content = client.generic_list(record_id=record_id, data_model="Problem", body=query_params))
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading appointments: %s"%content)
        appoints = simplejson.loads(content)

    else:
        # get record info
        carenet_id = request.session['carenet_id']
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)

        # read problems from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Appointment")
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading appointments from carenet: %s"%content)
        appoints = simplejson.loads(content)

    appoints = map(process_problem, appoints)
    record_label = record.attrib['label']
    num_appointments = len(appoints)

    return render_template('archived_list', {'record_label': record_label, 'num_appointments' : num_appointments,
                                    'appointments': appoints, 'in_carenet':in_carenet, 'jsonData': jsonData })


def restore_appointment(request,appointment_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=appointment_id, body={'status':'active', 'reason':'restored by user'})
        return HttpResponseRedirect(reverse(archived_appointments))
