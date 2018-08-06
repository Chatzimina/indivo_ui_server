"""
Views for the 
Chatzimina Maria
"""

from utils import *
import uuid
import urllib
import urllib2
import json
import httplib
import httplib2
import requests
import xml.etree.ElementTree as ET
import pprint
import itertools
import os
import sys
from subprocess import *
import suds
import psycopg2
from suds.client import Client
from django.utils import simplejson
from django.shortcuts import render_to_response
from rdflib.graph import Graph
from xml.dom import minidom
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import tostring



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

def medications(request):
    client = get_indivo_client(request)

    in_carenet = request.session.has_key('carenet_id')

    record_id = request.session['record_id'] 




    #query = """SELECT DISTINCT ?id ?code ?title ?text ?substanceCode ?patientId ?birthTime ?effectiveTime_start WHERE {?instPerson hl7rim:person_id ?patientId. ?instPerson hl7rim:person_code '337915000'. OPTIONAL{?instPerson hl7rim:person_birthTime ?birthTime} ?instPerson     hl7rim:person_role ?instRole2. ?instRole2 hl7rim:role_entityId ?patientId. ?instRole2 hl7rim:role_participation ?instPart2. ?instPart2 hl7rim:participation_entityId ?patientId. ?instPart2 hl7rim:participation_act ?instAct. ?instAct hl7rim:act_code ?code; hl7rim:act_classCode 'SBADM'; hl7rim:act_title ?title; hl7rim:act_text ?text; hl7rim:act_codeOrig ?substanceCode; hl7rim:act_id ?id. OPTIONAL{?instAct   hl7rim:act_effectiveTime_start ?effectiveTime_start}}"""

    query = """SELECT DISTINCT ?id ?code ?title ?text ?substanceCode  ?birthTime ?effectiveTime_start ?rateQuantity ?rateQuantityUnits ?doseQuantity ?doseQuantityUnits WHERE {?instPerson hl7rim:person_id '380b3a6f-75a4-410c-a5ed-c48141952efd'. ?instPerson hl7rim:person_code '337915000'. OPTIONAL{?instPerson hl7rim:person_birthTime ?birthTime} ?instPerson     hl7rim:person_role ?instRole2. ?instRole2         hl7rim:role_entityId '380b3a6f-75a4-410c-a5ed-c48141952efd'. ?instRole2         hl7rim:role_participation ?instPart2. ?instPart2         hl7rim:participation_entityId '380b3a6f-75a4-410c-a5ed-c48141952efd'. ?instPart2         hl7rim:participation_act ?instAct. ?instAct         hl7rim:act_code ?code;hl7rim:act_classCode 'SBADM'; hl7rim:act_title ?title; hl7rim:act_text ?text; hl7rim:act_codeOrig ?substanceCode; hl7rim:act_id ?id. OPTIONAL{?instAct   hl7rim:act_effectiveTime_start ?effectiveTime_start}OPTIONAL{?instAct       hl7rim:act_substanceAdministrationT ?instSBADM. ?instSBADM   a	hl7rim:substanceAdministrationT OPTIONAL {?instSBADM	hl7rim:substanceAdministrationT_doseQuantity ?doseQuantity} OPTIONAL {?instSBADM	hl7rim:substanceAdministrationT_doseQuantityUnits ?doseQuantityUnits} OPTIONAL {?instSBADM	hl7rim:substanceAdministrationT_rateQuantity ?rateQuantity} OPTIONAL {?instSBADM	hl7rim:substanceAdministrationT_rateQuantityUnits ?rateQuantityUnits}}}"""
    url = "https://kandel.dia.fi.upm.es:8443/new_eureca_collaborative_tools/services/SemanticInteroperabilityLayer?wsdl"
    clientQuery = Client(url)
    try:
        queryresult = clientQuery.service.executeQuery(query)
    except suds.WebFault, e:
        print e
    data = queryresult    

#    data = """<?xml version="1.0" encoding="UTF-8"?> <sparql> <head> <variable name="id"/> <variable name="code"/> <variable name="title"/> <variable name="text"/> <variable name="substanceCode"/> <variable name="patientId"/> <variable name="birthTime"/> <variable name="effectiveTime_start"/> </head> <results> <result> <binding name="id"> <literal>df868fff-9d48-11e2-8ee8-833b8491ffe6</literal> </binding> <binding name="code"> <literal>432102000</literal> </binding> <binding name="title"> <literal>Administration of substance (procedure)</literal> </binding> <binding name="text"> <literal>Aclarubicin (product)</literal> </binding> <binding name="substanceCode"> <literal>326830005</literal> </binding> <binding name="patientId"> <literal>fictitious1</literal> </binding> <binding name="birthTime"> <literal>1965-03-01T00:00:00.0</literal> </binding> </result></results></sparql>"""
    tree = ET.fromstring(data)
    #literalList = tree.findall('.//result/binding/literal')
    #newList = literalList
    newList = [literal.text for literal in tree.findall('.//result/binding/literal')]
    newList2 = [newList[i:i+7] for i in range(0, len(newList), 7)]
    for chunks in newList2:
        medicationTitle = chunks[3]
        params = {'drugName_title': medicationTitle,
                  'drugName_system': 'http://purl.bioontology.org/ontology/RXNORM/',
                  'drugName_identifier': '1111',
                  'endDate': '2007-11-14',
                  'frequency_value': '1',
                  'instructions': 'instructions',
                  'provenance_title': 'provenance_title',
                  'provenance_system': 'http://smartplatforms.org/terms/codes/MedicationProvenance#',
                  'provenance_identifier':'prescription',
                  'quantity_value': '1',
                  'quantity_unit': 'd',
                  'startDate': '2007-11-10',
                  'date': '2014-03-18',
                  'dispenseDaysSupply': '1',
                  'pbm': 'pbm',
                  'pharmacy_ncpdpid': '1234',
                  'pharmacy_org': 'org',
                  'pharmacy_adr_country': 'country',
                  'pharmacy_adr_city': 'city',
                  'pharmacy_adr_postalcode': '71300',
                  'pharmacy_adr_street': 'adr',
                  'provider_dea_number': '6',
                  'provider_npi_number': '8',
                  'provider_email': 'email@email.com',
                  'provider_name_given': 'name',
                  'provider_name_family': 'family',
                  'provider_tel_1_type': 'w',
                  'provider_tel_1_number': '123',
                  'provider_tel_1_preferred_p': 'true',
                  'quantityDispensed_value': '1',
                  'quantityDispensed_unit': 'd'}        
        medication_xml = render_raw('medication', params, type='xml')
        #fill_xml = render_raw('fill',params,type='xml')

        # add the problem

        resp, content = client.document_create(record_id=request.session['record_id'], body=medication_xml,
                                               content_type='application/xml')

        if resp['status'] != '200':
         # TODO: handle errors
            raise Exception("Error creating new medication: %s"%content)

    return HttpResponseRedirect(reverse(allergies_list))


