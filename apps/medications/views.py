"""
Views for the Indivo Problems app

Ben Adida
ben.adida@childrens.harvard.edu

Updated:
Chatzimina Maria
ICS-FORTH
"""

from utils import *
import uuid
import requests
import json
import urllib2
from django.utils import simplejson
from lxml import etree as ET
from xml.dom import minidom
from StringIO import StringIO
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

##    if not request.session.has_key('medications_access_token'):
        # request a request token
    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
    request.session['request_token'] = req_token

    return HttpResponseRedirect(client.auth_redirect_url)
    if 1==2:
       if datetime.datetime.now() > request.session['medications_time'] + datetime.timedelta(minutes=5):

         req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
         request.session['request_token'] = req_token

         return HttpResponseRedirect(client.auth_redirect_url)
       else:
         access_token=request.session['medications_access_token']
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
         return HttpResponseRedirect(reverse(medication_list))


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
    request.session['medications_access_token']=access_token
    request.session['medications_time']=datetime.datetime.now()
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
    return HttpResponseRedirect(reverse(medication_list))

def medication_list(request):
    #status = request.GET.get('status', 'void')
    client = get_indivo_client(request)
    jsonDataQuest = " " 
    in_carenet = request.session.has_key('carenet_id')
    if not in_carenet:
        # get record info
        record_id = request.session['record_id']


        INDIVO_IP = settings.INDIVO_IP

        jsonDataQuest = " "
        r = " " 
