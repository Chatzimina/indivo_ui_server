""" 
Updated:
Chatzimina Maria
ICS-FORTH
"""

from lxml import etree
from utils import *
from django.shortcuts import render_to_response
from django.utils import simplejson
import settings # app local
import dateutil.parser
from django.db import transaction
from django.utils.translation import ugettext as _
import xmltodict
import sys
from xml.dom.minidom import parseString
import json
import xml.etree.ElementTree as ET
import psycopg2
import datetime


NS = 'http://indivo.org/vocab/xml/documents#'

LAB_STATUSES = {
    'correction': 'Correction',
    'preliminary': 'Preliminary',
    'final': 'Final',
}

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

    ##if not request.session.has_key('labs_access_token'):
        # request a request token
    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
    request.session['request_token'] = req_token

    return HttpResponseRedirect(client.auth_redirect_url)
    if 1==2:
       if datetime.datetime.now() > request.session['labs_time'] + datetime.timedelta(minutes=5):

         req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
         request.session['request_token'] = req_token

         return HttpResponseRedirect(client.auth_redirect_url)
       else:
         access_token=request.session['labs_access_token']
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
         return index(request) 
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
    request.session['labs_access_token']=access_token
    request.session['labs_time']=datetime.datetime.now()
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
    return index(request)


def index(request):
    return list_labs(request)

def parse_labs(labs):

    def _process_lab(lab):
        lab['id'] = lab['__documentid__']
        del lab['__documentid__']

        # Parse the lab's date
        try:
            d = dateutil.parser.parse(lab['collected_at'])
            d = d.astimezone(dateutil.tz.tzutc())
        except ValueError as e:
            d = 'parse error'
        lab['collected_at'] = d
        
        # Normalize the lab's status text
        if lab['status_identifier'] in LAB_STATUSES:
            lab['status_title'] = LAB_STATUSES[lab['status_identifier']]
        else:
            lab['status_title'] = 'Unknown'

        # Determine if the lab is abnormal
        
        try:
            # See if we can determine if value is outside the normal min/max
            test_value = float(lab['quantitative_result_value_value'])
       
            if (lab['quantitative_result_normal_range_min_value'] is not None) and (lab['quantitative_result_normal_range_min_value'] is not None):
           #   test_value = float(lab['quantitative_result_value_value'])
             min = float(lab['quantitative_result_normal_range_min_value'])
             max = float(lab['quantitative_result_normal_range_max_value'])
             if test_value > max or test_value < min:
                lab['abnormal'] = True

            # labs are also abnormal if they are explicitly labeled as such
            abn_interp = lab.get('abnormal_interpretation_identifier', None)
            if abn_interp and abn_interp != 'normal':
                lab['abnormal'] = True
        except (KeyError, ValueError) as e:
            pass

        # Preprocess the lab's address and organization names
        lab['org'] = lab['collected_by_org_name'] or 'Not Supplied'
        prefix = 'collected_by_org_adr_'
        adr_fields = (
            lab[prefix+'street'],
            lab[prefix+'city'],
            lab[prefix+'region'],
            lab[prefix+'postalcode'],
            lab[prefix+'country'],
            )
        lab['adr'] = ', '.join([f for f in adr_fields if f]) or 'Not Supplied'

        return lab
        
    return map(_process_lab, labs)

def show_lab(request, lab_id):
    client = get_indivo_client(request)
    record_id = request.session['record_id']
    resp, doc = client.record_specific_document(record_id=record_id, document_id=lab_id)
    if resp['status'] != '200':
        # TODO: handle errors
        raise Exception("Error loading original lab document: %s"%doc)
    lab = etree.fromstring(doc)
    return render_to_response("labs/templates/show.html", {'lab':etree.tostring(lab, pretty_print=True), 
                                                           'STATIC_HOME': settings.STATIC_HOME}
    )