def problems(request):
    client = get_indivo_client(request)
    
    in_carenet = request.session.has_key('carenet_id')
    
    record_id = request.session['record_id']
   # resp, content = client.record(record_id=record_idk)
    params = {'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                 'date_onset': '2007-11-14',
                 'date_resolution': '2007-11-19',
                 'code_fullname': 'mariaaaaaaaaaa',
                 'code': '0101010101001010101',
                 'comments' : 'teeeeeeeeeeeeeeeeeeeeeeeesssssssssssssstttttttttttttffffffffffffooooooooooorrrrrrrrr'}
    problem_xml = render_raw('problem', params, type='xml')
        #fill_xml = render_raw('fill',params,type='xml')

        # add the problem
      
    resp, content = client.document_create(record_id=request.session['record_id'], body=problem_xml,
                                               content_type='application/xml')

    if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error adding problems: %s"%content)
    #resp, content = client.generic_list(record_id=record_id, data_model="Problem")
    #allergies = simplejson.loads(content)
    #return HttpResponse(simplejson.dumps(allergies), mimetype="text/plain")
    #doc_meta_xml = content
    #doc = parse_xml(doc_xml)    
    #problem = parse_sdmx_problem(doc, ns=True)
    #return HttpResponseRedirect(reverse(medication_list ))
    #return HttpResponse(content, mimetype="application/json")
    return HttpResponseRedirect(reverse(allergies_list))
    #return render_template('list', {'record_label': record_label, 'in_carenet':in_carenet, })




def proceduresxml(request):
    client = get_indivo_client(request)
    
    in_carenet = request.session.has_key('carenet_id')
    
    record_id = request.session['record_id']
    #resp, content = client.record(record_id=record_id)
    resp, content = client.generic_list(record_id=record_id, data_model="Procedure")
    #allergies = simplejson.loads(content)
    #return HttpResponse(simplejson.dumps(allergies), mimetype="text/plain")
    #doc_meta_xml = content
    #doc = parse_xml(doc_xml)    
    #problem = parse_sdmx_problem(doc, ns=True)

    return HttpResponse(content, mimetype="application/json")

def connectDWH(request):
    
    client = get_indivo_client(request)
    
    in_carenet = request.session.has_key('carenet_id')
    
    record_id = request.session['record_id']
    #resp, content = client.record(record_id=record_id)
    resp, content = client.read_demographics(record_id=record_id, response_format="application/json")
    #allergies = simplejson.loads(content)
    #return HttpResponse(simplejson.dumps(allergies), mimetype="text/plain")
    #doc_meta_xml = content
    #doc = parse_xml(doc_xml)    
    #problem = parse_sdmx_problem(doc, ns=True)
    #response = json.dumps(content)
    #test = content.read().decode(encoding)
    response = json.loads(content)
    email = response[0]["email"] 
    name = response[0]["name_family"]
    path = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/" + 'phrKey.jar')

    args = [filename, name, email] # Any number of args to be passed to the jar file

    result = jarWrapper(*args)


    list = result.splitlines()
    lastElement = len(list)
    pseudonym = list[lastElement-1]
    pseudonymPHR = pseudonym.split(":")
    pseudonymFinal= pseudonymPHR[1].strip()
   
  
    phrid=pseudonymFinal

    path = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/" + 'linkeArgs.jar')
    args2 = [filename,phrid] # Any number of args to be passed to the jar file

    results = jarWrapper(*args2)
    #results2 ="test"+results2
   # result = jarWrapper(*args)


    list = results.splitlines()
    lastElement = len(list)
    central = list[lastElement-1]
    #results2=phrid
    #listOf = results2.splitlines()
    #lastElement = len(listOf)
    #central = listOf[lastElement-1]
    centralID = central.split(":")
    pseudo = centralID[1].strip()
    central_id = pseudo 
    
    try:
       conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'");
       conn.autocommit = True
       conn.commit()
       cursor = conn.cursor()
    except:
        pseudonymFinal= "Cannot connect to db!!!!!!!!!!"


    #pseudonymFinal = "Cannot insert"
    try:
       cursor.execute("INSERT INTO indivo_phrkey (record_id,central_id,phrkey)VALUES("+"'"+record_id+"'"+","+"'"+central_id+"'"+","+"'"+phrid+"'"+");")
       conn.commit()
    except psycopg2.DatabaseError, e:

       if conn:
          conn.rollback()

       print 'Error %s' % e
       sys.exit(1)
    return HttpResponseRedirect(reverse(allergies_list)) 
#    return HttpResponse(content, mimetype="text/plain")


def jarWrapper(*args):
    process = Popen(['java', '-jar']+list(args), stdout=PIPE, stderr=PIPE)
    ret = []
    stdout, stderr = process.communicate()
    return stdout

def jarWrapper2(*args2):
    process2 = Popen(['java', '-jar']+list(args2), stdout=PIPE, stderr=PIPE)
    ret2 = []
    stdout2, stderr2 = process2.communicate()
    return stdout2

def json2xml(json_obj, line_padding=""):
    result_list = list()

    json_obj_type = type(json_obj)

    if json_obj_type is list:
        for sub_elem in json_obj:
            result_list.append(json2xml(sub_elem, line_padding))

        return "\n".join(result_list)

    if json_obj_type is dict:
        for tag_name in json_obj:
            sub_obj = json_obj[tag_name]
            result_list.append("%s<%s>" % (line_padding, tag_name))
            result_list.append(json2xml(sub_obj, "\t" + line_padding))
            result_list.append("%s</%s>" % (line_padding, tag_name))

        return "\n".join(result_list)

    return "%s%s" % (line_padding, json_obj)

def dict_to_xml(tag, d):
    '''
    Turn a simple dict of key/value pairs into XML
    '''
    elem = Element(tag)
    for key, val in d.items():
        child = Element(key)
        child.text = str(val)
        elem.append(child)
    return elem


def dict_to_xml2(tag, d):
    '''
    Turn a simple dict of key/value pairs into XML
    '''
    elem = Element(tag)
    for key, val in d.items():
        child = Element(key)
        child.text = str(val)
        elem.append(child)
    return elem