#        try:
#          r = requests.get(INDIVO_IP+"/ProfilingServer/getPatientResults?clinicianKey=clinician12.&patientId="+record_id,timeout=20)
#          r.text
#          jsonDataQuest = json.loads(r.text)
#        except Exception,e:
 #         pass
 #       except requests.exceptions.ConnectionError as e:    # This is the correct syntax
 #         pass
 #       charCount = {} 
 #       if r != " ":

  #       text = r.text
  #       for char in r.text:
  #         charCount[char] = charCount.get(char, 0) + 1
  #       characters = len(text) - text.count(' ')
  #       if characters < 60:
  #        jsonDataQuest = " "

        limit=int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
    #status = request.GET.get('status', 'archived')
        query_params = {
         'limit': limit,
         'offset': offset,
        #'order_by': 'startDate',
         'status': 'active',
         }
        client = get_indivo_client(request)


        resp, content = client.record(record_id=record_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)
        
        # read problems
        resp, content = client.generic_list(record_id=record_id, data_model="Medication", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems: %s"%content)
        medications = simplejson.loads(content)

    else:
        record_id=""
        INDIVO_IP = settings.INDIVO_IP
        # get record info
        carenet_id = request.session['carenet_id']
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)

        # read problems from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Medication")
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content)
        medications = simplejson.loads(content)
        
    medications = map(process_problem, medications)
    record_label = record.attrib['label']
    num_medications = len(medications)
    drugsData0 = ""
    drugsData1 = ""
    data = ""
    ids=''
    for i in medications:
       ids+=i['id']+","

    if len(medications) > 0:
      medicat = medications[0]['drugName_title']
      link = INDIVO_IP+"/DrugToDrugInteractions/checkDrugInteractionsInDrugList?drugList="
      if medications:
        for i in xrange(0,len(medications)):
           link += medications[i]['drugName_title']
	   link += ','
      #drugsData0 = medications[0]['drugName_title']
      #if num_medications > 1 :
      #   drugsData1 = medications[1]['drugName_title']
      
    #request = "black"
    #req =requests.get(link, timeout=60)
    #response = req.text
    #data = json.loads(response)   
      
      try:
        req =requests.get(link, timeout=80)
        response = req.text
        data = json.loads(response)
     #  r = requests.get("http://thor.ics.forth.gr:8580/DrugToDrugInteractions/checkDrugInteractionsInDrugList?drugList=Treprostinil,Lepirudin,Morphine (product),Aclarubicin (product),Aclarubicin (product),Clarithromycin 500 MG Extended Release Tablet,montelukast 10 MG Oral Tablet [Singulair],Nitroglycerin 0.4 MG Sublingual Tablet,Ramipril 10 MG Oral Capsule,Chantix Continuing Months Of Therapy Pack,glimepiride 4 MG Oral Tablet,celecoxib 200 MG Oral Capsule [Celebrex],pantoprazole 40 MG Enteric Coated Tablet,Ramipril 10 MG Oral Capsule [Altace],glimepiride 2 MG Oral Tablet,clopidogrel 75 MG Oral Tablet [Plavix],Pramipexole 0.5 MG Oral Tablet [Mirapex],Niacin 1000 MG Extended Release Tablet [Niaspan],")
       #r = requests.get("http://thor.ics.forth.gr:8580/DrugToDrugInteractions/checkDrugToDrugInteractions.json?drugNameA="+drugsData1+"&drugNameB="+drugsData0,timeout=20)
      # temp =  '[{'
      # temp += '"requestResult":"'+r.text+'"}]'
       #request = temp
       #temp = r.text
       #request = json.loads(temp)
       #request = json.loads(r.text)
      except Exception,e:
        pass
      except requests.exceptions.ConnectionError as e:    # This is the correct syntax
        pass
    #url = "http://thor.ics.forth.gr:8580/DrugToDrugInteractions/checkDrugToDrugInteractions.json?drugNameA="+drugsData1+"&drugNameB="+drugsData0
    #try:
       #r12 = requests.get("http://thor.ics.forth.gr:8580/DrugToDrugInteractions/checkDrugToDrugInteractions.json?drugNameA="+drugsData1+"&drugNameB="+drugsData0)
       #temp =  '[{'
       #temp += '"requestResult":"'+r12.text+'"}]'
       #request = temp
       #request = json.loads(temp)
    #except requests.exceptions.ConnectionError as e:    # This is the correct syntax
     #  pass 
    
    if data != " ":
      jsonData = data
      drugNames = []
      alertMessages = []
      drugNameA=''
      drugNameB=''
    
      if jsonData != " ":
       for item in jsonData:
         drugNameA = item.get("drugNameA")
         drugNames.append(drugNameA)
         drugNameB = item.get("drugNameB")
         drugNames.append(drugNameB)
         alertMessage = item.get("interactionDescription")
         alertMessages.append(alertMessage)
       woduplicates = list(set(drugNames))
       interactMedications = ['no' for x in xrange(len(medications))]
   
  
    #interactMedications = map(process_problem, medications) 
  #  for i in xrange(0,len(medications)):
    #    interactMedications[i][0]=medications[i]['drugName_title']
    #   interactMedications[i]='no'

       for i in xrange(0,len(medications)):
	for j in drugNames:
 	  if j.find(medications[i]['drugName_title'])!=-1:

                interactMedications[i]='yes'
         
        
       finalMedications = zip(medications,interactMedications)       

       woduplicates = [s.encode('utf-8') for s in woduplicates]
       alertMessages = [m.encode('utf-8') for m in alertMessages] 
       surl_credentials = client.get_surl_credentials()
          
       return render_template('list', {'record_label': record_label, 'num_medications' : num_medications,
                                    'medications': medications, 'in_carenet':in_carenet,'data':data,'alertMessages':alertMessages,'drugNames':woduplicates,'interactMedications':finalMedications, 'jsonDataQuest': jsonDataQuest,'drugName':drugNames,'data':data,'surl_credentials':surl_credentials,'record_id':record_id,'ids':ids}) 
      
    else:
      surl_credentials = client.get_surl_credentials()
      jsonDataQuest = ""
      return render_template('list', {'record_label': record_label, 'num_medications' : num_medications, 'jsonDataQuest': jsonDataQuest,
                                    'medications': medications, 'in_carenet':in_carenet,'data':data,'record_id':record_id,'surl_credentials':surl_credentials,'ids':ids}) 
  
 