def list_labs(request):
    # read in query params
    limit = int(request.GET.get('limit', 15))
    offset = int(request.GET.get('offset', 0))
    order_by = request.GET.get('order_by', 'collected_at') # test_name_title, created_at, collected_at
    lab_status = request.GET.get('lab_status', 'All') # final, corrected, preliminary
    lab_status_display = LAB_STATUSES.get(lab_status, 'All')
    status = request.GET.get('status', 'active')
    #read in previous values from session
    previous_date_start = request.session.get("date_start", None)
    previous_date_end = request.session.get("date_end", None)
    in_carenet = request.session.has_key('carenet_id')
    if request.session.has_key('record_id'):

        record_id = request.session['record_id']
        client = get_indivo_client(request)

        # retrieve a min date for labs
        oldest_params = {'limit': '1', 'order_by': 'collected_at'}

        if lab_status in LAB_STATUSES:
            oldest_params['status_identifier'] = lab_status
        resp, content = client.generic_list(record_id=record_id, data_model="LabResult", body=oldest_params)

        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching oldest lab: %s"%content)

        oldest_lab = parse_labs(simplejson.loads(content))

        if len(oldest_lab) > 1:
            oldest_lab_date = oldest_lab[0]['collected_at']
        else:
            oldest_lab_date = datetime.datetime.utcnow()

        max_date_string = datetime.datetime.utcnow().isoformat() + 'Z'
        min_date_string = datetime.datetime.combine(oldest_lab_date, datetime.time()).isoformat() + 'Z'
        date_start_string = request.GET.get('date_start', min_date_string)
        date_end_string = request.GET.get('date_end', max_date_string)
        
        #resets when changing date start/end
        if previous_date_start != date_start_string or previous_date_end != date_end_string:
            offset = 0
            
        #save off params in session
        request.session['date_start'] = date_start_string        
        request.session['date_end'] =  date_end_string
        
        # set params for lab query    
        parameters = {'limit': limit, 'offset': offset, 'order_by': order_by, 'status': status}
#        parameters.update({'date_range': 'collected_at*' + date_start_string + '*' + date_end_string})

        if lab_status in LAB_STATUSES:
            parameters['status_identifier'] = lab_status

        resp, content = client.generic_list(record_id=record_id, data_model="LabResult", body=parameters)

        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching labs: %s"%content)
        labs = parse_labs(simplejson.loads(content))
        resp, content2 = client.generic_list(record_id=record_id, data_model="LabResult", body={'status':'active'})
        allLabs = parse_labs(simplejson.loads(content2))
    else: 

        record_id = ""
        carenet_id = request.session['carenet_id']
        client = get_indivo_client(request)

        # retrieve a min date for labs
        oldest_params = {'limit': '1000', 'order_by': 'collected_at'}
        if lab_status in LAB_STATUSES:
            oldest_params['status_identifier'] = lab_status
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="LabResult", body=oldest_params)
    
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching oldest lab: %s"%content)
        oldest_lab = parse_labs(simplejson.loads(content))
        if len(oldest_lab) > 0:
            oldest_lab_date = oldest_lab[0]['collected_at']
        else:
            oldest_lab_date = datetime.datetime.utcnow()

        max_date_string = datetime.datetime.utcnow().isoformat() + 'Z'
        min_date_string = datetime.datetime.combine(oldest_lab_date, datetime.time()).isoformat() + 'Z'
        date_start_string = request.GET.get('date_start', min_date_string)
        date_end_string = request.GET.get('date_end', max_date_string)

        #resets when changing date start/end
        if previous_date_start != date_start_string or previous_date_end != date_end_string:
            offset = 0

        #save off params in session
        request.session['date_start'] = date_start_string
        request.session['date_end'] =  date_end_string

        # set params for lab query
        parameters = {'limit': limit, 'offset': offset, 'order_by': order_by, 'status': status}