class Py2XML():
 def parse( self, pythonObj, objName=None ):
        '''
        processes Python data structure into XML string
        needs objName if pythonObj is a List
        '''
        if pythonObj == None:
            return ""

        if isinstance( pythonObj, dict ):
            self.data = self._PyDict2XML( pythonObj )
            
        elif isinstance( pythonObj, list ):
            # we need name for List object
            self.data = self._PyList2XML( pythonObj, objName )
            
        else:
            self.data = "<%(n)s>%(o)s</%(n)s>" % { 'n':objName, 'o':str( pythonObj ) }
            
        return self.data

 def _PyDict2XML( self, pyDictObj, objName=None ):
        '''
        process Python Dict objects
        They can store XML attributes and/or children
        '''
        tagStr = ""     # XML string for this level
        attributes = {} # attribute key/value pairs
        attrStr = ""    # attribute string of this level
        childStr = ""   # XML string of this level's children

        for k, v in pyDictObj.items():

            if isinstance( v, dict ):
                # child tags, with attributes
                childStr += self._PyDict2XML( v, k )

            elif isinstance( v, list ):
                # child tags, list of children
                childStr += self._PyList2XML( v, k )

            else:
                # tag could have many attributes, let's save until later
                attributes.update( { k:v } )

        if objName == None:
            return childStr

        # create XML string for attributes
        for k, v in attributes.items():
            attrStr += " %s=\"%s\"" % ( k, v )

        # let's assemble our tag string
        if childStr == "":
            tagStr += "<%(n)s%(a)s />" % { 'n':objName, 'a':attrStr }
        else:
            tagStr += "<%(n)s%(a)s>%(c)s</%(n)s>" % { 'n':objName, 'a':attrStr, 'c':childStr }

        return tagStr

 def _PyList2XML( self, pyListObj, objName=None ):
        '''
        process Python List objects
        They have no attributes, just children
        Lists only hold Dicts or Strings
        '''
        tagStr = ""    # XML string for this level
        childStr = ""  # XML string of children

        for childObj in pyListObj:
            
            if isinstance( childObj, dict ):
                # here's some Magic
                # we're assuming that List parent has a plural name of child:
                # eg, persons > person, so cut off last char
                # name-wise, only really works for one level, however
                # in practice, this is probably ok
                childStr += self._PyDict2XML( childObj, objName[:-1] )
            else:
                for string in childObj:
                    childStr += string;

        if objName == None:
            return childStr

        tagStr += "<%(n)s>%(c)s</%(n)s>" % { 'n':objName, 'c':childStr }

        return tagStr

def exportrdf(request):

    client = get_indivo_client(request)

    in_carenet = request.session.has_key('carenet_id')

    record_id = request.session['record_id']
    limit=int(request.GET.get('limit', 100))
    offset = int(request.GET.get('offset', 0))


#    output='[{"patient_id":"'+record_id+'"}'
    output=''
    try:
        demographics=request.POST['demographics']
    except Exception:
        demographics= None

    try:
        problems=request.POST['problems']
    except Exception:
        problems= None

    try:
        procedures=request.POST['procedures']
    except Exception:
        procedures= None
    try:
        allergies=request.POST['allergies']
    except Exception:
        allergies= None

    try:
        labs=request.POST['labs']
    except Exception:
        labs= None
    try:
        medications=request.POST['medications']
    except Exception:
        medications= None

    try:
        procedures=request.POST['procedures']
    except Exception:
        procedures= None
    
    try:
        appointments=request.POST['appointments']
    except Exception:
        appointments= None
 
    try:
        measurements=request.POST['measurements']
    except Exception:
        measurements= None

    try:
        formats=request.POST['format']
    except Exception:
        formats= None


    if formats is not None:
       if formats == 'json':
	   query_params = {
           'limit': limit,
           'offset': offset,
           'status': 'active',
           'response_format':'application/json',
           }

	   query_params2 = {
           'response_format': 'application/json',
           }
           response_format="json"
       elif formats == 'xml':
	 
	   query_params = {
           'limit': limit,
           'offset': offset,
           'status': 'active',
           'response_format':'application/xml',
           }

	   query_params2 = {
	           'response_format': 'application/xml',
           }
	   response_format="text/xml"
       elif formats=='rdf':
           query_params = {
           'limit': limit,
           'offset': offset,
           'status': 'active',
           'response_format':'application/rdf+xml',
           }


	   query_params2 = {
                   'response_format': 'application/rdf+xml',
           }
	   response_format="application/rdf+xml"

	

    if demographics=='yes':
 	output+= 'DEMOGRAPHICS: \n'
        resp, contental = client.read_demographics(record_id=record_id,body=query_params2)
        output+= '\n'+contental

    if problems=='yes':
	output+= '\n PROBLEMS: \n'
#        resp, contental2 = client.smart_generic(record_id=record_id, model_name="problems")       
        resp, contental2 = client.generic_list(record_id=record_id, data_model="Problem",response_format=response_format, body=query_params)
        output+= '\n'+contental2

    if labs=='yes':
	output+= '\n LABORATORIES: \n'
#	resp, contental3 = client.smart_generic(record_id=record_id, model_name="lab_results")
        resp, contental3 = client.generic_list(record_id=record_id, data_model="LabResult",response_format=response_format, body=query_params)
        output+= '\n'+contental3
    if allergies=='yes':
	output+= '\n ALLERGIES: \n'
#        resp, contental4 = client.smart_generic(record_id=record_id, model_name="allergies")
        resp, contental4 = client.generic_list(record_id=record_id, data_model="Allergy",response_format=response_format, body=query_params)
        output += '\n'+contental4
    if medications == 'yes':
	output+= '\n MEDICATIONS: \n'
#        resp, contental5 = client.smart_generic(record_id=record_id, model_name="medications")
        resp, contental5 = client.generic_list(record_id=record_id, data_model="Medication",response_format=response_format, body=query_params)

	output += '\n'+contental5

    if procedures=='yes':
        output+= '\n PROCEDURES: \n'
#        resp, contental2 = client.smart_generic(record_id=record_id, model_name="problems")
        resp, contental6 = client.generic_list(record_id=record_id, data_model="Procedure",response_format=response_format, body=query_params)
        output+= '\n'+contental6

    if measurements=='yes':
        output+= '\n Measurements: \n'
#        resp, contental2 = client.smart_generic(record_id=record_id, model_name="problems")
        resp, contental7 = client.generic_list(record_id=record_id, data_model="Measurements",response_format=response_format, body=query_params)
        output+= '\n'+contental7

    if appointments=='yes':
        output+= '\n APPOINTMENTS: \n'
#        resp, contental2 = client.smart_generic(record_id=record_id, model_name="problems")
        resp, contental8 = client.generic_list(record_id=record_id, data_model="Appointment",response_format=response_format, body=query_params)
        output+= '\n'+contental8


    return HttpResponse(output,mimetype="application/force-download")#mimetype="text/plain") #mimetype="application/force-download")



