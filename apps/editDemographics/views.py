"""
Views for the Edit Demographics app
Chatzimina MAria
ICS-FORTH
"""

from utils import *
import uuid
import urllib
import urllib2
import requests
import json

import psycopg2

from django.utils import simplejson
from django.db import transaction
from django.utils.translation import ugettext as _
from psycopg2.extras import RealDictCursor
import json
import os
import sys
from subprocess import *


from django.utils import simplejson

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
    
    # redirect to the UI server
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
        return HttpResponse("oh oh bad token")
    
    # get the indivo client and use the request token as the token for the exchange
    client = get_indivo_client(request, with_session_token=False)
    client.update_token(token_in_session)
    access_token = client.exchange_token(oauth_verifier)
    
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
    
    in_carenet = request.session.has_key('carenet_id')
    if not in_carenet:
        record_id = request.session['record_id']
        INDIVO_IP = settings.INDIVO_IP
        jsonData = None
        r = " "

        try:
           conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'");
#           conn.autocommit = True
           conn.set_isolation_level(0)
           conn.commit()
           cursor = conn.cursor()
           url="prwto connect"
        except  psycopg2.DatabaseError, e:
           url=e
           print 'Error %s' % e
 
        recordInf=[]
        demographics_id="SELECT demographics_id FROM indivo_record where id='"+record_id+"'"

        try:

           cursor.execute( "SELECT demographics_id FROM indivo_record where id='"+record_id+"'" )
           conn.commit()
           result = cursor.fetchall()
           tuples = result
           url = result
           for item in tuples:
              demographics_id=(str(item[0]))


       #url2 = result[1]
        except psycopg2.DatabaseError, e:
           demographics_id=e
           if conn:
              conn.rollback()

           print 'Error %s' % e
        bday="" 
        try:

           cursor.execute( "SELECT email,gender,name_given,name_family,siop,weight,weight_unit,pregnancy,smoking,adr_street,adr_postalcode, adr_city,adr_country FROM indivo_demographics where id='"+demographics_id+"'" )
           conn.commit()
           result = cursor.fetchall()
           tuples = result
           url = result
           for item in tuples:
              recordInf=(item)


       #url2 = result[1]
        except psycopg2.DatabaseError, e:
           url=e
           if conn:
              conn.rollback()

           print 'Error %s' % e
        try:

           cursor.execute( "SELECT bday FROM indivo_demographics where id='"+demographics_id+"'" )
           conn.commit()
           result = cursor.fetchall()
           tuples = result
           url = result
           for item in tuples:
              bday=(str(item[0]))


       #url2 = result[1]
        except psycopg2.DatabaseError, e:
           url=e
           if conn:
              conn.rollback()

           print 'Error %s' % e
 

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
        
       
        

    else:
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
        
   
    bda = bday.split('-') 
   
#    recordIn = json.dumps(recordInf) 
    return render_template('list', {'recordInf':recordInf, 'demographics_id':demographics_id,'in_carenet':in_carenet,'bday':bda})



def updateDemographics(request):
    client = get_indivo_client(request)

    in_carenet = request.session.has_key('carenet_id')

    record_id = request.session['record_id']
    
    name=''   
    familyname=''
    gender=''
    email=''
    month=''
    year=''
    day=''
    siop=''
    weight=''
    weight_unit=''
    pregnancy=''
    smoking=''
    country=''
    street=''
    postalcode=''
    city=''
 
    if request.GET.get('name'):
       request.session['name'] = request.GET['name']
       name = request.GET['name']

    if request.GET.get('familyname'):
       request.session['familyname'] = request.GET['familyname']
       familyname = request.GET['familyname']


    if request.GET.get('gender'):
       request.session['gender'] = request.GET['gender']
       gender = request.GET['gender']
 

    if request.GET.get('email'):
       request.session['email'] = request.GET['email']
       email = request.GET['email']


    if request.GET.get('month'):
       request.session['month'] = request.GET['month']
       month = request.GET['month']

    if request.GET.get('year'):
       request.session['year'] = request.GET['year']
       year = request.GET['year']

    if request.GET.get('day'):
       request.session['day'] = request.GET['day']
       day = request.GET['day']

    if request.GET.get('siop'):
       request.session['siop'] = request.GET['siop']
       siop = request.GET['siop']
    
    if request.GET.get('weight'):
       request.session['weight'] = request.GET['weight']
       weight = request.GET['weight']

    if request.GET.get('weight_unit'):
       request.session['weight_unit'] = request.GET['weight_unit']
       weight_unit = request.GET['weight_unit']

    if request.GET.get('street'):
       request.session['street'] = request.GET['street']
       street = request.GET['street']
 
    if request.GET.get('postalcode'):
       request.session['postalcode'] = request.GET['postalcode']
       postalcode = request.GET['postalcode']

    if request.GET.get('city'):
       request.session['city'] = request.GET['city']
       city = request.GET['city']


    if request.GET.get('country'):
       request.session['country'] = request.GET['country']
       country = request.GET['country']

    if request.GET.get('pregnancy'):
       request.session['pregnancy'] = request.GET['pregnancy']
       pregnancy = request.GET['pregnancy']


    if request.GET.get('smoking'):
       request.session['smoking'] = request.GET['smoking']
       smoking = request.GET['smoking']




    bday = year+'-'+month+'-'+day


    try:
           conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'");