#        parameters.update({'date_range': 'collected_at*' + date_start_string + '*' + date_end_string})# maria: to afairesa gt den emfanizotan sto sharing h lista olh
        if lab_status in LAB_STATUSES:
            parameters['status_identifier'] = lab_status
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="LabResult", body=parameters)

        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching labs: %s"%content)
        labs = parse_labs(simplejson.loads(content))

        allLabs=labs
        #TODO: not the case anymore
       
      
    
    # build a description for the range of results shown and calculate offsets
    next_offset = None
    prev_offset = None
    num_labs = len(labs)
    if num_labs == 0 and offset == 0:
        range_description = _('No Results')
    elif num_labs == 0:
        range_description = _('End of Results')
    else:
        range_description = _('Showing Results ') + str(offset + 1) + '-' + str(offset + num_labs)
        if limit == num_labs:
            next_offset = offset + limit
         
    if offset > 0:
        prev_offset = offset - limit
        if prev_offset < 0:
            prev_offset = 0
    surl_credentials = client.get_surl_credentials()
    ids=''

    for i in allLabs:

       ids+=i['id']+","

    return render_to_response("labs/templates/list.html", {'labs': labs, 
                                                           'lab_statuses': LAB_STATUSES,
                                                           'STATIC_HOME': settings.STATIC_HOME,
                                                           'order_by': order_by,
                                                           'limit': limit,
                                                           'offset': offset,
                                                           'lab_status_id': lab_status,
                                                           'lab_status_display': lab_status_display,
					 		   'status': status,
                                                           'next_offset': next_offset,
                                                           'prev_offset': prev_offset,
                                                           'range_description': range_description,
                                                           'num_labs': num_labs,
                                                           'min_date': min_date_string,
                                                           'max_date': max_date_string,
                                                           'date_start': date_start_string,
                                                           'date_end': date_end_string,
							   'in_carenet':in_carenet,
							   'ids':ids,
							   'surl_credentials':surl_credentials,
							   'record_id':record_id}
    )



def new_lab(request):
    record_id = request.session['record_id']
    if request.method == "GET":
        return render_template('newLab')
    else:

        # Fix dates formatted by JQuery into xs:dateTime
        collected_at = request.POST['collected_at'] + 'T00:00:00Z' if request.POST['collected_at'] != '' else ''
        #endDate = request.POST['endDate'] + 'T00:00:00Z' if request.POST['endDate'] != '' else ''

        # get the variables and create a problem XML
        params = {'abnormal_interpretation_title': request.POST['abnormal_interpretation_title'],
                  'abnormal_interpretation_system': 'http://smartplatforms.org/terms/codes/LabResultInterpretation#',
                  'abnormal_interpretation_identifier': request.POST['abnormal_interpretation_identifier'],
                  'accession_number': request.POST['accession_number'],
                  'test_name_title': request.POST['test_name_title'],
                  'test_name_system': 'http://purl.bioontology.org/ontology/LNC/',
                  'test_name_identifier': request.POST['test_name_identifier'],
   		  'status_title': request.POST['status_title'],
     	   	  'status_system': 'http://smartplatforms.org/terms/codes/LabStatus#',
		  'status_identifier':request.POST['status_identifier'],
		  'notes': request.POST['notes'],
		  'quantitative_result_non_critical_range_max_value': request.POST['quantitative_result_non_critical_range_max_value'],
	   	  'quantitative_result_non_critical_range_max_unit': request.POST['quantitative_result_non_critical_range_max_unit'],
	    	  'quantitative_result_non_critical_range_min_value': request.POST['quantitative_result_non_critical_range_min_value'],
	  	  'quantitative_result_non_critical_range_min_unit': request.POST['quantitative_result_non_critical_range_min_unit'],
 	 	  'quantitative_result_normal_range_max_value': request.POST['quantitative_result_normal_range_max_value'],
	   	  'quantitative_result_normal_range_max_unit': request.POST['quantitative_result_normal_range_max_unit'],
	   	  'quantitative_result_normal_range_min_value': request.POST['quantitative_result_normal_range_min_value'],
	 	  'quantitative_result_normal_range_min_unit': request.POST['quantitative_result_normal_range_min_unit'],
	   	  'quantitative_result_value_value': request.POST['quantitative_result_value_value'],
	  	  'quantitative_result_value_unit': request.POST['quantitative_result_value_unit'],
	    	  'collected_at': collected_at,
		  'collected_by_org_name': request.POST['collected_by_org_name'],
		  'collected_by_org_adr_country': request.POST['collected_by_org_adr_country'],
	  	  'collected_by_org_adr_city': request.POST['collected_by_org_adr_city'],
		  'collected_by_org_adr_postalcode': request.POST['collected_by_org_adr_postalcode'],
	  	  'collected_by_org_adr_region': request.POST['collected_by_org_adr_region'],
	   	  'collected_by_org_adr_street': request.POST['collected_by_org_adr_street'],
		  'collected_by_name_family': request.POST['collected_by_name_family'],
		  'collected_by_name_given': request.POST['collected_by_name_given'],
		  'collected_by_role': request.POST['collected_by_role']}
        problem_xml = render_raw('LabResult', params, type='xml')

        # add the problem
        client = get_indivo_client(request)
        problem_xml = problem_xml.encode('ascii', 'xmlcharrefreplace')