def allxml(request):
    
    client = get_indivo_client(request)
    
    in_carenet = request.session.has_key('carenet_id')
    
    record_id = request.session['record_id']
    resp, content0 = client.read_demographics(record_id=record_id)
    resp, content1 = client.generic_list(record_id=record_id, data_model="problem",response_format=None)
    resp, contental = client.smart_generic(record_id=record_id, model_name="lab_results")
    resp, content2 = client.generic_list(record_id=record_id, data_model="Procedure",response_format="text/xml")
    fileroot = str('[{"patient_id":"'+record_id+'"},'+content0+','+content1+','+content2+']')
#    jsonData = simplejson.loads(fileroot)[0]
    #jsonData = json.dumps(fileroot)
    #serializer = Py2XML()
    #xml_string = serializer.parse(fileroot )

    content = simplejson.loads(fileroot)

#    e=tostring(content[0])

    e2=""
    for i in range(1,len(content)):
       e = dict_to_xml('Somenode',content[i][0])
       result = tostring(e)
       e2 += result    
   
  

 

##    g = Graph()
 #   g.parse(fileroot, format="nt")
  #  g.serialize("test.rdf", format="rdf/xml")
   # result = "" 
    #for stmt in g:
    #  result += stmt
    #result = json2xml(fileroot)
#    result = dict_to_xml('stock', jsonData)
    return HttpResponse(contental,mimetype="text/plain") #mimetype="application/force-download")#mimetype="text/plain")



def downloadData(request):
    client = get_indivo_client(request)

    in_carenet = request.session.has_key('carenet_id')

    record_id = request.session['record_id']
    allergies= None
    problems = None
    procedures= None
    medications= None
    labs= None
    #output='[{"patient_id":"'+record_id+'"}'
    
    #medications=request.POST['medications']
   
    if request.GET.get('allergies'):
       request.session['allergies'] = request.GET['allergies']
       problems = request.GET['allergies']
    
    if request.GET.get('problems'):
       request.session['problems'] = request.GET['problems']
       problems = request.GET['problems']

    if request.GET.get('medications'): 
       request.session['medications'] = request.GET['medications']
       medications = request.GET['medications']
    

    #problems=request.POST['problems']
    if request.GET.get('procedures'):
       request.session['procedures'] = request.GET['procedures']
       procedures = request.GET['procedures']    

    if request.GET.get('labs'):
       request.session['labs'] = request.GET['labs']
       labs = request.GET['labs']
    #try:
    #    procedures=request.POST['procedures']
    #except Exception:
    #    procedures= None
    try:
       conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
       conn.autocommit = True
       conn.commit()
       cursor = conn.cursor()

    except:
       print "Cannot connect to db"
    tuples = ''
    try:
       cursor.execute("SELECT central_id  FROM indivo_phrkey where record_id="+"'"+record_id+"'")
       existing_record = cursor.fetchall()
    except psycopg2.DatabaseError, e:

       if conn:
           conn.rollback()

           print 'Error %s' % e
    central_id =existing_record
    #tuples = existing_record
    #for item in tuples:
    #    phrid=str(item[0])
    
    #path = os.path.dirname(os.path.realpath(__file__))
    #filename = os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/" + 'centralIdentification.jar')
    #args2 = [filename,phrid] # Any number of args to be passed to the jar file

    #results = jarWrapper(*args2)
    #results2 ="test"+results2
   # result = jarWrapper(*args)


    #list = results.splitlines()
    #lastElement = len(list)
    #central = list[lastElement-1]
    #results2=phrid
    #listOf = results2.splitlines()
    #lastElement = len(listOf)
    #central = listOf[lastElement-1]
    #centralID = central.split(":")
    #pseudo = centralID[1]
    tuples = existing_record
    for item in tuples:
        centralid=str(item[0])

    central_id = centralid.strip()
    