def new_medication(request):	

    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP 
    jsonData = " "
    r = " "

    if request.method == "GET":
        return render_template('newmedication',{'jsonData': jsonData})
    else:
       
         # Fix dates formatted by JQuery into xs:dateTime
        startDate = request.POST['startDate'] + 'T00:00:00Z' if request.POST['startDate'] != '' else ''
    	date = request.POST['date'] + 'T00:00:00Z' if request.POST['date'] != '' else ''
        endDate = request.POST['endDate'] + 'T00:00:00Z' if request.POST['endDate'] != '' else ''
      	drugName_title = request.POST['drugName_title'] 
        #endDate = request.POST['endDate'] + 'T00:00:00Z' if request.POST['endDate'] != '' else ''

        # get the variables and create a problem XML

        params = {'drugName_title': request.POST['drugName_title'],
                  'drugName_system': 'http://purl.bioontology.org/ontology/RXNORM/',
                  'drugName_identifier': request.POST['drugName_identifier'],
                  'endDate': request.POST['endDate'],
                 'frequency_value': request.POST['frequency_value'],
                  'frequency_unit': request.POST['frequency_unit'],
                  'instructions': request.POST['instructions'], 
                  'provenance_title': request.POST['provenance_title'],
                  'provenance_system': 'http://smartplatforms.org/terms/codes/MedicationProvenance#',
                  'provenance_identifier':request.POST['provenance_identifier'],
                  'quantity_value':request.POST['quantity_value'],
                  'quantity_unit':request.POST['quantity_unit'],    
                  'startDate': request.POST['startDate'],
                  'date': request.POST['date'],
                  'dispenseDaysSupply': request.POST['dispenseDaysSupply'],
                  'pbm': request.POST['pbm'],
                  'pharmacy_ncpdpid': request.POST['pharmacy_ncpdpid'],
                  'pharmacy_org': request.POST['pharmacy_org'],
                  'pharmacy_adr_country': request.POST['pharmacy_adr_country'],
                  'pharmacy_adr_city': request.POST['pharmacy_adr_city'],
                  'pharmacy_adr_postalcode': request.POST['pharmacy_adr_postalcode'],
                  'pharmacy_adr_street': request.POST['pharmacy_adr_street'],
                  'provider_dea_number': request.POST['provider_dea_number'],
                  'provider_npi_number': request.POST['provider_npi_number'],
                  'provider_email': request.POST['provider_email'],
                  'provider_name_given': request.POST['provider_name_given'],
                  'provider_name_family': request.POST['provider_name_family'],
                  'provider_tel_1_type': request.POST['provider_tel_1_type'],
                  'provider_tel_1_number': request.POST['provider_tel_1_number'],
                  'provider_tel_1_preferred_p': request.POST['provider_tel_1_preferred_p'],
                  'quantityDispensed_value': request.POST['quantityDispensed_value'],
                  'quantityDispensed_unit': request.POST['quantityDispensed_unit']}
	          #'date2': request.POST['date2'],
                  #'dispenseDaysSupply2': request.POST['dispenseDaysSupply2'],
                  #'pbm': request.POST['pbm'],
                  #'pharmacy_ncpdpid': request.POST['pharmacy_ncpdpid'],
                  #'pharmacy_org': request.POST['pharmacy_org'],
                  #'pharmacy_adr_country': request.POST['pharmacy_adr_country'],
                  #'pharmacy_adr_city': request.POST['pharmacy_adr_city'],
                  #'pharmacy_adr_postalcode': request.POST['pharmacy_adr_postalcode'],
                  #'pharmacy_adr_street': request.POST['pharmacy_adr_street'],
                  #'provider_dea_number': request.POST['provider_dea_number'],
                  #'provider_npi_number': request.POST['provider_npi_number'],
                  #'provider_email': request.POST['provider_email'],
                  #'provider_name_given': request.POST['provider_name_given'],
                  #'provider_name_family': request.POST['provider_name_family'],
                  #'provider_tel_1_type': request.POST['provider_tel_1_type'],
                  #'provider_tel_1_number': request.POST['provider_tel_1_number'],
                  #'provider_tel_1_preferred_p': request.POST['provider_tel_1_preferred_p'],
                  #'quantityDispensed_value': request.POST['quantityDispensed_value'],
                  #'quantityDispensed_unit': request.POST['quantityDispensed_unit']}
                  
             
        medication_xml = render_raw('medication', params, type='xml')
        #fill_xml = render_raw('fill',params,type='xml')

        # add the problem
        client = get_indivo_client(request)
        medication_xml = medication_xml.encode('ascii', 'xmlcharrefreplace')