#        resp, content = client.document_create(record_id=request.session['record_id'], body=problem_xml,
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
        resp, content = client.generic_list(record_id=record_id, data_model="LabResult", body=query_params)

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
            raise Exception("Error creating new lab: %s"%content)

        # add a notification
        # let's not do this anymore because it's polluting the healthfeed
        client.record_notify(record_id=request.session['record_id'],
                              body={'content':'a new lab has been added to your labs list"'})

        return HttpResponseRedirect(reverse(list_labs))




def code_lookup(request):
    client = get_indivo_client(request)

    query = request.GET['query']

    # reformat this for the jQuery autocompleter
    resp, content = client.coding_system_query(system_short_name='loinc', body={'q':query})
    if resp['status'] != '200':
        # TODO: handle errors
        # But this Indivo instance might not support codingsystem lookup, so let's pass
        pass
    codes = simplejson.loads(content)
    formatted_codes = {'query': query, 'suggestions': [c['physician_value'] for c in codes], 'data': codes}

    return HttpResponse(simplejson.dumps(formatted_codes), mimetype="text/plain") 



def archived_lab(request, lab_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
    
        resp, content = client.document_set_status(record_id=record_id, document_id=lab_id, body={'status':'archived', 'reason':'removed by user'}) 
        return HttpResponseRedirect(reverse(list_labs))
        #return render_template('newLab')



def archived_labs(request):
    # read in query params
    limit = int(request.GET.get('limit', 15))
    offset = int(request.GET.get('offset', 0))
    order_by = request.GET.get('order_by', 'collected_at') # test_name_title, created_at, collected_at
    lab_status = request.GET.get('lab_status', 'All') # final, corrected, preliminary
    lab_status_display = LAB_STATUSES.get(lab_status, 'All')
    status = request.GET.get('status', 'archived')
    #read in previous values from session
    previous_date_start = request.session.get("date_start", None)
    previous_date_end = request.session.get("date_end", None)

    if request.session.has_key('record_id'):
        record_id = request.session['record_id']
        client = get_indivo_client(request)

        # retrieve a min date for labs
        oldest_params = {'limit': '1', 'order_by': 'collected_at'}
        if lab_status in LAB_STATUSES:
            oldest_params['status_identifier'] = lab_status
        resp, content = client.generic_list(record_id=record_id, data_model="LabResult", body=oldest_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching oldest lab: %s"%content)
        oldest_lab = parse_labs(simplejson.loads(content))
        if len(oldest_lab) > 0:
            oldest_lab_date = oldest_lab[0]['collected_at']
        else:
            oldest_lab_date = datetime.datetime.utcnow()

        max_date_string = datetime.datetime.utcnow().isoformat() + 'Z'
        min_date_string = datetime.datetime.combine(oldest_lab_date, datetime.time()).isoformat() + 'Z'
        date_start_string = request.GET.get('date_start', min_date_string)
        date_end_string = request.GET.get('date_end', max_date_string)

        #resets when changing date start/end
        if previous_date_start != date_start_string or previous_date_end != date_end_string:
            offset = 0

        #save off params in session
        request.session['date_start'] = date_start_string
        request.session['date_end'] =  date_end_string
         
        # set params for lab query
        parameters = {'limit': limit, 'offset': offset, 'order_by': order_by, 'status': status}
        parameters.update({'date_range': 'collected_at*' + date_start_string + '*' + date_end_string})
        if lab_status in LAB_STATUSES:
            parameters['status_identifier'] = lab_status
        resp, content = client.generic_list(record_id=record_id, data_model="LabResult", body=parameters)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching labs: %s"%content)
        labs = parse_labs(simplejson.loads(content))
    else:
        #TODO: not the case anymore
        print 'FIXME: no client support for labs via carenet. See problems app for an example.. Exiting...'
        return

    # build a description for the range of results shown and calculate offsets
    next_offset = None
    prev_offset = None
    num_labs = len(labs)
    if num_labs == 0 and offset == 0:
        range_description = _('No Results')
    elif num_labs == 0:
        range_description = _('End of Results')
    else:
        range_description = _('Showing Results ') + str(offset + 1) + '-' + str(offset + num_labs)
        if limit == num_labs:
            next_offset = offset + limit

    if offset > 0:
        prev_offset = offset - limit
        if prev_offset < 0:
            prev_offset = 0

    return render_to_response("labs/templates/archived_list.html", {'labs': labs,
                                                           'lab_statuses': LAB_STATUSES,
                                                           'STATIC_HOME': settings.STATIC_HOME,
                                                           'order_by': order_by,
                                                           'limit': limit,
                                                           'offset': offset,
                                                           'lab_status_id': lab_status,
                                                           'lab_status_display': lab_status_display,
                                                           'status': status,
                                                           'next_offset': next_offset,
                                                           'prev_offset': prev_offset,
                                                           'range_description': range_description,
                                                           'num_labs': num_labs,
                                                           'min_date': min_date_string,
                                                           'max_date': max_date_string,
                                                           'date_start': date_start_string,
                                                           'date_end': date_end_string}
    )



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

    return HttpResponseRedirect(reverse(list_labs))


def restore_lab(request,lab_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=lab_id, body={'status':'active', 'reason':'removed by user'})
        return HttpResponseRedirect(reverse(archived_labs)) 


def edit_lab(request, lab_id):

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
           resp, content = client.record_specific_document(record_id=record_id, document_id=lab_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document: %s"%content)
           doc_xml = content

           # read the document's metadata
           resp, content = client.record_document_meta(record_id=record_id, document_id=lab_id)
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
           resp, content = client.carenet_document(carenet_id=carenet_id, document_id=lab_id)
           if resp['status'] != '200':
               # TODO: handle errors
               raise Exception("Error fetching document from carenet: %s"%content)
           doc_xml = content
       doc = parse_xml(doc_xml)
       LabResult = parse_sdmx_problem(doc, ns=True)

       if doc_meta_xml:
           doc_meta = parse_xml(doc_meta_xml)
           meta = parse_meta(doc_meta)
       else:
           meta = None

       record_label = record.attrib['label']
       surl_credentials = client.get_surl_credentials()

       #return render_template('one_edit', {'allergy':allergy 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'allergy_id': allergy_id, 'surl_credentials': surl_credentials})
       return render_template('one_edit', {'LabResult':LabResult, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'lab_id': lab_id, 'surl_credentials': surl_credentials})
    else:


        collected_at = request.POST['collected_at']
        if collected_at.find("T00:00:00Z")== -1:
            collected_at = request.POST['collected_at'] + 'T00:00:00Z'

        params = {'abnormal_interpretation_title': request.POST['abnormal_interpretation_title'],
                  'abnormal_interpretation_system': 'http://smartplatforms.org/terms/codes/LabResultInterpretation#',
                  'abnormal_interpretation_identifier': request.POST['abnormal_interpretation_title'],
                  'accession_number': request.POST['accession_number'],
                  'test_name_title': request.POST['test_name_title'],
                  'test_name_system': 'http://purl.bioontology.org/ontology/LNC/',
                  'test_name_identifier': request.POST['test_name_identifier'],
                  'status_title': request.POST['status_title'],
                  'status_system': 'http://smartplatforms.org/terms/codes/LabStatus#',
                  'status_identifier':request.POST['status_title'],
                  'notes': request.POST['notes'],
                  'quantitative_result_non_critical_range_max_value': request.POST['quantitative_result_non_critical_range_max_value'],
                  'quantitative_result_non_critical_range_max_unit': request.POST['quantitative_result_non_critical_range_max_unit'],
                  'quantitative_result_non_critical_range_min_value': request.POST['quantitative_result_non_critical_range_min_value'],
                  'quantitative_result_non_critical_range_min_unit': request.POST['quantitative_result_non_critical_range_min_unit'],
                  'quantitative_result_normal_range_max_value': request.POST['quantitative_result_normal_range_max_value'],
                  'quantitative_result_normal_range_max_unit': request.POST['quantitative_result_normal_range_max_unit'],
                  'quantitative_result_normal_range_min_value': request.POST['quantitative_result_normal_range_min_value'],
                  'quantitative_result_normal_range_min_unit': request.POST['quantitative_result_normal_range_min_unit'],
                  'quantitative_result_value_value': request.POST['quantitative_result_value_value'],
                  'quantitative_result_value_unit': request.POST['quantitative_result_value_unit'],
                  'collected_at': collected_at,
                  'collected_by_org_name': request.POST['collected_by_org_name'],
                  'collected_by_org_adr_country': request.POST['collected_by_org_adr_country'],
                  'collected_by_org_adr_city': request.POST['collected_by_org_adr_city'],
                  'collected_by_org_adr_postalcode': request.POST['collected_by_org_adr_postalcode'],
                  'collected_by_org_adr_region': request.POST['collected_by_org_adr_region'],
                  'collected_by_org_adr_street': request.POST['collected_by_org_adr_street'],
                  'collected_by_name_family': request.POST['collected_by_name_family'],
                  'collected_by_name_given': request.POST['collected_by_name_given'],
                  'collected_by_role': request.POST['collected_by_role']}
        lab_xml = render_raw('LabResult', params, type='xml')


        client = get_indivo_client(request)
        record_id = request.session.get('record_id', None)
        lab_xml = lab_xml.encode('ascii', 'xmlcharrefreplace')
       # add the problem
       #resp, content = client.record_app_document_create_or_update(pha_email="procedures@apps.indivo.org", document_id=procedure_id, body=procedure_xml)
        resp, content = client.document_version(record_id=request.session['record_id'], document_id=lab_id, body=lab_xml, headers={}, content_type='application/xml')
       #resp, content = client.document_create(record_id=request.session['record_id'], body=procedure_xml, content_type='application/xml')

        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error creatiTANM AASASHASKLng new lab: %s"%content)
 # add a notification
       # let's not do this anymore because it's polluting the healthfeed
       # client.record_notify(record_id=request.session['record_id'],
       #                      body={'content':'a new problem has been added to your problem list'})



        return HttpResponseRedirect(reverse(list_labs))



def one_lab(request,lab_id):
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
         resp, content = client.record_specific_document(record_id=record_id, document_id=lab_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error fetching document: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.record_document_meta(record_id=record_id, document_id=lab_id)
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
         resp, content = client.carenet_document(carenet_id=carenet_id, document_id=lab_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error fetching document from carenet: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=lab_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error fetching document metadata from carenet: %s"%content)
         doc_meta_xml = content

    doc = parse_xml(doc_xml)
    lab = parse_sdmx_problem(doc, ns=True)

    if doc_meta_xml:
        doc_meta = parse_xml(doc_meta_xml)
        meta = parse_meta(doc_meta)
    else:
        meta = None

    record_label = record.attrib['label']
    surl_credentials = client.get_surl_credentials()

    return render_template('one', {'lab':lab, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'lab_id': lab_id, 'surl_credentials': surl_credentials})