#380b3a6f-75a4-410c-a5ed-c48141952efd
    if labs == 'yes':
      #query = """SELECT DISTINCT ?id ?code ?name ?text  ?birthTime ?effectiveTime ?value ?valueType ?units ?refmin ?refmax    WHERE {     ?instPerson                    hl7rim:person_id '380b3a6f-75a4-410c-a5ed-c48141952efd'.     ?instPerson                    hl7rim:person_code '337915000'.     OPTIONAL{?instPerson        hl7rim:person_birthTime ?birthTime}     ?instPerson                    hl7rim:person_role ?instRole2.     ?instRole2                    hl7rim:role_entityId '380b3a6f-75a4-410c-a5ed-c48141952efd'.     ?instRole2                    hl7rim:role_participation ?instPart2.     ?instPart2                    hl7rim:participation_entityId '380b3a6f-75a4-410c-a5ed-c48141952efd'.     ?instPart2                    hl7rim:participation_act ?instAct.     ?instAct                    hl7rim:act_code ?code;                                 hl7rim:act_id    ?id;                                 hl7rim:act_title ?name;                                 hl7rim:act_text ?text.       OPTIONAL {?instAct      hl7rim:act_effectiveTime ?effectiveTime}      FILTER (?code IN ('263605001', '27327002', '38007001', '104846005', '11211-0', '67487000', '103228002', '312469006', '59573005', '104589004', '391084000', '270982000', '441689006', '33747003', '14089001', '28317006', '104133003', '54706004', '37254006', '165475005', '61928009', '75672003', '767002', '30630007', '74765001', '67776007', '71960002', '42351005', '103220009', '396451008', '42525009', '104934005', '1959-6', '71878006', '38151008', '104867005', '104485008', '105011006', '113075003', '80274001', '55235003', '74040009', '45896001', '34608000', '88810008', '69480007', '1975-2', '11579-0', '3051-0'))      OPTIONAL{?instAct      hl7rim:act_observationAct ?instObs.            ?instObs hl7rim:observationAct_actObservationValues ?instValues.            ?instValues          a hl7rim:actObservationValues.             OPTIONAL{?instValues hl7rim:actObservationValues_value ?value}            OPTIONAL{?instValues hl7rim:actObservationValues_valueType ?valueType}            OPTIONAL{?instValues hl7rim:actObservationValues_units ?units}            OPTIONAL{?instValues hl7rim:actObservationValues_refRangeMin ?refmin}            OPTIONAL{?instValues hl7rim:actObservationValues_refRangeMax ?refmax}          } }"""
      #url = "https://kandel.dia.fi.upm.es:8443/new_eureca_collaborative_tools/services/SemanticInteroperabilityLayer?wsdl"
      #clientQuery = Client(url)
      #queryresult= ''
      #try:
      #      queryresult = clientQuery.service.executeQuery(query)
      #except suds.WebFault, e:
      #      print e
      path = os.path.dirname(os.path.realpath(__file__))
      filename = os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/" + 'queriesFin.jar')
      query = """SELECT DISTINCT ?id ?code ?name ?text  ?birthTime ?effectiveTime ?value ?valueType ?units ?refmin ?refmax WHERE{?instPerson hl7rim:person_id '"""+central_id+"""'. ?instPerson hl7rim:person_code '337915000'. OPTIONAL{?instPerson hl7rim:person_birthTime ?birthTime} ?instPerson hl7rim:person_role ?instRole2. ?instRole2 hl7rim:role_entityId '"""+central_id+"""'. ?instRole2 hl7rim:role_participation ?instPart2. ?instPart2 hl7rim:participation_entityId '"""+central_id+"""'. ?instPart2 hl7rim:participation_act ?instAct. ?instAct hl7rim:act_code ?code; hl7rim:act_id ?id; hl7rim:act_title ?name; hl7rim:act_text ?text. OPTIONAL {?instAct hl7rim:act_effectiveTime ?effectiveTime} FILTER (?code IN ('263605001', '27327002', '38007001', '104846005', '11211-0', '67487000', '103228002', '312469006', '59573005', '104589004', '391084000', '270982000', '441689006', '33747003', '14089001', '28317006', '104133003', '54706004', '37254006', '165475005', '61928009', '75672003', '767002', '30630007', '74765001', '67776007', '71960002', '42351005', '103220009', '396451008', '42525009', '104934005', '1959-6', '71878006', '38151008', '104867005', '104485008', '105011006', '113075003', '80274001', '55235003', '74040009', '45896001', '34608000', '88810008', '69480007', '1975-2', '11579-0', '3051-0')) OPTIONAL{?instAct hl7rim:act_observationAct ?instObs. ?instObs hl7rim:observationAct_actObservationValues ?instValues. ?instValues a hl7rim:actObservationValues. OPTIONAL{?instValues hl7rim:actObservationValues_value ?value} OPTIONAL{?instValues hl7rim:actObservationValues_valueType ?valueType} OPTIONAL{?instValues hl7rim:actObservationValues_units ?units} OPTIONAL{?instValues hl7rim:actObservationValues_refRangeMin ?refmin} OPTIONAL{?instValues hl7rim:actObservationValues_refRangeMax ?refmax}}}"""

      args = [filename,query] # Any number of args to be passed to the jar file

      result = jarWrapper(*args)
      xml = result.split("Query result:")
      queryresult = xml[1].strip()
      

      data = queryresult
      #if queryresult !='':
      tree = ET.fromstring(data)
      newList = [literal.text for literal in tree.findall('.//result/binding/literal')]
      newList2 = [newList[i:i+10] for i in range(0, len(newList), 10)]

      for chunks in newList2:
           test_name_title = chunks[2]
           test_name_identifier = chunks[1]
           quantitative_result_non_critical_range_max_value=10
           quantitative_result_non_critical_range_min_value=10
           unit ='m'
           if len(chunks) >10:

             quantitative_result_non_critical_range_max_value=chunks[10]
	     quantitative_result_non_critical_range_min_value=chunks[9]
	     unit = chunks[8]
           
           quantitative_result_value_value = chunks[6]
           
           s = chunks[5]
           collected_at = '2014-03-18'
           collected_at = s.split('T')[0]
           if chunks[1] !='' and chunks[2]!='':
       
              params = {'abnormal_interpretation_title':'Normal',
                  'abnormal_interpretation_system': 'http://smartplatforms.org/terms/codes/LabResultInterpretation#',
                  'abnormal_interpretation_identifier': 'normal',
                  'accession_number': '',
                  'test_name_title': test_name_title,
                  'test_name_system': 'http://purl.bioontology.org/ontology/LNC/',
                  'test_name_identifier': test_name_identifier,
                  'status_title': 'Unknown',
                  'status_system': 'http://smartplatforms.org/terms/codes/LabStatus#',
                  'status_identifier':'final',
                  'notes': 'N/A',
                  'quantitative_result_non_critical_range_max_value': quantitative_result_non_critical_range_max_value,
                  'quantitative_result_non_critical_range_max_unit': unit,
                  'quantitative_result_non_critical_range_min_value': quantitative_result_non_critical_range_min_value,
                  'quantitative_result_non_critical_range_min_unit': unit,
                  'quantitative_result_normal_range_max_value':quantitative_result_non_critical_range_max_value,
                  'quantitative_result_normal_range_max_unit': unit,
                  'quantitative_result_normal_range_min_value': quantitative_result_non_critical_range_min_value,
                  'quantitative_result_normal_range_min_unit': unit,
                  'quantitative_result_value_value': quantitative_result_value_value,
                  'quantitative_result_value_unit': unit,
                  'collected_at': collected_at,
                  'collected_by_org_name': 'EURECA',
                  'collected_by_org_adr_country': 'Unknown',
                  'collected_by_org_adr_city': 'Unknown',
                  'collected_by_org_adr_postalcode': 'Unknown',
                  'collected_by_org_adr_region': 'Unknown',
                  'collected_by_org_adr_street': 'Unknown',
                  'collected_by_name_family': 'Unknown',
                  'collected_by_name_given': 'Unknown',
                  'collected_by_role': 'Unknown'}
              problem_xml = render_raw('LabResult', params, type='xml')

               # add the problem
              client = get_indivo_client(request)
              resp, content = client.document_create(record_id=request.session['record_id'], body=problem_xml,
                                             content_type='application/xml')
              if resp['status'] != '200':
               # TODO: handle errors
                  raise Exception("Error creating new lab: %s"%content)
 

    if problems =='yes':