#           conn.autocommit = True
           conn.set_isolation_level(0)
           conn.commit()
           cursor = conn.cursor()
           url="prwto connect"
    except  psycopg2.DatabaseError, e:
           url=e
           print 'Error %s' % e

     
    

    try:

           cursor.execute( "SELECT demographics_id FROM indivo_record where id='"+record_id+"'" )
           conn.commit()
           result = cursor.fetchall()
           tuples = result
           url = result
           for item in tuples:
              demographics_id=(str(item[0]))


       #url2 = result[1]
    except psycopg2.DatabaseError, e:
           demographics_id=e
           if conn:
              conn.rollback()

           print 'Error %s' % e



    try:

           cursor.execute("UPDATE indivo_demographics SET  bday='"+bday+"', email='"+email+"', gender='"+gender+"',name_given='"+name+"', name_family='"+familyname+"', siop='"+siop+"',weight='"+weight+"', adr_country='"+country+"', adr_street='"+street+"', adr_postalcode='"+postalcode+"', adr_city='"+city+"',weight_unit='"+weight_unit+"', pregnancy='"+pregnancy+"', smoking='"+smoking+"' WHERE id='"+demographics_id+"'") 
           conn.commit()
#           result = cursor.fetchall()

 #          tuples = result
 #          url = result

           #for item in tuples:
            #  demographics_id=(str(item[0]))


       #url2 = result[1]
    except psycopg2.DatabaseError, e:

           
	   return HttpResponse(e)

    nameall = name+" "+familyname
    try:

           cursor.execute( "UPDATE indivo_record SET  label='"+nameall+"' WHERE id='"+record_id+"'" )
           conn.commit()
 #          result = cursor.fetchall()

 #          tuples = result
 #          url = result
           #for item in tuples:
            #  demographics_id=(str(item[0]))


       #url2 = result[1]
    except psycopg2.DatabaseError, e:
	  return HttpResponse(e)


    query="UPDATE indivo_record SET  label='"+nameall+"' WHERE id='"+record_id+"'"
   
#    if siop != '':
#        demographicsArgs = "<Demographics xmlns=\"http://indivo.org/vocab/xml/documents#\"> <dateOfBirth></dateOfBirth><gender></gender><email></email><Name><familyName></familyName><givenName></givenName></Name><siop>"+siop+"</siop></Demographics>"
             
        # palio project linkin pseudonyms me ton server tou elias nomizw
        #path = os.path.dirname(os.path.realpath(__file__))
        #filename = os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/" + 'linkingPseudonyms.jar')
        #writeFileN = os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/" +'file.py')
        #f = open( writeFileN, 'w' )
        #f.close()
        #args = [filename, demographicsArgs, record_id]
        #results = jarWrapper(*args)

#    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))
    return render_template('refresh', {'siop':siop,'gender':gender,'email':email,'name':name,'familyname':familyname,'year':year,'month':query,'day':result})


def jarWrapper(*args):
    process = Popen(['java', '-jar']+list(args), stdout=PIPE, stderr=PIPE)
    ret = []
    stdout, stderr = process.communicate()
    return stdout






