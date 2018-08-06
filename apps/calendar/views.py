"""
Views for the Calendar app
Chatzimina Maria

"""

from utils import *
import uuid
import urllib
import urllib2
import sys
import urllib2
from urllib2 import HTTPError
#import urllib.request
from urllib import urlopen
import xml.etree.ElementTree as ET
from lxml import etree
import urllib, re, copy
import MySQLdb
import requests
import json
import utils
import urlparse
import psycopg2
#import oursql
from django.utils import simplejson
import time
import datetime
import string 
import pytz

utc=pytz.UTC

from datetime import date
from datetime import timedelta

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

##    if not request.session.has_key('calendars_access_token'):
        # request a request token
    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
    request.session['request_token'] = req_token

    return HttpResponseRedirect(client.auth_redirect_url)
    if 1==2:
       if datetime.datetime.now() > request.session['calendars_time'] + datetime.timedelta(minutes=5):

         req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
         request.session['request_token'] = req_token

         return HttpResponseRedirect(client.auth_redirect_url)
       else:
         access_token=request.session['calendars_access_token']
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
         return HttpResponseRedirect(reverse(problem_list))



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
        return HttpResponse("Something went wrong. Please refresh the page.")

    # get the indivo client and use the request token as the token for the exchange
    client = get_indivo_client(request, with_session_token=False)
    client.update_token(token_in_session)
    access_token = client.exchange_token(oauth_verifier)
    request.session['calendars_access_token']=access_token
    request.session['calendars_time']=datetime.datetime.now()
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
    return HttpResponseRedirect(reverse(problem_list))


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

    return HttpResponseRedirect(reverse(problem_list))

def problem_list(request):


    client = get_indivo_client(request)
    appointments=''
    probs=''
    procedures=''
    medications=''
    in_carenet = request.session.has_key('carenet_id')
    appointments = ''