#      query="""SELECT DISTINCT ?id ?code ?title ?birthTime ?effectiveTime WHERE {     ?instPerson               hl7rim:person_id '380b3a6f-75a4-410c-a5ed-c48141952efd'.     ?instPerson               hl7rim:person_code '337915000'.     OPTIONAL{?instPerson      hl7rim:person_birthTime ?birthTime}     ?instPerson               hl7rim:person_role ?instRole2.     ?instRole2                hl7rim:role_entityId '380b3a6f-75a4-410c-a5ed-c48141952efd'.     ?instRole2                hl7rim:role_participation ?instPart2.     ?instPart2                hl7rim:participation_entityId '380b3a6f-75a4-410c-a5ed-c48141952efd'.     ?instPart2                hl7rim:participation_act ?instAct.     ?instAct                  hl7rim:act_code ?code;                               hl7rim:act_id    ?id.                                  OPTIONAL {?instAct      hl7rim:act_effectiveTime ?effectiveTime}     OPTIONAL {?instAct      hl7rim:act_title ?title}         ?instAct                hl7rim:act_observation ?instObs.     OPTIONAL {?instObs        hl7rim:observation_value ?value}     FILTER (!BOUND(?value)) }"""
#      url = "https://kandel.dia.fi.upm.es:8443/new_eureca_collaborative_tools/services/SemanticInteroperabilityLayer?wsdl"
 #     clientQuery = Client(url)
 
      path = os.path.dirname(os.path.realpath(__file__))
      filename = os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/" + 'queriesFin.jar')
      query = """SELECT DISTINCT ?id ?code ?title ?birthTime ?effectiveTime WHERE{ ?instPerson hl7rim:person_id '"""+central_id+"""'.  ?instPerson hl7rim:person_code '337915000'. OPTIONAL{?instPerson hl7rim:person_birthTime ?birthTime} ?instPerson hl7rim:person_role ?instRole2. ?instRole2 hl7rim:role_entityId '"""+central_id+"""'.  ?instRole2 hl7rim:role_participation ?instPart2. ?instPart2 hl7rim:participation_entityId '"""+central_id+"""'. ?instPart2 hl7rim:participation_act ?instAct. ?instAct hl7rim:act_code ?code; hl7rim:act_id    ?id. OPTIONAL {?instAct hl7rim:act_effectiveTime ?effectiveTime} OPTIONAL {?instAct hl7rim:act_title ?title} ?instAct hl7rim:act_observation ?instObs. OPTIONAL {?instObs hl7rim:observation_value ?value}  FILTER (!BOUND(?value))}"""

      args = [filename,query] # Any number of args to be passed to the jar file
      queryresult =''
      result = jarWrapper(*args)
      xml = result.split("Query result:")
      queryresult = xml[1].strip()


      
      #data = queryresult
      #try:
      #      queryresult = clientQuery.service.executeQuery(query)
      #except suds.WebFault, e:
      #      print e
      data = queryresult
      if queryresult !='':
        tree = ET.fromstring(data)
        newList = [literal.text for literal in tree.findall('.//result/binding/literal')]
        newList2 = [newList[i:i+5] for i in range(0, len(newList), 5)]
        for chunks in newList2:
           code_fullname = chunks[2]
           code = chunks[1]
           s = chunks[4]
           date_performed = '2014-03-18'
           date_performed = s.split('T')[0]
           if chunks[1] !='' and chunks[2]!='':
  
              params = {'coding_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                 'date_onset':date_performed ,
                 'date_resolution': '',
                 'code_fullname': code_fullname,
                 'code': code,
                 'comments' : 'Unknown'}
              problem_xml = render_raw('problem', params, type='xml')
        #fill_xml = render_raw('fill',params,type='xml')

        # add the problem

              resp, content = client.document_create(record_id=request.session['record_id'], body=problem_xml,
                                               content_type='application/xml')

              if resp['status'] != '200':
              # TODO: handle errors
                  raise Exception("Error adding problems: %s"%content)  

    if procedures=='yes':
      #query = """ SELECT DISTINCT ?id ?name ?code ?dateperformed WHERE {    ?instPerson                	hl7rim:person_id '380b3a6f-75a4-410c-a5ed-c48141952efd'.    ?instPerson               	hl7rim:person_code '337915000'.    ?instPerson                	hl7rim:person_role ?instRole2.     ?instRole2                	hl7rim:role_entityId '380b3a6f-75a4-410c-a5ed-c48141952efd'.    ?instRole2                	hl7rim:role_participation ?instPart2.    ?instPart2                	hl7rim:participation_entityId '380b3a6f-75a4-410c-a5ed-c48141952efd'.     ?instPart2                	hl7rim:participation_act ?instAct.    ?instAct                	hl7rim:act_code ?code;								hl7rim:act_id    ?id;								hl7rim:act_title ?name; 								hl7rim:act_text ?text.	    OPTIONAL {?instAct      hl7rim:act_effectiveTime ?dateperformed}    OPTIONAL {?instAct      hl7rim:act_classCode 'PROC'} }"""

      #url = "https://kandel.dia.fi.upm.es:8443/new_eureca_collaborative_tools/services/SemanticInteroperabilityLayer?wsdl"
      #clientQuery = Client(url)
      #queryresult= ''
      #try:
      #      queryresult = clientQuery.service.executeQuery(query)
      #except suds.WebFault, e:
      #      print e
      #data = queryresult
      path = os.path.dirname(os.path.realpath(__file__))
      filename = os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/" + 'queriesFin.jar')
      query = """SELECT DISTINCT ?id ?name ?code ?dateperformed WHERE { ?instPerson hl7rim:person_id '"""+central_id+"""'. ?instPerson hl7rim:person_code '337915000'.  ?instPerson hl7rim:person_role ?instRole2. ?instRole2  hl7rim:role_entityId '"""+central_id+"""'.  ?instRole2 hl7rim:role_participation ?instPart2. ?instPart2 hl7rim:participation_entityId '"""+central_id+"""'. ?instPart2 hl7rim:participation_act ?instAct. ?instAct hl7rim:act_code ?code; hl7rim:act_id ?id; hl7rim:act_title ?name; hl7rim:act_text ?text. OPTIONAL {?instAct hl7rim:act_effectiveTime ?dateperformed} OPTIONAL {?instAct hl7rim:act_classCode 'PROC'}}"""

      args = [filename,query] # Any number of args to be passed to the jar file
      queryresult =''
      result = jarWrapper(*args)
      xml = result.split("Query result:")
      queryresult = xml[1].strip()



      #data = queryresult
      #try:
      #      queryresult = clientQuery.service.executeQuery(query)
      #except suds.WebFault, e:
      #      print e
      data = queryresult

      if queryresult !='': 
        tree = ET.fromstring(data)
        newList = [literal.text for literal in tree.findall('.//result/binding/literal')]
        newList2 = [newList[i:i+4] for i in range(0, len(newList), 4)]
        for chunks in newList2:
           name = chunks[1]
           name_abbrev = chunks[2]
           s = chunks[3]
           date_performed = '2014-03-18'
           date_performed = s.split(' ')[0]	    
           if chunks[1] !='' and chunks[2]!='':
	      params = {'date_performed': date_performed,
                  'name': name,
                  'name_type': 'http://purl.bioontology.org/ontology/SNOMEDCT/',
                  'name_abbrev':name_abbrev,
                  'name_value': '',
                  'provider_name': '',
                  'provider_institution': 'Unknown',
                  'location': 'Unknown',
                  'comments' : 'Unknown'}
              procedure_xml = render_raw('procedure', params, type='xml')

        # add the problem
              client = get_indivo_client(request)
              resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml,
                                             content_type='application/xml')
              if resp['status'] != '200':
               # TODO: handle errors
                  raise Exception("Error creating new procedure: %s"%content) 


    if medications=='yes':
        #query = """SELECT DISTINCT ?id ?code ?title ?text ?substanceCode ?patientId ?birthTime ?effectiveTime_start WHERE {?instPerson hl7rim:person_id ?patientId. ?instPerson hl7rim:person_code '337915000'. OPTIONAL{?instPerson hl7rim:person_birthTime ?birthTime} ?instPerson     hl7rim:person_role ?instRole2. ?instRole2 hl7rim:role_entityId ?patientId. ?instRole2 hl7rim:role_participation ?instPart2. ?instPart2 hl7rim:participation_entityId ?patientId. ?instPart2 hl7rim:participation_act ?instAct. ?instAct hl7rim:act_code ?code; hl7rim:act_classCode 'SBADM'; hl7rim:act_title ?title; hl7rim:act_text ?text; hl7rim:act_codeOrig ?substanceCode; hl7rim:act_id ?id. OPTIONAL{?instAct   hl7rim:act_effectiveTime_start ?effectiveTime_start}}"""

        #query = """SELECT DISTINCT ?id ?code ?title ?text ?substanceCode  ?birthTime ?effectiveTime_start ?rateQuantity ?rateQuantityUnits ?doseQuantity ?doseQuantityUnits WHERE {?instPerson hl7rim:person_id '380b3a6f-75a4-410c-a5ed-c48141952efd'. ?instPerson hl7rim:person_code '337915000'. OPTIONAL{?instPerson hl7rim:person_birthTime ?birthTime} ?instPerson     hl7rim:person_role ?instRole2. ?instRole2         hl7rim:role_entityId '380b3a6f-75a4-410c-a5ed-c48141952efd'. ?instRole2         hl7rim:role_participation ?instPart2. ?instPart2         hl7rim:participation_entityId '380b3a6f-75a4-410c-a5ed-c48141952efd'. ?instPart2         hl7rim:participation_act ?instAct. ?instAct         hl7rim:act_code ?code;hl7rim:act_classCode 'SBADM'; hl7rim:act_title ?title; hl7rim:act_text ?text; hl7rim:act_codeOrig ?substanceCode; hl7rim:act_id ?id. OPTIONAL{?instAct   hl7rim:act_effectiveTime_start ?effectiveTime_start}OPTIONAL{?instAct       hl7rim:act_substanceAdministrationT ?instSBADM. ?instSBADM   a      hl7rim:substanceAdministrationT OPTIONAL {?instSBADM    hl7rim:substanceAdministrationT_doseQuantity ?doseQuantity} OPTIONAL {?instSBADM        hl7rim:substanceAdministrationT_doseQuantityUnits ?doseQuantityUnits} OPTIONAL {?instSBADM      hl7rim:substanceAdministrationT_rateQuantity ?rateQuantity} OPTIONAL {?instSBADM        hl7rim:substanceAdministrationT_rateQuantityUnits ?rateQuantityUnits}}}"""
        #queryresult=''
        #url = "https://kandel.dia.fi.upm.es:8443/new_eureca_collaborative_tools/services/SemanticInteroperabilityLayer?wsdl"
        #clientQuery = Client(url)
        #try:
        #    queryresult = clientQuery.service.executeQuery(query)
        #except suds.WebFault, e:
        #    print e
        #data = queryresult
        path = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/" + 'queriesFin.jar')
        query = """SELECT DISTINCT ?id ?code ?title ?text ?substanceCode  ?birthTime ?effectiveTime_start ?rateQuantity ?rateQuantityUnits ?doseQuantity ?doseQuantityUnits WHERE { ?instPerson hl7rim:person_id '"""+central_id+"""'. ?instPerson hl7rim:person_code '337915000'. OPTIONAL{?instPerson hl7rim:person_birthTime ?birthTime} ?instPerson hl7rim:person_role ?instRole2. ?instRole2 hl7rim:role_entityId '"""+central_id+"""'. ?instRole2 hl7rim:role_participation ?instPart2. ?instPart2 hl7rim:participation_entityId '"""+central_id+"""'. ?instPart2 hl7rim:participation_act ?instAct. ?instAct hl7rim:act_code ?code; hl7rim:act_classCode 'SBADM'; hl7rim:act_title ?title; hl7rim:act_text ?text; hl7rim:act_codeOrig ?substanceCode;  hl7rim:act_id ?id. OPTIONAL{?instAct hl7rim:act_effectiveTime_start ?effectiveTime_start} OPTIONAL{?instAct hl7rim:act_substanceAdministrationT ?instSBADM. ?instSBADM a hl7rim:substanceAdministrationT OPTIONAL {?instSBADM hl7rim:substanceAdministrationT_doseQuantity ?doseQuantity} OPTIONAL {?instSBADM hl7rim:substanceAdministrationT_doseQuantityUnits ?doseQuantityUnits} OPTIONAL {?instSBADM	hl7rim:substanceAdministrationT_rateQuantity ?rateQuantity} OPTIONAL {?instSBADM hl7rim:substanceAdministrationT_rateQuantityUnits ?rateQuantityUnits}}}""" 

        args = [filename,query] # Any number of args to be passed to the jar file
        queryresult =''
        result = jarWrapper(*args)
        xml = result.split("Query result:")
        queryresult = xml[1].strip()
        data = queryresult 
        tree = ET.fromstring(data)
        newList = [literal.text for literal in tree.findall('.//result/binding/literal')]
        newList2 = [newList[i:i+10] for i in range(0, len(newList), 10)]   
        for chunks in newList2:
           medicationTitle = chunks[3]
           s = chunks[5]
           startDate = '2014-03-18'
           startDate = s.split('T')[0]
           drugName_identifier = chunks[4]
           #startDate = chunks[6]
           frequency_value = ''
           frequency_unit = ''
           quantity_value=''
           quantity_unit=''
           frequency_value=chunks[6]
           frequency_unit=chunks[7]
           quantity_value=chunks[8]
           quantity_unit=chunks[9]
           if chunks[3]!='' and chunks[4]!='':
             params = {'drugName_title': medicationTitle,
                  'drugName_system': 'http://purl.bioontology.org/ontology/RXNORM/',
                  'drugName_identifier': drugName_identifier,
                  'endDate': '2007-11-14',
                  'frequency_value': frequency_value,
                  'frequency_unit':frequency_unit, 
                  'instructions': '',
                  'provenance_title': '',
                  'provenance_system': 'http://smartplatforms.org/terms/codes/MedicationProvenance#',
                  'provenance_identifier':'administration',
                  'quantity_value': quantity_value,
                  'quantity_unit': quantity_unit,
                  'startDate': startDate,
                  'date': '2014-03-18',
                  'dispenseDaysSupply': '1',
                  'pbm': '',
                  'pharmacy_ncpdpid': '',
                  'pharmacy_org': '',
                  'pharmacy_adr_country': '',
                  'pharmacy_adr_city': '',
                  'pharmacy_adr_postalcode': '',
                  'pharmacy_adr_street': '',
                  'provider_dea_number': '',
                  'provider_npi_number': '',
                  'provider_email': '',
                  'provider_name_given': '',
                  'provider_name_family': '',
                  'provider_tel_1_type': 'w',
                  'provider_tel_1_number': '',
                  'provider_tel_1_preferred_p': 'true',
                  'quantityDispensed_value': '',
                  'quantityDispensed_unit': ''}
             medication_xml = render_raw('medication', params, type='xml')
        #fill_xml = render_raw('fill',params,type='xml')

        # add the problem

             resp, content = client.document_create(record_id=request.session['record_id'], body=medication_xml,
                                               content_type='application/xml')

             if resp['status'] != '200':
         # TODO: handle errors
               raise Exception("Error creating new medication: %s"%content)     
        #return HttpResponseRedirect(reverse(allergies_list))
    #if problems=='yes':
    #    return HttpResponseRedirect(reverse(allergies_list))
    #record_label = record.attrib['label'] 
    #return render_template('list', {'record_label': record_label,'in_carenet':in_carenet})
    return HttpResponseRedirect(reverse(allergies_list))


