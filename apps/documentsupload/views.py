"""
Views for the Indivo Documents Upload app
Chatzimina Maria
ICS-FORTH
"""

from utils import *
import uuid
import urllib
import urllib2
import requests
import json

from django.utils import simplejson
import tempfile
import os
# We'll render HTML templates and access data sent by POST
# using the request object from flask. Redirect and url_for
# will be used to redirect the user once the upload is done
# and send_from_directory will help us to send/show on the
# browser the file that the user just uploaded
from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug import secure_filename
from django import forms
#from django.shortcuts import render_to_response
#from django.template import RequestContext
#from django.http import HttpResponseRedirect
#from django.core.urlresolvers import reverse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from django.conf import settings
from django.db import models
from PIL import Image
import StringIO
import magic
import uuid
import datetime
import time


class Document(models.Model):
    docfile = models.FileField(upload_to="test.jpg")


class DocumentForm(forms.Form):
    docfile = forms.FileField(
        label='Select a file',
        help_text='max. 42 megabytes'
    )


# Initialize the Flask application
app = Flask(__name__)


# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = '/media/data/hatzimin/web/indivo_ui_server/apps/documentsupload/static/files'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# This route will show a form to perform an AJAX request
# jQuery is loaded to execute the request and update the
# value of the operation
@app.route('/')





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

    ##if not request.session.has_key('documents_uploads_access_token'):
        # request a request token
    req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
    request.session['request_token'] = req_token

    return HttpResponseRedirect(client.auth_redirect_url)
    if 1==2:
       if datetime.datetime.now() > request.session['documents_uploads_time'] + datetime.timedelta(minutes=5):

         req_token = client.fetch_request_token(params)

    # store the request token in the session for when we return from auth
         request.session['request_token'] = req_token

         return HttpResponseRedirect(client.auth_redirect_url)
       else:
         access_token=request.session['documents_uploads_access_token']
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
         return HttpResponseRedirect(reverse(documents_upload))

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
    request.session['documents_uploads_access_token']=access_token
    request.session['documents_uploads_time']=datetime.datetime.now()
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
    return HttpResponseRedirect(reverse(documents_upload))


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

    return HttpResponseRedirect(reverse(documents_upload))

def documents_upload(request):
    
 
    client = get_indivo_client(request)
    
    in_carenet = request.session.has_key('carenet_id')
    if not in_carenet:
        record_id = request.session['record_id']
        INDIVO_IP = settings.INDIVO_IP
        jsonData = None
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
        resp, content = client.generic_list(record_id=record_id, data_model="Filedocument", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems: %s"%content)
        docs = simplejson.loads(content)

    else:
        record_id = ""#request.session['record_id']
        INDIVO_IP = settings.INDIVO_IP
        jsonData = None

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
        #resp2, content2 = client.carenet_document_list(carenet_id=carenet_id)
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)
        #record2 = parse_xml(content2)
        # read problems from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Filedocument", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content)
        
        docs = simplejson.loads(content)
        
    docs = map(process_problem, docs)
    record_label = record.attrib['label']
    num_docs = len(docs)
    

    # Route that will process the file upload
    # Ge the name of the uploaded file

#    if request.method == 'POST':
        
 #       form = DocumentForm(request.POST, request.FILES)
  #      STATIC=settings.STATIC_HOME

   #     if form.is_valid():
    #        file = request.FILES['docfile']
     #       filename=uuid.uuid4()

            #request.FILES['docfile'].name
      #      path = default_storage.save(settings.MEDIA_ROOT+'/documents_app/'+str(filename), ContentFile(file.read()))
       #     tmp_file = os.path.join(settings.MEDIA_ROOT, path)



#$            m=magic.open(magic.MAGIC_MIME)
 #           m.load()
  #         test=(m.file(settings.MEDIA_ROOT+'/documents_app/'+str(filename)))

            
#            mime = magic.Magic(mime=True)
 #           return HttpResponse(mime.from_file(settings.MEDIA_ROOT+'/documents_app/'+request.FILES['docfile'].name))

   #         test_file = open(settings.MEDIA_ROOT+'/documents_app/'+str(filename),'rb')
    #        response = HttpResponse(content=test_file)
     #       if "image" in test:
      #        response['Content-Type']= 'image/jpeg'
       #     else:
        #      response['Content-Type']= ''
         #   response['Content-Disposition'] = 'filename="%s"' \
          #                             % request.FILES['docfile'].name
#            return response
#            return HttpResponseRedirect('https://iphr.ics.forth.gr/indivo_files/documents_app/'+request.FILES['docfile'].name)           
            