#    record = client.record_get_owner(record_id=request.session['record_id'])
 #   return HttpResponse(record)
    if not in_carenet:
        record_id = request.session['record_id']


        client.record_pha_setup(record_id=record_id,pha_email = 'calendar@apps.indivo.org')

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
        resp, content = client.generic_list(record_id=record_id, data_model="Problem", body=query_params)
	
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems: %s"%content)
        probs = simplejson.loads(content)

           
        respA, contentA = client.generic_list(record_id=record_id, data_model="Medication", body=query_params)
        if respA['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading allergies: %s"%content)
        medications = simplejson.loads(contentA)
 
        respP, contentP = client.generic_list(record_id=record_id, data_model="Procedure", body=query_params)
        if respP['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading allergies: %s"%content)
        procedures = simplejson.loads(contentP)
        respAp, contentAp = client.generic_list(record_id=record_id, data_model="Appointment", body=query_params)
        if respAp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading allergies: %s"%content)
        appointments = simplejson.loads(contentAp)



    else:
        # get record info
        record_id=""
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
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Problem", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content)
        probs = simplejson.loads(content)
     
        respA, contentA = client.carenet_generic_list(carenet_id=carenet_id, data_model="Medication", body=query_params)
        if respA['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content)
        medications = simplejson.loads(contentA)
            
        respP, contentP = client.carenet_generic_list(carenet_id=carenet_id, data_model="Procedure", body=query_params)#generic_list(carenet_id=carenet_id, data_model="Procedure", body=query_params)
        if respP['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading allergies: %s"%content)
        procedures = simplejson.loads(contentP)

        respAp, contentAp = client.carenet_generic_list(carenet_id=carenet_id, data_model="Appointment", body=query_params)
        if respAp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading allergies: %s"%content)
        appointments = simplejson.loads(contentAp)



   # probs=""
   # medications=""
   # procedures=""

    probs = map(process_problem, probs)
    record_label = record.attrib['label']
    num_problems = len(probs)

    medications = map(process_problem, medications)
    record_label = record.attrib['label']
    num_medications = len(medications)

    procedures = map(process_problem, procedures)
    record_label = record.attrib['label']
    num_procedures = len(procedures)

    appointments = map(process_problem, appointments)
    record_label = record.attrib['label']
    num_appointments = len(appointments)
   

    if num_problems > 0:
     for x in range(0, num_problems): 
      problemStartDate = probs[x].get('startDate')
      problemStartDateT = problemStartDate.replace ("T", " ")
      problee = problemStartDateT.replace("Z"," ")
      probleee = problee.replace("00","10")
      probs[x]["startDate"] = probleee
      problemEndDate = probs[x].get("endDate")
      if problemEndDate is not None:
         problemEndDateT = problemEndDate.replace("T"," ")
         problemEndDateZ = problemEndDateT.replace("Z"," ")
         problemEndDateZZ =  problemEndDateZ.replace("00","10")
         probs[x]["endDate"] = problemEndDateZZ
         listproblemEndDateZZ =  problemEndDateZZ.split('-', 3 )
         probs[x]["yearE"] = listproblemEndDateZZ[0]
         probs[x]["monthE"] = int(listproblemEndDateZZ[1])-1
         probs[x]["dayE"] = listproblemEndDateZZ[2].split(' ')[0]#[:-10]
      else:
         probs[x]["endDate"] = '2100-02-01 10:10:10' 
         probs[x]["yearE"] = int('2100')
         probs[x]["monthE"] = int('02')
         probs[x]["dayE"] = int('01')
      listProblee = problee.split('-', 3 )
      probs[x]["yearS"] = listProblee[0]
      probs[x]["monthS"] = int(listProblee[1])-1

      probs[x]["dayS"] = listProblee[2].split(' ')[0] #[:-10]
 
#      listproblemEndDateZZ =  problemEndDateZZ.split('-', 3 )
#      probs[x]["yearE"] = listproblemEndDateZZ[0]
#      probs[x]["monthE"] = int(listproblemEndDateZZ[1])-1
#      probs[x]["dayE"] = listproblemEndDateZZ[2][:-10]



    if num_medications > 0: 
     for x in range(0, num_medications):
      problemStartDate = medications[x].get('startDate')
      problemStartDateT = problemStartDate.replace ("T", " ")
      problee = problemStartDateT.replace("Z"," ")
      medications[x]["startDate"] = problee
      problemEndDate = medications[x].get('endDate')
      if problemEndDate is not None:
        problemEndDateT = problemEndDate.replace("T"," ")
        problemEndDateZ = problemEndDateT.replace("Z"," ")
        problemEndDateZZ =  problemEndDateZ.replace("00","10")
        medications[x]["endDate"] = problemEndDateZZ
        listproblemEndDateZ = problemEndDateZ.split('-',3)
        medications[x]["yearE"] = listproblemEndDateZ[0]
        medications[x]["monthE"] = int(listproblemEndDateZ[1])-1
        medications[x]["dayE"] = listproblemEndDateZ[2]
      else:
         medications[x]["endDate"] = '2100-02-01 10:10:10'
         medications[x]["yearE"] = int('2100')
         medications[x]["monthE"] = int('02')
         medications[x]["dayE"] = int('01')

      listProblee = problee.split('-', 3 )
      medications[x]["yearS"] = listProblee[0]
      medications[x]["monthS"] = int(listProblee[1])-1
      medications[x]["dayS"] = listProblee[2]

    if num_procedures > 0:
     for x in range(0, num_procedures):
      problemStartDate = procedures[x].get('date_performed')
      problemStartDateT = problemStartDate.replace ("T", " ")
      problee = problemStartDateT.replace("Z"," ")
      procedures[x]["date_performed"] = problee
      listproblee = problee.split('-',3)
      procedures[x]["year"] = listproblee[0]
      procedures[x]["month"] = int(listproblee[1])-1
      procedures[x]["day"] = listproblee[2][:-10]
     
    if num_appointments > 0:
       for x in range(0, num_appointments):
 	appointmentDate = appointments[x].get('date')
        startDateAp = appointmentDate.replace("T", " ")
        startDateeAp = startDateAp.replace("Z"," ")
        listAppoin = startDateeAp.split('-',3)

        appointments[x]["year"] = listAppoin[0]
        appointments[x]["month"] = int(listAppoin[1])-1
        appointments[x]["day"] = listAppoin[2][:-10]


    day = time.strftime("%d")
    monthh = time.strftime("%m")
    month = int(monthh) - 1
    monthTimeline = monthh
    year = time.strftime("%Y")
    previousyear = year
    if month == 0:
      previousyear = int(year) - 1
    if month == 1: 
      previousyear = int(year) - 1
    today = datetime.date.today()
    monthString = str(month)
    finalM = "false"
    if int(monthh) < 10:
        finalM = "true"
    #date=time.strptime(argv[1], "%y-%m-%d");
    #newdate=date + datetime.timedelta(days=1)
    nextDate= date.today() - timedelta(days=32)
    nextDayy = nextDate.strftime("%m")
    nextDay = int(nextDayy)-1
#    datee = time.strftime("%Y-%m-%d") 
      
    todayDate=datetime.datetime.now()
    #now = datetime.datetime.now()
    #todayDate= now.strftime("%Y-%m-%d %H:%M")

    try:
               conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
#               conn.autocommit = True
               conn.set_isolation_level(0)
               conn.commit()
               cursor = conn.cursor()

    except psycopg2.DatabaseError, e:
                 print "Cannot connect to db"
    document_ids=[] 
    alertList = []
    timelist = []
    results = '' 
    if appointments:
     for i in appointments:
   
        document_ids.append(i['id'])

     appointments_ids = []
     for ap_id in document_ids:
         appointments_ids.append(ap_id)


     select_string = '' 

     if len(appointments_ids) > 1:
      for i in xrange(0,(len(appointments_ids)-1)):
          
          select_string += "document_id='"+str(appointments_ids[i])+"' OR "
      select_string += "document_id='"+str(appointments_ids[len(appointments_ids)-1])+"'"
     else:
      select_string = "document_id='"+str(appointments_ids[0])+"'"


#     results = ''
     try:
               cursor.execute('SELECT id FROM indivo_fact where '+select_string)
               results = cursor.fetchall()
#               if results != '':
#
 #                 account_id_returned = results[0][0]
  #                secret_returned = results[0][1]
     except psycopg2.DatabaseError, e:
	       return HttpResponse(e)
               if conn:
                 conn.rollback()
                 print 'Error %s' % e

     select_string_app = ''

     if len(results) > 1:
      for i in xrange(0,(len(results)-1)):

          select_string_app += "fact_ptr_id='"+str(results[i][0])+"' OR "
      select_string_app += "fact_ptr_id='"+str(results[len(results)-1][0])+"'"
     else:
      select_string_app = "fact_ptr_id='"+str(results[0][0])+"'"



     appointments_results = ''

     
     try:
               cursor.execute('SELECT date, '+'"'+'time'+'", appointment_title,alert FROM indivo_appointment where '+select_string_app)
               appointments_results = cursor.fetchall()
#               if results != '':
#
 #                 account_id_returned = results[0][0]
  #                secret_returned = results[0][1]
     except psycopg2.DatabaseError, e:
               return HttpResponse(e)
               if conn:
                 conn.rollback()

                 print 'Error %s' % e

     if appointments_results !='':
	for i in appointments_results:

#          if i[3] == '1':
               appointmentDate = i[0].replace(tzinfo=utc)
               shmera = todayDate.replace(tzinfo=utc)
               difference = shmera-appointmentDate
               hour = int(i[1].split(":")[0])
              
               minutes = int(i[1].split(":")[1])
               shmeraTime = shmera.replace(hour=hour, minute=minutes)
               timelist.append(difference.days)
               if difference.days == -1:

                 if i[3] =='1':
                    alertList.append(i)

               if difference.days == -2:
                 if i[3] == '2':
                    alertList.append(i)
               if difference.days == 0:
                 differenceTime = shmeraTime-appointmentDate

                 if (25 <= difference.seconds// 60 % 60) <= 40:
 		   if i[3] == '30':
 	            alertList.append(i)

                 if (3 <= difference.seconds// 60 % 60) <= 6:
                   if i[3] == '5':
                    alertList.append(i)
                 if (55 <= difference.seconds// 60 % 60) <= 65:
                   if i[3] == '60':
                    alertList.append(i)


    
     
#    alertList=simplejson.loads(alertList) 

    return render_template('list', {'record_label': record_label, 'num_problems' : num_problems,
                                    'problems': probs, 'in_carenet':in_carenet,'medications':medications,'procedures':procedures,'appointments':appointments,'day':day,'month':month,'year':year,'monthTimeline':monthTimeline,'finalM':finalM, 'nextDay':nextDay,'monthh':monthh,'previousyear':previousyear,'record_id':record_id, 'alertList':alertList, 'results':results,'timelist':timelist})



def share_step(request):

     return HttpResponse('tipote')


def new_problem_calendar(request):

    record_id = request.session['record_id']
    
    jsonData = None
    r="" 
    client = get_indivo_client(request)
    surl_credentials = client.get_surl_credentials()

    if request.method == "GET":
        return render_template('newproblem',{'jsonData': jsonData,'record_id':record_id})
    else:


        # Fix dates formatted by JQuery into xs:dateTime
        date_onset = request.POST['date_onset'].replace(' A','T')      # + 'T00:00:00Z' if request.POST['date_onset'] != '' else ''
        date_onset = date_onset.replace('F','Z')
        date_resolution = request.POST['date_resolution'].replace(' A','T')      #+ 'T00:00:00Z' if request.POST['date_resolution'] != '' else ''
        date_resolution = date_resolution.replace('F','Z')
        code_fullname = request.POST['code_fullname']

        #return HttpResponse(code_fullname)
        if date_resolution == '__:__ __':
             date_resolution = ''
        # get the variables and create a problem XML
        params = {'date_onset': date_onset,
                  'date_resolution': date_resolution,
                  'code_fullname': code_fullname,
                  'name_system':'http://purl.bioontology.org/ontology/SNOMEDCT/',
                  'code': request.POST['code'],
                  'category':request.POST['category'],
                  'comments' : request.POST['comments']}

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


        ##       'code_abbrev':'',
          ##        'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
            ##      'startDate': startDate,
              ##    'endDate': endDate,
                ##  'code_fullname': request.POST['code_fullname'],
                 ## 'code': request.POST['code'],
                 ## 'comments' : request.POST['comments']}
        problem_xml = render_raw('problem', params, type='xml')

        # add the problem
        client = get_indivo_client(request)


        problem_xml= problem_xml.encode('ascii', 'xmlcharrefreplace')#encode('utf-8')


 	limit=int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
    #status = request.GET.get('status', 'archived')
        query_params = {
         'limit': limit,
         'offset': offset,
         #'order_by': 'startDate',
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
#               for elem in tree.iter():
 #                   test +=str(elem.tag)

               Document = tree.findall(".//Carenet")

               for e in Document:
                   carenet_list.append( e.attrib.get('id'))

        resp, content = client.document_create(record_id=request.session['record_id'], body=problem_xml,
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

               client = get_indivo_client(request)
               surl_credentials = client.get_surl_credentials()
               return render_template('share_step', {'record_id':record_id,'carenet_list':carenet_list,'document_id':str(new_document_id),'surl_credentials':surl_credentials})


        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error creating new problem: %s"%content)

        # add a notification
        # let's not do this anymore because it's polluting the healthfeed
        client.record_notify(record_id=request.session['record_id'],
                              body={'content':'a new problem has been added to your problem list'})
        #if request.session['carenet_id']:
        #       resp,content = client.carenet_document_placement(record_id=request.session['record_id'],carenet_id=request.session['carenet_id'],document_id=request.session['document_id'])
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error creating new problem: %s"%content)

        return HttpResponseRedirect(reverse(problem_list))



def new_medication_calendar(request):

    record_id = request.session['record_id']

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
        client.record_notify(record_id=request.session['record_id'], body={'content':'a new medication has been added to your medications list'})
        #r = requests.get("http://thor.ics.forth.gr:8580/ProfilingServer/getPatientResults?clinicianKey=clinician12.&patientId=396i@gqr!a")
        #r.text
        #drugsData = json.loads(r.text)

        return HttpResponseRedirect(reverse(problem_list)) 

def new_procedure_calendar(request):

    record_id = request.session['record_id']

    jsonData = " "
    r = " "
    if request.method == "GET":
        return render_template('newprocedure',{ 'jsonData': jsonData})
    else:

        # Fix dates formatted by JQuery into xs:dateTime
        date_performed = request.POST['date_performed'] + 'T00:00:00Z' if request.POST['date_performed'] != '' else ''
        name_type2 =request.POST['code_fullname']
        name_type = (name_type2[:18] + '') if len(name_type2) > 19 else name_type2

        name_abbrev2 = request.POST['code']
        name_abbrev = (name_abbrev2[:18] + '') if len(name_abbrev2) > 19 else name_abbrev2
        if name_abbrev2 == '' or name_abbrev2 == ' ':
          name_abbrev2 ='None'

        # get the variables and create a problem XML
        params = {'date_performed': date_performed,
                  'name': name_abbrev2,#'http://purl.bioontology.org/ontology/SNOMEDCT/',    #request.POST['code_fullname'],
                  'name_type': name_type2,
                  'name_abbrev':'http://purl.bioontology.org/ontology/SNOMEDCT/',
                  'name_value': name_abbrev2,
                  'provider_name': request.POST['provider_name'],
                  'provider_institution': request.POST['provider_institution'],
                  'location': request.POST['location'],
                  'comments' : request.POST['comments']}
        procedure_xml = render_raw('procedure', params, type='xml')

        # add the problem
        client = get_indivo_client(request)
        procedure_xml = procedure_xml.encode('ascii', 'xmlcharrefreplace')
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
        resp, content = client.generic_list(record_id=record_id, data_model="Procedure", body=query_params)

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
            raise Exception("Error creating new pocedure: %s"%content)

        # add a notification
        # let's not do this anymore because it's polluting the healthfeed
        client.record_notify(record_id=request.session['record_id'],
                              body={'content':'a new procedure has been added to your procedures list'})

        return HttpResponseRedirect(reverse(problem_list))


def new_appointment_calendar(request):
    record_id = request.session['record_id']

    jsonData = None
    r = " "

    if request.method == "GET":
        return render_template('newappointment',{'jsonData': jsonData})
    else:


        # Fix dates formatted by JQuery into xs:dateTime
        date = request.POST['date'] + 'T00:00:00Z' if request.POST['date'] != '' else ''
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
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error creating new problem: %s"%content)

        return HttpResponseRedirect(reverse(problem_list))



def problem_list2(request):
    #status = request.GET.get('status', 'void')
    #limit=int(request.GET.get('limit', 100))
    #offset = int(request.GET.get('offset', 0))
    #status = request.GET.get('status', 'archived')
    #query_params = {
   #     'limit': limit,
   #     'offset': offset,
        #'order_by': 'startDate',
    #    'status': 'active',
    #   } 
    #client = get_indivo_client(request)
    
    #in_carenet = request.session.has_key('carenet_id')
    #if not in_carenet:
        # get record info
     #   record_id = request.session['record_id']
      #  resp, content = client.record(record_id=record_id)
       # if resp['status'] != '200':
            # TODO: handle errors
       #     raise Exception("Error reading Record info: %s"%content)
       # record = parse_xml(content)
        
        # read problems
      #  resp, content = client.generic_list(record_id=record_id, data_model="Problem", body=query_params)
      #  if resp['status'] != '200':
            # TODO: handle errors
      #      raise Exception("Error reading problems: %s"%content)
      #  probs = simplejson.loads(content)

    #else:
        # get record info
     #   carenet_id = request.session['carenet_id']
      #  resp, content = client.carenet_record(carenet_id=carenet_id)
       # if resp['status'] != '200':
            # TODO: handle errors
         #   raise Exception("Error reading Record info: %s"%content)
        #record = parse_xml(content)

        # read problems from the carenet
        #resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Problem")
        #if resp['status'] != '200':
            # TODO: handle errors
         #   raise Exception("Error reading problems from carenet: %s"%content)
        #probs = simplejson.loads(content)
        
    #probs = map(process_problem, probs)
    #record_label = record.attrib['label']
    #inum_problems = len(probs)i
     
    client = get_indivo_client(request)

    in_carenet = request.session.has_key('carenet_id')

    record_id = request.session['record_id']    
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
        resp, content = client.generic_list(record_id=record_id, data_model="Problem")
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems: %s"%content)
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
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Problem")
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content)
        probs = simplejson.loads(content)
        
    probs = map(process_problem, probs)
    record_label = record.attrib['label']
    num_problems = len(probs)
    
    return render_template('list', {'record_label': record_label, 'num_problems' : num_problems,
                                    'problems': probs, 'in_carenet':in_carenet, })
    #return render_template('list')

def new_problem(request):
    if request.method == "GET":
        return render_template('newproblem')
    else:


        # Fix dates formatted by JQuery into xs:dateTime
        date_onset = request.POST['date_onset'] + 'T00:00:00Z' if request.POST['date_onset'] != '' else ''
        date_resolution = request.POST['date_resolution'] + 'T00:00:00Z' if request.POST['date_resolution'] != '' else ''

        # get the variables and create a problem XML
        params = {'date_onset': date_onset,
                  'date_resolution': date_resolution,
                  'code_fullname': request.POST['code_fullname'],
                  'code': request.POST['code'],
                  'comments' : request.POST['comments']}

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
        problem_xml = render_raw('problem', params, type='xml')
        
        # add the problem
        client = get_indivo_client(request)
        resp, content = client.document_create(record_id=request.session['record_id'], body=problem_xml, 
                                               content_type='application/xml')
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error creating new problem: %s"%content)
        
        # add a notification
        # let's not do this anymore because it's polluting the healthfeed
        client.record_notify(record_id=request.session['record_id'], 
                              body={'content':'a new problem has been added to your problem list'})
        
        return HttpResponseRedirect(reverse(problem_list))

def code_lookup(request):
    client = get_indivo_client(request)
    
    query = request.GET['query']
    
    # reformat this for the jQuery autocompleter
    resp, content = client.coding_system_query(system_short_name='snomed', body={'q':query})
    if resp['status'] != '200':
        # TODO: handle errors
        # But this Indivo instance might not support codingsystem lookup, so let's pass
        pass
    codes = simplejson.loads(content)
    formatted_codes = {'query': query, 'suggestions': [c['consumer_value'] for c in codes], 'data': codes}
    
    return HttpResponse(simplejson.dumps(formatted_codes), mimetype="text/plain")

def one_problem(request,problem_id):
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
         resp, content = client.record_specific_document(record_id=record_id, document_id=problem_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error fetching document: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.record_document_meta(record_id=record_id, document_id=problem_id)
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
         resp, content = client.carenet_document(carenet_id=carenet_id, document_id=problem_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error fetching document from carenet: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=problem_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error fetching document metadata from carenet: %s"%content)
         doc_meta_xml = content
    
    doc = parse_xml(doc_xml)    
    problem = parse_sdmx_problem(doc, ns=True)
    
    if doc_meta_xml:
        doc_meta = parse_xml(doc_meta_xml)
        meta = parse_meta(doc_meta)
    else:
        meta = None
    
    record_label = record.attrib['label']
    surl_credentials = client.get_surl_credentials()
    
    return render_template('one', {'problem':problem, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'problem_id': problem_id, 'surl_credentials': surl_credentials})

def archived_problem(request,problem_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=problem_id, body={'status':'archived', 'reason':'removed by user'})
        return HttpResponseRedirect(reverse(problem_list))



def edit_problem(request, problem_id):

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
           resp, content = client.record_specific_document(record_id=record_id, document_id=problem_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document: %s"%content)
           doc_xml = content

           # read the document's metadata
           resp, content = client.record_document_meta(record_id=record_id, document_id=problem_id)
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
           resp, content = client.carenet_document(carenet_id=carenet_id, document_id=problem_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document from carenet: %s"%content)
           doc_xml = content
# read the document's metadata
           resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=problem_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document metadata from carenet: %s"%content)
           doc_meta_xml = content

       doc = parse_xml(doc_xml)
       problem = parse_sdmx_problem(doc, ns=True)

       if doc_meta_xml:
           doc_meta = parse_xml(doc_meta_xml)
           meta = parse_meta(doc_meta)
       else:
           meta = None

       record_label = record.attrib['label']
       surl_credentials = client.get_surl_credentials()

       return render_template('one_edit', {'problem':problem, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'problem_id': problem_id, 'surl_credentials': surl_credentials})
    else:

       # Fix dates formatted by JQuery into xs:dateTime
       date_onset = request.POST['date_onset']
       if date_onset.find("T00:00:00Z")== -1:
           date_onset = request.POST['date_onset'] + 'T00:00:00Z'

       date_resolution = request.POST['date_resolution']
       if date_resolution.find("T00:00:00Z")== -1:
           date_resolution = request.POST['date_resolution'] + 'T00:00:00Z'

        # get the variables and create a problem XML
       
       params = {'date_onset': date_onset,
                  'date_resolution': date_resolution,
                  'code_fullname': request.POST['code_fullname'],
                  'code': request.POST['code'],
                  'comments' : request.POST['comments']}



                  
                 # 'code_abbrev':'',
                 # 'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                 # 'startDate': startDate,
                 # 'endDate': endDate,
                 # 'code_fullname': request.POST['code_fullname'],
                 # 'code': request.POST['code'],
                 # 'comments' : request.POST['comments']}      
                            
       problem_xml = render_raw('problem', params, type='xml')

       client = get_indivo_client(request)
       record_id = request.session.get('record_id', None)

       resp, content = client.document_version(record_id=request.session['record_id'], document_id=problem_id, body=problem_xml, content_type='application/xml')
       #resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml, content_type='application/xml')

       if resp['status'] != '200':
          # TODO: handle errors
            raise Exception("Error creatiTANM AASASHASKLng new pocedure: %s")

       # add a notification
       # let's not do this anymore because it's polluting the healthfeed
       # client.record_notify(record_id=request.session['record_id'],
       #                      body={'content':'a new problem has been added to your problem list'})

       return HttpResponseRedirect(reverse(problem_list))




def edit_problem2(request,problem_id):

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
           resp, content = client.record_specific_document(record_id=record_id, document_id=problem_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document: %s"%content)
           doc_xml = content

           # read the document's metadata
           resp, content = client.record_document_meta(record_id=record_id, document_id=problem_id)
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
           resp, content = client.carenet_document(carenet_id=carenet_id, document_id=problem_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document from carenet: %s"%content)
           doc_xml = content


       doc = parse_xml(doc_xml)
       problem = parse_sdmx_problem(doc, ns=True)

       if doc_meta_xml:
           doc_meta = parse_xml(doc_meta_xml)
           meta = parse_meta(doc_meta)
       else:
           meta = None

       record_label = record.attrib['label']
       surl_credentials = client.get_surl_credentials()

       #return render_template('one_edit', {'allergy':allergy 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'allergy_id': allergy_id, 'surl_credentials': surl_credentials})
       return render_template('one_edit', {'problem':problem, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'problem_id': problem_id, 'surl_credentials': surl_credentials})
    else:
        #formatted by JQuery into xs:dateTime
    
        startDate = request.POST['startDate']
        if startDate.find("T00:00:00Z")== -1:
            startDate = request.POST['startDate'] + 'T00:00:00Z'
        
        endDate = request.POST['endDate']
        if endDate.find("T00:00:00Z")== -1:
            endDate = request.POST['endDate'] + 'T00:00:00'

        # get the variables and create a problem XML
        params = {'code_abbrev':'',
                  'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                  'startDate': startDate,
                  'endDate': endDate,
                  'code_fullname': request.POST['code_fullname'],
                  'code': request.POST['code'],
                  'comments' : request.POST['comments']}

        problem_xml = render_raw('problem', params, type='xml')

        client = get_indivo_client(request)
        record_id = request.session.get('record_id', None)



       # add the problem
       #resp, content = client.record_app_document_create_or_update(pha_email="procedures@apps.indivo.org", document_id=procedure_id, body=procedure_xml)
        resp, content = client.document_version(record_id=request.session['record_id'], document_id=problem_id, body=problem_xml, content_type='application/xml')
       # resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml, content_type='application/xml')

        if resp['status'] != '200':
           # TODO: handle errors
            raise Exception("Error creatiTANM AASASHASKLng new allergy: %s"%content)
 # add a notification
       # let's not do this anymore because it's polluting the healthfeed
       # client.record_notify(record_id=request.session['record_id'],
       #                      body={'content':'a new problem has been added to your problem list'})



        return HttpResponseRedirect(reverse(problem_list))


def archived_problems(request):
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
        resp, content = client.generic_list(record_id=record_id, data_model="Problem", body=query_params)
        #resp, content = client.generic_list(record_id=record_id, data_model="Problem", body=query_params))
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems: %s"%content)
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
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Problem")
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content)
        probs = simplejson.loads(content)

    probs = map(process_problem, probs)
    record_label = record.attrib['label']
    num_problems = len(probs)

    return render_template('archived_list', {'record_label': record_label, 'num_problems' : num_problems,
                                    'problems': probs, 'in_carenet':in_carenet, })


def restore_problem(request,problem_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=problem_id, body={'status':'active', 'reason':'restored by user'})
        return HttpResponseRedirect(reverse(archived_problems))