def allxml2(request):

    client = get_indivo_client(request)

    in_carenet = request.session.has_key('carenet_id')

    record_id = request.session['record_id']

    output='[{"patient_id":"'+record_id+'"}'

    try:
        demographics=request.POST['demographics']
    except Exception:
        demographics= None

    try:
        problems=request.POST['problems']
    except Exception:
        problems= None

    try:
        procedures=request.POST['procedures']
    except Exception:
        procedures= None

    if demographics=='yes':
        resp, content0 = client.read_demographics(record_id=record_id)
        output+= ','+content0

    if problems=='yes':
        resp, content1 = client.generic_list(record_id=record_id, data_model="problem")
        output+= ','+content1

    if procedures=='yes':
        resp, content2 = client.generic_list(record_id=record_id, data_model="Procedure")
        output+= ','+content2

    output+=']'
    output2 = output
    url='http://thor.ics.forth.gr:8580/dwh.importer.jersey/rest/import/json'
    headers={'Content-type':'application/json','Accept':'text/plain'}
    headers2={'Content-type':'application/json'}
    datain1=json.dumps(output)
    datain2={'json':json.dumps(output)}
    datain3=urllib.urlencode({'json':output})
    dataout= requests.post(url, data=output, headers=headers)
#    return render_template('list', {'dataout':dataout, 'datain1':datain1, 'datain2':datain2,'datain3':datain3,'output':output2})
    return HttpResponse(output2 , mimetype="text/html")