#    else:
 #       form = DocumentForm() # A empty, unbound form
    surl_credentials = client.get_surl_credentials()

    return render_template('documents_upload', {'record_label': record_label, 'num_docs' : num_docs,'documents': docs, 'in_carenet':in_carenet,'jsonData':jsonData,'MEDIA_ROOT':settings.MEDIA_ROOT,'surl_credentials':surl_credentials,'record_id':record_id})


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file  = forms.FileField()



def handle_uploaded_file(file):
#    logging.debug("upload_here")
    return HttpResponse(file)
    if file:
        destination = open('/tmp/'+file.name, 'wb+')
        #destination = open('/tmp', 'wb+')
        for chunk in file.chunks():
            destination.write(chunk)
        destination.close()

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



def new_document(request):
    record_id = request.session['record_id']
    INDIVO_IP = settings.INDIVO_IP
    jsonData = None
  
#    today = datetime.date.today()
#    ts = time.time()
#    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')

    if request.method == "GET":
        return render_template('newdocument',{'jsonData': jsonData})
    else:

      if request.method == 'POST': 
	registered_date = request.POST['registered_date'] + 'T00:00:00Z' if request.POST['registered_date'] != '' else ''

        form = DocumentForm(request.POST, request.FILES)
        STATIC=settings.STATIC_HOME

        if form.is_valid():

            file = request.FILES['docfile']
            filename=uuid.uuid4()
            extention = file.name.split('.')[-1]

            #request.FILES['docfile'].name
            path = default_storage.save(settings.MEDIA_ROOT+'/documents_app/'+str(filename)+'.'+extention, ContentFile(file.read()))
            tmp_file = os.path.join(settings.MEDIA_ROOT, path)
           # try:
           #    m = magic.open(magic.MAGIC_NONE)
           #    m.load()
           #    ftype = m.file(tmp_file)
              
           # except AttributeError:
              
	    #  m = magic.Magic(mime=True)
            #  m.from_file(tmp_file)
            #  m = magic.from_file(tmp_file)
               
            
            mime = magic.Magic(mime=True)
            m = magic.from_file(tmp_file)

  #          m=magic.open(magic.MAGIC_MIME)  #error open
  #          m.load() #error open
#            test=(m.file(settings.MEDIA_ROOT+'/documents_app/'+str(filename)+'.'+extention))  #error open
            test = open(settings.MEDIA_ROOT+'/documents_app/'+str(filename)+'.'+extention,'rb')  # kai ssta duo

            response = HttpResponse(content=test)
            if "image" in test:
              response['Content-Type']= 'image/jpeg'
            else:
              response['Content-Type']= ''
            response['Content-Disposition'] = 'filename="%s"' \
                                       % filename


	    
            #registered_date=' '
            params = {'title': request.POST['title'],
                  'filename':str(filename)+'.'+extention,
                  'registered_date':registered_date,
                  'organisation': request.POST['organisation'],
		  'doctor': request.POST['doctor'],
 		  'reasons': request.POST['reasons'],
		  'diagnosis': request.POST['diagnosis'],
                  'comments': request.POST['comments'],
                  'type_of_file': request.POST['type']
		 }

            document_xml = render_raw('filedocument', params, type='xml')

            # add the problem
            client = get_indivo_client(request)
            resp, content = client.document_create(record_id=request.session['record_id'], body=document_xml,
                                               content_type='application/xml')
            if resp['status'] != '200':
            # TODO: handle errors
              raise Exception("Error creating new problem: %s"%content)

        # add a notification
        # let's not do this anymore because it's polluting the healthfe
        #if request.session['carenet_id']:
        #       resp,content = client.carenet_document_placement(record_id=request.session['record_id'],carenet_id=request.session['carenet_id'],document_id=request.session['document_id'])
            if resp['status'] != '200':
            # TODO: handle errors
              raise Exception("Error creating new problem: %s"%content)

        return HttpResponseRedirect(reverse(documents_upload))


def one_document(request,document_id):
    client = get_indivo_client(request)
    record_id = request.session.get('record_id', None)
 
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

         resp, content = client.record_specific_document(record_id=record_id, document_id=document_id)
         if resp['status'] != '200':
             # TODO: handle errors
             raise Exception("Error fetching document: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.record_document_meta(record_id=record_id, document_id=document_id)
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
         resp, content = client.carenet_document(carenet_id=carenet_id, document_id=document_id)
         if resp['status'] != '200':
            # TODO: handle errors
             raise Exception("Error fetching document from carenet: %s"%content)
         doc_xml = content

        # read the document's metadata
         resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=document_id)
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
    filename=problem['filename']