#        resp, content = client.document_create(record_id=request.session['record_id'], body=medication_xml, 
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
        resp, content = client.generic_list(record_id=record_id, data_model="Medication", body=query_params)

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

        resp, content = client.document_create(record_id=request.session['record_id'], body=medication_xml,
                                               content_type='application/xml')

        if resp['status'] != '200':
           raise Exception("Error creating new medication: %s"%content)
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
            raise Exception("Error creating new medication: %s"%content)
        
        # add a notification
        # let's not do this anymore because it's polluting the healthfeed
        client.record_notify(record_id=request.session['record_id'], 
                             body={'content':'a new medication has been added to your medications list'})
        #r = requests.get("http://thor.ics.forth.gr:8580/ProfilingServer/getPatientResults?clinicianKey=clinician12.&patientId=396i@gqr!a")
    	#r.text
    	#drugsData = json.loads(r.text)
	if request.POST['fromcalendar'] == 1:
           return render_template('newproblem',{'jsonData': jsonData,'record_id':record_id,'fromcalendar':fromcalendar})
	
        return HttpResponseRedirect(reverse(medication_list ))

def code_lookup(request):
    client = get_indivo_client(request)
    
    query = request.GET['query']
    
    # reformat this for the jQuery autocompleter
    resp, content = client.coding_system_query(system_short_name='rxterms', body={'q':query})
    if resp['status'] != '200':
        # TODO: handle errors
        # But this Indivo instance might not support codingsystem lookup, so let's pass
        pass
    codes = simplejson.loads(content)
    formatted_codes = {'query': query, 'suggestions': [c['consumer_value'] for c in codes], 'data': codes}
    
    return HttpResponse(simplejson.dumps(formatted_codes), mimetype="text/plain")