def allxml22222(request):
    
    client = get_indivo_client(request)
    
    in_carenet = request.session.has_key('carenet_id')
    
    record_id = request.session['record_id']
    
    output='[{"patient_id":"'+record_id+'"}' 

    try:
        demographics=request.POST['demographics']
    except Exception:
        demographics= None

    try:
        problems=request.POST['problems']
    except Exception:
        problems= None

    try:
        procedures=request.POST['procedures']
    except Exception:
        procedures= None
    
    if demographics=='yes':
        resp, content0 = client.read_demographics(record_id=record_id)
        output+= ','+content0

    if problems=='yes':
        resp, content1 = client.generic_list(record_id=record_id, data_model="problem")
        output+= ','+content1
    
    if procedures=='yes':
        resp, content2 = client.generic_list(record_id=record_id, data_model="Procedure")
        output+= ','+content2

    output+=']'
    url='http://thor.ics.forth.gr:8580/dwh.importer.jersey/rest/import/json'    
    headers={'Content-type':'application/json','Accept':'text/plain'}
    headers2={'Content-type':'application/json'}
    datain1=json.dumps(output)
    datain2={'json':json.dumps(output)}
    datain3=urllib.urlencode({'json':output})

    #http=httplib2.Http()
    #response, content= http.request(url, 'POST', datain1, headers)
    #req= urllib2.Request(url, output, headers2)
    #f=urllib2.urlopen(req) 
    #dataout=f.read()
    #f.close()	
    #dataout= urllib.urlopen(url, data=json.dumps(output)).read()
    dataout= requests.post(url, data=output, headers=headers)
    
    return HttpResponse(dataout , mimetype="text/html")


def labsxml(request):
    
    client = get_indivo_client(request)
    
    in_carenet = request.session.has_key('carenet_id')
    
    record_id = request.session['record_id']
    #resp, content = client.record(record_id=record_id)i
    resp, content = client.generic_list(record_id=record_id, data_model="labs")
    #allergies = simplejson.loads(content)
    #return HttpResponse(simplejson.dumps(allergies), mimetype="text/plain")
    #doc_meta_xml = content
    #doc = parse_xml(doc_xml)    
    #problem = parse_sdmx_problem(doc, ns=True)

    return HttpResponse(content, mimetype="application/force-download")

def allergies_list(request):
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
    #allergies = map(process_problem, allergies)
    
    #num_allergies = len(allergies)
    try:
       conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
       conn.autocommit = True
       conn.commit()
       cursor = conn.cursor()
       conn.commit() 
    except:
       print "Cannot connect to db"

    #try:
    #   cursor.execute("SELECT phrkey  FROM indivo_phrkey where record_id="+"'"+record_id+"'") 
    #   existing_record = cursor.fetchall()
    #except psycopg2.DatabaseError, e:
    
     #  if conn:
      #     conn.rollback()
    
       #    print 'Error %s' % e     
	# retrieve the records from the database
        
    
    return render_template('list', {'record_label': record_label,'in_carenet':in_carenet})

def new_allergy(request):
    if request.method == "GET":
        return render_template('newallergy')
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
        
        params = {'allergic_reaction_title':'Anaphylaxis', 
                  'allergic_reaction_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/', 
                  'allergic_reaction_identifier': '39579001', 
                  'category_title': 'Drug allergy', 
                  'category_system': 'http://purl.bioontology.org/ontology/SNOMEDCT/', 
                  'category_identifier': '416098002',
                  'drug_class_allergen_title' : 'Sulfonamide Antibacterial',
                  'drug_class_allergen_system' : 'http://purl.bioontology.org/ontology/NDFRT/',
                  'drug_class_allergen_identifier' : 'N0000175503',
                  'severity_title' : 'Severe',
                  'severity_system' : '',
                  'severity_identifier' : '24484000'}

        allergy_xml = render_raw('allergy', params, type='xml')
        
        # add the problem
        client = get_indivo_client(request)
        resp, content = client.document_create(record_id=request.session['record_id'], body=allergy_xml, 
                                               content_type='application/xml')
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error creating new allergy: %s"%content)
        
        # add a notification
        # let's not do this anymore because it's polluting the healthfeed
        # client.record_notify(record_id=request.session['record_id'], 
        #                      body={'content':'a new problem has been added to your problem list'})
        
        return HttpResponseRedirect(reverse(allergies_list))

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

def one_problem(request, problem_id):
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