#    m=magic.open(magic.MAGIC_MIME) #error open
#    m.load() #error open
#    test=(m.file(settings.MEDIA_ROOT+'/documents_app/'+str(filename)))    #error open

    mime = magic.Magic(mime=True)
    m = magic.from_file(settings.MEDIA_ROOT+'/documents_app/'+str(filename))

  
    #mime = magic.Magic(mime=True)
    #       return HttpResponse(mime.from_file(settings.MEDIA_ROOT+'/documents_app/'+request.FILES['docfile'].name))
#    return HttpResponse(m)
#    test=(m.file(settings.MEDIA_ROOT+'/documents_app/'+str(filename)))
    test = open(settings.MEDIA_ROOT+'/documents_app/'+str(filename),'rb').read()
    response = HttpResponse(content=test)

    if "image" in m.lower():
              response['Content-Type']= 'image/jpeg'
    elif "pdf" in m.lower():
              response['Content-Type']= ''
    else:
              response['Content-Type']= 'application/force-download'

    response['Content-Disposition'] = 'filename="%s"'% filename 
    return response

def details(request,document_id):
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
        resp, content = client.record_specific_document(record_id=record_id, document_id=document_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching document: %s"%content)
        doc_xml = content

        # read the document's metadata
        resp, content = client.record_document_meta(record_id=record_id, document_id=document_id)
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
        resp, content = client.carenet_document(carenet_id=carenet_id, document_id=document_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching document from carenet: %s"%content)
        doc_xml = content

        # read the document's metadata
        resp, content = client.carenet_document_meta(carenet_id=carenet_id, document_id=document_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error fetching document metadata from carenet: %s"%content)
        doc_meta_xml = content

    doc = parse_xml(doc_xml)
    document = parse_sdmx_problem(doc, ns=True)

    if doc_meta_xml:
        doc_meta = parse_xml(doc_meta_xml)
        meta = parse_meta(doc_meta)
    else:
        meta = None

    record_label = record.attrib['label']
    surl_credentials = client.get_surl_credentials()

    return render_template('one_detail', {'document':document, 'record_label': record_label, 'meta': meta, 'record_id': record_id, 'document_id': document_id, 'surl_credentials': surl_credentials,'document_id':document_id})

def archived_document(request,document_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=document_id, body={'status':'archived', 'reason':'removed by user'})
        return HttpResponseRedirect(reverse(documents_upload))



def archived_documents(request):
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
        record_id = request.session['record_id']
        INDIVO_IP = settings.INDIVO_IP
        jsonData = None
        limit=int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
    #status = request.GET.get('status', 'archived')
        query_params = {
         'limit': limit,
         'offset': offset,
         #'order_by': 'startDate',
         'status': 'archived',
        }
        # get record info
        record_id = request.session['record_id']
        resp, content = client.record(record_id=record_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)


        # read problems
        resp, content = client.generic_list(record_id=record_id, data_model="Filedocument", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems: %s"%content)
        docs = simplejson.loads(content)

    else:
        record_id = ""#request.session['record_id']
        INDIVO_IP = settings.INDIVO_IP
        jsonData = None

        # get record info
        limit=int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
    #status = request.GET.get('status', 'archived')
        query_params = {
         'limit': limit,
         'offset': offset,
         #'order_by': 'startDate',
         'status': 'archived',
        }
        jsonData = None
        carenet_id = request.session['carenet_id']
        #resp2, content2 = client.carenet_document_list(carenet_id=carenet_id)
        resp, content = client.carenet_record(carenet_id=carenet_id)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading Record info: %s"%content)
        record = parse_xml(content)
        #record2 = parse_xml(content2)
        # read problems from the carenet
        resp, content = client.carenet_generic_list(carenet_id=carenet_id, data_model="Filedocument", body=query_params)
        if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error reading problems from carenet: %s"%content)

        docs = simplejson.loads(content)

    docs = map(process_problem, docs)
    record_label = record.attrib['label']
    num_docs = len(docs)
    surl_credentials = client.get_surl_credentials()

    return render_template('archived_list', {'record_label': record_label, 'num_docs' : num_docs,'documents': docs, 'in_carenet':in_carenet,'jsonData':jsonData,'MEDIA_ROOT':settings.MEDIA_ROOT,'surl_credentials':surl_credentials,'record_id':record_id})



def restore_document(request,document_id):
        client = get_indivo_client(request)
        record_id = request.session['record_id']
        resp, content = client.document_set_status(record_id=record_id, document_id=document_id, body={'status':'active', 'reason':'restored by user'})
        return HttpResponseRedirect(reverse(archived_documents))