def one_medication(request,medication_id):
    client = get_indivo_client(request)
    record_id = request.session.get('record_id', None)
    INDIVO_IP = settings.INDIVO_IP
    jsonData = " "
    r= " "

    if record_id:
        # get record info
         resp, content = client.record(record_id=record_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error reading Record info: %s"%content)
         record = parse_xml(content)
        
        # read the document
         resp, content = client.record_specific_document(record_id=record_id, document_id=medication_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error fetching document: %s"%content)
         doc_xml = content
    
        # read the document's metadata
         resp, content = client.record_document_meta(record_id=record_id, document_id=medication_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error fetching document metadata: %s"%content)
         doc_meta_xml = content

         limit=int(request.GET.get('limit', 100))
         offset = int(request.GET.get('offset', 0))
    #status = request.GET.get('status', 'archived')
         query_params = {
         'limit': limit,
         'offset': offset,
        #'order_by': 'startDate',
         'status': 'active',
         }


         resp, content = client.generic_list(record_id=record_id, data_model="Medication", body=query_params)
         if resp['status'] != '200':
              # TODO: handle errors
            raise Exception("Error reading problems: %s"%content)
         medications = simplejson.loads(content)

    else:
         # get record info
         carenet_id = request.session['carenet_id']
         resp, content = client.carenet_record(carenet_id=carenet_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error reading Record info: %s"%content)
         record = parse_xml(content)
        
        # read the document
         resp, content = client.carenet_document(carenet_id=carenet_id, document_id=medication_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error fetching document from carenet: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=medication_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error fetching document metadata from carenet: %s"%content)
         doc_meta_xml = content

         limit=int(request.GET.get('limit', 100))
         offset = int(request.GET.get('offset', 0))
         query_params = {
         'limit': limit,
         'offset': offset,
        #'order_by': 'startDate',
         'status': 'active',
         }


         resp, content = client.generic_list(record_id=record_id, data_model="Medication", body=query_params)
         if resp['status'] != '200':
              # TODO: handle errors
            raise Exception("Error reading problems: %s"%content)
         medications = simplejson.loads(content) 

#    return HttpResponse(ET.fromstring(doc_xml))
#    tree = ET.XML(doc_xml)
#    ns=False
#    test = ''
#    def _t(tag):
#        return NS+tag if ns else tag

#    for field in tree.find(_t('Model')).findall(_t('Field')):
#             test += field
#    return HttpResponse(test)    
 #   root = tree.getroot()
#    test=[] 
#    root = ET.fromstring(doc_xml)
#    for child in root:
#        for i in child:
#         test.append(i.attrib)
#    return HttpResponse(test)
#    for te in root.findall('fulfillemtns'):
#       return HttpResponse(te) 

#    eleos = ET.parse(StringIO(doc_xml))
#    return HttpResponse(eleos.find('drugName_title'))
#    test = parse_xml(doc_xml)
#    return HttpResponse(doc_xml)
#    test = ET.XML(doc_xml)
#    return HttpResponse(test.findall('.//Medication/drugName_title'))
#    etree = test.find('fulfillments')
#    return HttpResponse(etree)
#    root = test.getroot()
#    return HttpResponse(root.tag)
#    return HttpResponse(root.text)
#    uuid = root.find('fulfillemnts')
#    return HttpResponse(uuid.text) 
    doc = parse_xml(doc_xml)
    fulfillments=''
    for i in medications:
        if i['__documentid__']== medication_id:
	     fulfillments=i['fulfillments']

    medication = parse_sdmx_problem(doc, ns=True)
    if doc_meta_xml:
        doc_meta = parse_xml(doc_meta_xml)
        meta = parse_meta(doc_meta)
    else:
        meta = None

    record_label = record.attrib['label']
    surl_credentials = client.get_surl_credentials()
 
    return render_template('one', {'medication':medication, 'fulfillments':fulfillments,'record_label': record_label, 'meta': meta, 'record_id': record_id, 'medication_id': medication_id, 'surl_credentials': surl_credentials,'jsonData': jsonData})


NS = "{http://indivo.org/vocab/xml/documents#}"

def archived_medication(request,medication_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=medication_id, body={'status':'archived', 'reason':'removed by user'})
        return HttpResponseRedirect(reverse(medication_list))
  
 
def edit_medication(request,medication_id):
    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP
    jsonData = " "
    r = " "
    if request.method == "GET":

       client = get_indivo_client(request)
       record_id = request.session.get('record_id')

       if record_id:
           # get record info
           resp, content = client.record(record_id=record_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error reading Record info: %s"%content)
           record = parse_xml(content)

           # read the document
           resp, content = client.record_specific_document(record_id=record_id, data_model="Medication",document_id=medication_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document: %s"%content)
           doc_xml = content


           # read the document's metadata
           resp, content = client.record_document_meta(record_id=record_id, data_model="Medication",document_id=medication_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document metadata: %s"%content)
           doc_meta_xml = content

           limit=int(request.GET.get('limit', 100))
           offset = int(request.GET.get('offset', 0))
           query_params = {
         'limit': limit,
         'offset': offset,
        #'order_by': 'startDate',
         'status': 'active',
         }


           resp, content = client.generic_list(record_id=record_id, data_model="Medication", body=query_params)
           if resp['status'] != '200':
               # TODO: handle errors
              raise Exception("Error reading problems: %s"%content)
           medications = simplejson.loads(content)

       else:
           # get record info
           carenet_id = request.session['carenet_id']
           resp, content = client.carenet_record(carenet_id=carenet_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error reading Record info: %s"%content)
           record = parse_xml(content)

           # read the document
           resp, content = client.carenet_document(carenet_id=carenet_id, data_model="Medication",document_id=medication_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document from carenet: %s"%content)
           doc_xml = content
     
           limit=int(request.GET.get('limit', 100))
           offset = int(request.GET.get('offset', 0))
           query_params = {
           'limit': limit,
           'offset': offset,
        #'order_by': 'startDate',
           'status': 'active',
           }
 

           resp, content = client.generic_list(record_id=record_id, data_model="Medication", body=query_params)
           if resp['status'] != '200':
              # TODO: handle errors
             raise Exception("Error reading problems: %s"%content)
           medications = simplejson.loads(content)

       doc = parse_xml(doc_xml)
       medication = parse_sdmx_problem(doc, ns=True)
       

       if doc_meta_xml:
           doc_meta = parse_xml(doc_meta_xml)
           meta = parse_meta(doc_meta)
       else:
           meta = None
       
       
       record_label = record.attrib['label']
       surl_credentials = client.get_surl_credentials()

       fulfillments=''
       for i in medications:
        if i['__documentid__']== medication_id:
             fulfillments=i['fulfillments']
 

       #return render_template('one_edit', {'allergy':allergy 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'allergy_id': allergy_id, 'surl_credentials': surl_credentials})
       return render_template('one_edit', {'medication':medication, 'fulfillments':fulfillments,'record_label': record_label, 'meta': meta, 'record_id': record_id, 'medication_id': medication_id, 'surl_credentials': surl_credentials, 'jsonData': jsonData})
    else:
        #formatted by JQuery into xs:dateTime
        # Fix dates formatted by JQuery into xs:dateTime 
        #endDate = request.POST['endDate'] + 'T00:00:00Z' if request.POST['endDate'] != '' else ''
        date = request.POST['date']
        if date.find("T00:00:00Z")!= -1:
            date = request.POST['date'].replace('T00:00:00Z','')
#        if date.find("T00:00:00Z")== -1:
 #           date = request.POST['date'] + 'T00:00:00Z'
        startDate = request.POST['startDate']
 
        if startDate.find("T00:00:00Z")!= -1:
            startDate = request.POST['startDate'].replace('T00:00:00Z','')

#        if startDate.find("T00:00:00Z")== -1:
 #           startDate = request.POST['startDate'] + 'T00:00:00Z'
        endDate = request.POST['endDate']

        if endDate.find("T00:00:00Z")!= -1:
            endDate = request.POST['endDate'].replace('T00:00:00Z','')
#        if endDate.find("T00:00:00Z")== -1:
 #           endDate = request.POST['endDate'] + 'T00:00:00Z'

        # get the variables and create a problem XML

        #endDate = request.POST['endDate'] + 'T00:00:00Z' if request.POST['endDate'] != '' else ''


        # get the variables and create a problem XML

        params = {'drugName_title': request.POST['drugName_title'],
                  'drugName_system': 'http://purl.bioontology.org/ontology/RXNORM/',
                  'drugName_identifier': request.POST['drugName_identifier'],
                  'endDate': request.POST['endDate'],
                 'frequency_value': request.POST['frequency_value'],
                  'frequency_unit': request.POST['frequency_unit'],
                  'instructions': request.POST['instructions'],
                  'provenance_title': request.POST['provenance_title'],
                  'provenance_system': 'http://smartplatforms.org/terms/codes/MedicationProvenance#',
                  'provenance_identifier':request.POST['provenance_identifier'],
                  'quantity_value':request.POST['quantity_value'],
                  'quantity_unit':request.POST['quantity_unit'],
                  'startDate': request.POST['startDate'],
                  'date': request.POST['date'],
                  'dispenseDaysSupply': request.POST['dispenseDaysSupply'],
                  'pbm': request.POST['pbm'],
                  'pharmacy_ncpdpid': request.POST['pharmacy_ncpdpid'],
                  'pharmacy_org': request.POST['pharmacy_org'],
                  'pharmacy_adr_country': request.POST['pharmacy_adr_country'],
                  'pharmacy_adr_city': request.POST['pharmacy_adr_city'],
                  'pharmacy_adr_postalcode': request.POST['pharmacy_adr_postalcode'],
                  'pharmacy_adr_street': request.POST['pharmacy_adr_street'],
                  'provider_dea_number': request.POST['provider_dea_number'],
                  'provider_npi_number': request.POST['provider_npi_number'],
                  'provider_email': request.POST['provider_email'],
                  'provider_name_given': request.POST['provider_name_given'],
                  'provider_name_family': request.POST['provider_name_family'],
                  'provider_tel_1_type': request.POST['provider_tel_1_type'],
                  'provider_tel_1_number': request.POST['provider_tel_1_number'],
                  'provider_tel_1_preferred_p': request.POST['provider_tel_1_preferred_p'],
                  'quantityDispensed_value': request.POST['quantityDispensed_value'],
                  'quantityDispensed_unit': request.POST['quantityDispensed_unit']}




        medication_xml = render_raw('medication', params, type='xml') # gia kapoio logo den douleuei kanonika. eleos
        client = get_indivo_client(request)
        record_id = request.session.get('record_id', None)

        medication_xml2 = medication_xml.replace('>None<','><')        
        medication_xml = medication_xml2.encode('ascii', 'xmlcharrefreplace')

       # add the problem
       #resp, content = client.record_app_document_create_or_update(pha_email="procedures@apps.indivo.org", document_id=procedure_id, body=procedure_xml)

        resp, content = client.document_version(record_id=record_id, document_id=medication_id, body=medication_xml, content_type='application/xml')
       #resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml, content_type='application/xml')

        if resp['status'] != '200':
           # TODO: handle errors
            raise Exception("Error editing medication: %s"%resp)
 # add a notification
       # let's not do this anymore because it's polluting the healthfeed
       # client.record_notify(record_id=request.session['record_id'],
       #                      body={'content':'a new problem has been added to your problem list'})



        return HttpResponseRedirect(reverse(medication_list))


def archived_medications(request):
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
        resp, content = client.generic_list(record_id=record_id, data_model="Medication", body=query_params)
        #resp, content = client.generic_list(record_id=record_id, data_model="Problem", body=query_params))
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems: %s"%content)
        medications = simplejson.loads(content)

    else:
        # get record info
        carenet_id = request.session['carenet_id']
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)

        # read problems from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Medication")
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content)
        medications = simplejson.loads(content)

    medications = map(process_problem, medications)
    record_label = record.attrib['label']
    num_medications = len(medications)

    return render_template('archived_list', {'record_label': record_label, 'num_medications' : num_medications,
                                    'medications': medications, 'in_carenet':in_carenet, 'jsonData':jsonData})


def restore_medication(request,medication_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=medication_id, body={'status':'active', 'reason':'restored by user'})
        return HttpResponseRedirect(reverse(archived_medications))



def add_fill(request,medication_id):
    if request.method == "GET":
        return render_template('newfill')
    else:

         # Fix dates formatted by JQuery into xs:dateTime
       
        date = request.POST['date'] + 'T00:00:00Z' if request.POST['date'] != '' else ''
      
        #endDate = request.POST['endDate'] + 'T00:00:00Z' if request.POST['endDate'] != '' else ''

        # get the variables and create a problem XML

        params = {'date': request.POST['date'],
                  'dispenseDaysSupply': request.POST['dispenseDaysSupply'],
                  'pbm': request.POST['pbm'],
	          'medication_id': {"fk":medication_id},
                  'pharmacy_ncpdpid': request.POST['pharmacy_ncpdpid'],
                  'pharmacy_org': request.POST['pharmacy_org'],
                  'pharmacy_adr_country': request.POST['pharmacy_adr_country'],
                  'pharmacy_adr_city': request.POST['pharmacy_adr_city'],
                  'pharmacy_adr_postalcode': request.POST['pharmacy_adr_postalcode'],
                  'pharmacy_adr_street': request.POST['pharmacy_adr_street'],
                  'provider_dea_number': request.POST['provider_dea_number'],
                  'provider_npi_number': request.POST['provider_npi_number'],
                  'provider_email': request.POST['provider_email'],
                  'provider_name_given': request.POST['provider_name_given'],
                  'provider_name_family': request.POST['provider_name_family'],
                  'provider_tel_1_type': request.POST['provider_tel_1_type'],
                  'provider_tel_1_number': request.POST['provider_tel_1_number'],
                  'provider_tel_1_preferred_p': request.POST['provider_tel_1_preferred_p'],
                  'quantityDispensed_value': request.POST['quantityDispensed_value'],
                  'quantityDispensed_unit': request.POST['quantityDispensed_unit']}
        medication_xml = render_raw('fill', params, type='xml')

        # add the problem
        client = get_indivo_client(request)
        resp, content = client.document_create(record_id=request.session['record_id'],body=medication_xml,
                                               content_type='application/xml')
      
        #resp, content = client.document_create_by_rel(record_id=request.session['record_id'],body=medication_xml, REL='annotation', document_id=medication_id,content_type='application/xml')

        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error creating new fill: %s"%content)

        # add a notification
        # let's not do this anymore because it's polluting the healthfeed
        client.record_notify(record_id=request.session['record_id'],
                              body={'content':'a new fill has been added to your problem list'})

        return HttpResponseRedirect(reverse(medication_list))

