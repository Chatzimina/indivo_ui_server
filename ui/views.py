"""
Views for Indivo JS UI

"""
# pylint: disable=W0311, C0301
# fixme: rm unused imports
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError, Http404, HttpRequest
from django.contrib.auth.models import User
from django.core.exceptions import *
from django.core.urlresolvers import reverse
from django.core import serializers
from django.db import transaction
from django.conf import settings

from django.views.static import serve
from django.template import Template, Context
from django.utils import simplejson
from django.utils.translation import ugettext as _

from indivo_client_py.oauth2 import Request as OauthRequest

import xml.etree.ElementTree as ET
from lxml import etree
import urllib, re, copy
import psycopg2
import utils
import urlparse
from errors import ErrorStr
import requests
import json
#from utils import *
import uuid
import os
import sys
from subprocess import *
import subprocess
import datetime
import time
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
from bson import json_util
import logging
import base64
from django.utils.html import escape
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
from psycopg2.extras import RealDictCursor
import uuid

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
from django.core.urlresolvers import reverse

from django.utils import timezone
import requests

HTTP_METHOD_GET = 'GET'
HTTP_METHOD_POST = 'POST'
HTTP_METHOD_DELETE = 'DELETE'
LOGIN_PAGE = 'ui/login'
DEBUG = False

# init the IndivoClient python object
from indivo_client_py import IndivoClient

SERVER_PARAMS = {"api_base":settings.INDIVO_SERVER_LOCATION,
                 "authorization_base":settings.INDIVO_UI_SERVER_BASE}
CONSUMER_PARAMS = {"consumer_key": settings.CONSUMER_KEY,
                   "consumer_secret": settings.CONSUMER_SECRET}



def ignore_certificate_error(self, code):
        """Ignore certificate errors."""
        return True  # has an expired certificate.


def testfunc(request):
     record_id = request.session['record_id']
     text=''
     try:
       conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
#       conn.autocommit = True
       conn.set_isolation_level(0)
       conn.commit()
       cursor = conn.cursor()
       test=record_id
     except psycopg2.DatabaseError, e:
          existing_account_i="Cannot connect to db"

     linked_id=""

     try:

           cursor.execute( "SELECT linked_id FROM indivo_record where id='"+record_id+"'" )
           conn.commit()
           result = cursor.fetchall()
           tuples = result
           url = result
           for item in tuples:
              linked_id=(str(item[0]))


       #url2 = result[1]
     except psycopg2.DatabaseError, e:
           url=e
           if conn:
              conn.rollback()

           print 'Error %s' % e
     project_clicked=[]
     try:


           cursor.execute( "SELECT clicked FROM indivo_pdfdecision where patient_id='"+linked_id+"'" )
           conn.commit()
           result = cursor.fetchall()
           tuples = result

           for item in tuples:
               project_clicked.append(str(item[0]))
          
         

       #url2 = result[1]
     except psycopg2.DatabaseError, e:
                 project_clicked.append(e) 
                 if conn:
                   conn.rollback()

                 print 'Error %s' % e
     for i in project_clicked:
	if i == 'false':
           text='updated'
 
     return HttpResponse(text, content_type="text") 
# todo: safe for now, but revisit this (maybe make a global api object) later
def get_api(request=None):
    
    api = IndivoClient(SERVER_PARAMS, CONSUMER_PARAMS)
    if request:
        api.update_token(request.session.get('oauth_token_set'))
    
    return api


def tokens_p(request):

    try:

        ########### FIXME CHECK SECURITY ######################
        if request.session['oauth_token_set']:
            return True
        else:
            return False
    except KeyError:
        return False


def tokens_get_from_server(request, username, password):
    """
    This method will not catch exceptions raised by create_session, be sure to catch them!
    """
    # hack! re-initing IndivoClient here

    api = get_api()
    resp, content = api.session_create({'username' : username, 'password' : password})
    
    logging.debug("tokens_get_ftom_server: %s",str(content)) 
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
    
    return (resp, content)

def store_connect_secret(request, raw_credentials):
    xml_etree = etree.XML(raw_credentials)

    credentials = {
        "app_id": xml_etree.find('App').get("id"),
        "connect_token": xml_etree.findtext("ConnectToken"),
        "api_base": xml_etree.findtext('APIBase'), 
        "rest_token":xml_etree.findtext('RESTToken'),          
        "rest_secret": xml_etree.findtext('RESTSecret'), 
        "oauth_header": xml_etree.findtext('OAuthHeader'),
        }
    
    request.session[credentials["connect_token"]] = xml_etree.findtext('ConnectSecret')
    return credentials

def retrieve_connect_secret(request, connect_token_str):
    if connect_token_str:
        return request.session.get(connect_token_str, None)
    return None

def get_connect_credentials(request, account_id, app_email):
    api = get_api(request)
    data = {'record_id': request.GET.get('record_id', ''), 'carenet_id': request.GET.get('carenet_id', '')}
    resp, content = api.get_connect_credentials(account_email=account_id, pha_email=app_email, body=data)
    credentials = store_connect_secret(request, content)
    return HttpResponse(simplejson.dumps(credentials), content_type="application/json")

def loginOauthToken(request):

    username = request.GET.get('username')
    password = request.GET.get('password')
    
    try:
        logging.debug("tokens_get_ftom_server: ")
        res, content = tokens_get_from_server(request, username, password)
    except Exception as e:
        params['ERROR'] = ErrorStr(e[1])


    if res['status'] != '200':
      return HttpResponse('Not registered user in portal')
    else:
      returnstring = content.split("=")

      returns = returnstring[2].split("&")
      oauth_token_access = returns[0]
      return HttpResponse (oauth_token_access)



def sendEmailNewUser(request):
    contact_email = request.GET.get('contact_email')
    if not contact_email or not utils.is_valid_email(contact_email):
        return HttpResponseBadRequest("Contact email not valid")

    sendMail([contact_email],'no-reply@www.iphr.care','Register to iMC portal','Hello, please register to iMC portal in link https://www.iphr.care. A user asked to share his health information with you.',[])
    return HttpResponse('ok')


def sendMail(recipient,fro , subject, body,files=[]):
    import smtplib
    user = 'imanagecancerplatform@gmail.com'
    gmail_user = 'imanagecancerplatform@gmail.com'
    gmail_pwd = '19868888'
    FROM = user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        return HttpResponse( 'successfully sent the mail')
    except:
        return HttpResponse( "failed to send mail")

def sendMailold(to, fro, subject, text, files=[],server="localhost"):
    assert type(to)==list
    assert type(files)==list


    msg = MIMEMultipart()
    msg['From'] = fro
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for file in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(file,"rb").read() )
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"'
                       % os.path.basename(file))
        msg.attach(part)

    smtp = smtplib.SMTP(server)
    res = smtp.sendmail(fro, to, msg.as_string() )

    smtp.close()



def index(request):  #MERGE
    
#    record_id = request.GET.get('record_id', '')i
#    client = get_indivo_client(request)


    # do we have a record_id?

    record_id=""
#    record_id = request.POST.get('record_id', '') 
    if tokens_p(request):
      account_id = urllib.unquote(request.session['oauth_token_set']['account_id'])
    #record_id = urllib.unquote(request.session['oauth_token_set']['record_id']) 
      existing_account_i=""
      INDIVO_URL=settings.INDIVO_URL

      try:
       conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
#       conn.autocommit = True
       conn.set_isolation_level(0)
       conn.commit()
       cursor = conn.cursor()
      except psycopg2.DatabaseError, e:
          existing_account_i="Cannot connect to db"
    
      tuples = ''
      try:
        cursor.execute("SELECT account_id  FROM indivo_account where contact_email="+"'"+account_id+"'")
        existing_email = cursor.fetchall()
      except psycopg2.DatabaseError, e:
        existing_account_id="Cannot connect to db"
        if conn:
          conn.rollback()
          print "fail"
       
      tuples = existing_email
      for item in tuples:
        existing_account_i=str(item[0])
   
      querystring = "SELECT id FROM indivo_record where owner_id="+"'"+existing_account_i+"'"
      try:
        cursor.execute("SELECT id FROM indivo_record where owner_id="+"'"+existing_account_i+"'")
        existing_email = cursor.fetchall()
      except psycopg2.DatabaseError, e:
       existing_record_id="Cannot connect to db"
       if conn:
         conn.rollback()
         existing_record_id = "sadasdsada"
      tuples = existing_email
      for item in tuples:
        record_id=str(item[0])


 
    INDIVO_IP = settings.INDIVO_IP
    jsonData = " "
    r = " "
    if tokens_p(request):
        account_id = urllib.unquote(request.session['oauth_token_set']['account_id'])
        existing_username=''
        regex_http_          = re.compile(r'^HTTP_.+$')
        regex_content_type   = re.compile(r'^CONTENT_TYPE$')
        regex_content_length = re.compile(r'^CONTENT_LENGTH$')

        request_headers = {}
	uuid=''
        existing_record_id =''
        existing_account_id =''
        existing_username_id=''
        for header in request.META:
          if regex_http_.match(header) or regex_content_type.match(header) or regex_content_length.match(header):
             request_headers[header]= request.META[header]
#        s = request_headers.read()
          uuid = ''
          test=''
	  if 'HTTP_AUTHORIZATION' in request_headers:
            test = request_headers.get('HTTP_AUTHORIZATION',"empty")
            if test != 'empty':
              contents = test.split(',')
              for i in contents:
                if "croxy_uuid" in i:
                    uuid = i.split('=')
                    croxy_uuid = uuid[1]
                    uuid = croxy_uuid.strip('"')

#          if 'HTTP_AUTHORIZATION' in request_headers:
#            test = request_headers.get('HTTP_AUTHORIZATION',"empty")
#            if test != 'empty':
#              contents = test.split(',')
#
#              uuid = contents[8].split('=')
#              croxy_uuid = uuid
#              uuid = croxy_uuid.strip('"')

                    try:
                       conn = psycopg2.connect("dbname='indivo' user='indivo' host='iapetus.ics.forth.gr' password='indivo'")
#                       conn.autocommit = True
                       conn.set_isolation_level(0)
                       conn.commit()
                       cursor = conn.cursor()

                    except psycopg2.DatabaseError, e:
                       print "Cannot connect to db"


                    tuples = ''
                    try:
                       cursor.execute("SELECT record_id  FROM indivo_phrkey where custodix_id="+"'"+uuid+"'")
                       existing_record = cursor.fetchall()
                    except psycopg2.DatabaseError, e:

                       if conn:
                         conn.rollback()

                         print 'Error %s' % e
                    tuples = existing_record
                    for item in tuples:
                       existing_record_id=str(item[0])

                    try:
                       cursor.execute("SELECT owner_id  FROM indivo_record where id="+"'"+existing_record_id+"'")
                       existing_account = cursor.fetchall()
                    except psycopg2.DatabaseError, e:

                      if conn:
                        conn.rollback()

                        print 'Error %s' % e
        #existing_username = 'test'
                    tuples = existing_account
                    for item in tuples:
                       existing_account_id=str(item[0])
                    try:
                       cursor.execute("SELECT username  FROM indivo_accountauthsystem where account_id="+"'"+existing_account_id+"'")
                       existing_username = cursor.fetchall()
         
                    except psycopg2.DatabaseError, e:

                       if conn:
                         conn.rollback()

                         print 'Error %s' % e
                    tuples = existing_username
                    for item in tuples:
                         existing_username_id=str(item[0])

        return utils.render_template('ui/index', { 'ACCOUNT_ID': account_id,
                                                   'SETTINGS': settings, 'jsonData':jsonData,'record_id':record_id})
    
    return HttpResponseRedirect(reverse(login))

def forumlogin(request):

    forum = "https://www.iphr.care:8004"

    headers = {'User-Agent': 'Mozilla/5.0'}
    payload = {'username': 'diana', 'password': 'indivo_pass', 'redirect':'index.php', 'sid':'', 'login':'Login'}
    session = requests.Session()

    r = session.post(forum + "/ucp.php?mode=login", headers=headers, data=payload)
    return HttpResponse(r.text)


#def logout(request):
#    login_return_url = request.session.get('login_return_url')
#    request.session.flush()

    # if we had a callback url stored, redirect to that one
#    return HttpResponseRedirect(login_return_url or '/login/did_logout')

def login_backup(request, status):
    """
    clear tokens in session, show a login form, get tokens from indivo_server, then redirect to index or return_url
    FIXME: make note that account will be disabled after x failed logins!!!
    """

    # carry over login_return_url should we still have it
    return_url = request.session.get('login_return_url');
    request.session.flush()

    # generate a new session and get return_url
    if request.POST.has_key('return_url'):
        return_url = request.POST['return_url']
    elif request.GET.has_key('return_url'):
        return_url = request.GET['return_url']

    # save return_url
    if return_url:
        request.session['login_return_url'] = return_url

    # set up the template
    FORM_USERNAME = 'username'
    FORM_PASSWORD = 'password'
    params = {'SETTINGS': settings}
    if return_url:
        params['RETURN_URL'] = return_url

    if 'did_logout' == status:
        params['MESSAGE'] = _("You were logged out")
    elif 'changed' == status:
        params['MESSAGE'] = _("Your password has been changed")

    # process form vars
    if request.method == HTTP_METHOD_GET:
        return utils.render_template(LOGIN_PAGE, params)

    if request.method == HTTP_METHOD_POST:
        if request.POST.has_key(FORM_USERNAME) and request.POST.has_key(FORM_PASSWORD):
            username = request.POST[FORM_USERNAME].lower().strip()
            password = request.POST[FORM_PASSWORD]
        else:
            # Also checked initially in js
            params['ERROR'] = ErrorStr('Name or password missing')
            return utils.render_template(LOGIN_PAGE, params)
    else:
        utils.log('error: bad http request method in login. redirecting to /')
        return HttpResponseRedirect('/')

    # get tokens from the backend server and save in this user's django session

    try:
        res, content = tokens_get_from_server(request, username, password)
    except Exception as e:

        params['ERROR'] = ErrorStr(e[1])
        return utils.render_template(LOGIN_PAGE, params)

    if res['status'] != '200':
        if '403' == res['status']:
            params['ERROR'] = ErrorStr('Incorrect credentials')         # a 403 could also mean logging in to a disabled account!
        elif '400' == res['status']:
			params['ERROR'] = ErrorStr('Name or password missing')      # checked before; highly unlikely to ever arrive here
        else:
            params['ERROR'] = ErrorStr(content)
        return utils.render_template(LOGIN_PAGE, params)
    if request.session.has_key('login_return_url'):
        del request.session['login_return_url']
    return HttpResponseRedirect(return_url or '/')

def login(request, status):
    """
    clear tokens in session, show a login form, get tokens from indivo_server, then redirect to index or return_url
    FIXME: make note that account will be disabled after x failed logins!!!
    """

    # carry over login_return_url should we still have it
    return_url = request.session.get('login_return_url');

    request.session.flush()

    # generate a new session and get return_url
    if request.POST.has_key('return_url'):
        return_url = request.POST['return_url']
    elif request.GET.has_key('return_url'):
        return_url = request.GET['return_url']
    

    # save return_url
    if return_url:
        request.session['login_return_url'] = return_url

    # set up the template
    FORM_USERNAME = 'username'
    FORM_PASSWORD = 'password'
    params = {'SETTINGS': settings}
    if return_url:
        params['RETURN_URL'] = return_url

    if 'did_logout' == status:
        params['MESSAGE'] = _("You were logged out")
    elif 'changed' == status:
        params['MESSAGE'] = _("Your password has been changed")

    # process form vars
    if request.method == HTTP_METHOD_GET:
      if request.GET.get('username'):
        username = request.GET['username']
        password = request.GET['password']
      else:  
        return utils.render_template(LOGIN_PAGE, params)

    if request.method == HTTP_METHOD_POST:
        if request.POST.has_key(FORM_USERNAME) and request.POST.has_key(FORM_PASSWORD):
            username = request.POST[FORM_USERNAME].lower().strip()
            password = request.POST[FORM_PASSWORD]
        else:
            # Also checked initially in js
            params['ERROR'] = ErrorStr('Name or password missing')
            return utils.render_template(LOGIN_PAGE, params)
    #else:
        #utils.log('error: bad http request method in login. redirecting to /')
        #return HttpResponseRedirect('/')

    # get tokens from the backend server and save in this user's django session

    try:
       res, content = tokens_get_from_server(request, username, password)

    except Exception as e:

        params['ERROR'] = ErrorStr(e[1])
        return utils.render_template(LOGIN_PAGE, params)

    if res['status'] != '200':
   
        if '403' == res['status']:
            params['ERROR'] = ErrorStr('Incorrect credentials')         # a 403 could also mean logging in to a disabled account!
        elif '400' == res['status']:
            params['ERROR'] = ErrorStr('Name or password missing')      # checked before; highly unlikely to ever arrive here
        else:
            params['ERROR'] = ErrorStr(content)
        return utils.render_template(LOGIN_PAGE, params)
    if request.session.has_key('login_return_url'):

        del request.session['login_return_url']

    if request.GET.get('app'):
       return HttpResponseRedirect('/?app=settings')
#    request.set_cookie("app2go",  "yes")
#    request.session['app2go'] = "yes"
    return HttpResponseRedirect(return_url or '/')
   


def logout(request):
    login_return_url = request.session.get('login_return_url')
    request.session.flush()
    regex_http_          = re.compile(r'^HTTP_.+$')
    regex_content_type   = re.compile(r'^CONTENT_TYPE$')
    regex_content_length = re.compile(r'^CONTENT_LENGTH$')

    request_headers = {}
    for header in request.META:
     if regex_http_.match(header) or regex_content_type.match(header) or regex_content_length.match(header):
        request_headers[header]= request.META[header]
        uuid = ''
        test=''
    return HttpResponseRedirect(login_return_url or '/login/did_logout')


def deleteaccountadmin(request,deleteaccount_id):

    api = get_api()
    token = request.session.get('oauth_token_set')
    account_id = request.POST.get('account_id')
    account_id = urllib.unquote(token.get('account_id') if token else '')

    resp,content =api.account_set_state(account_email=deleteaccount_id,body={'state':'disabled'})
    if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error%s"%content)
    return HttpResponseRedirect(reverse(admin_console))


def deleteaccount(request):
    # create the client to Indivo


    # do we have a record_id?

    api = get_api()
    token = request.session.get('oauth_token_set')
    account_id = request.POST.get('account_id')
    account_id = urllib.unquote(token.get('account_id') if token else '')
    resp,content =api.account_set_state(account_email=account_id,body={'state':'retired'})
    if resp['status'] != '200':
            # TODO: handle errors
            raise Exception("Error%s"%content)
    return HttpResponseRedirect('/login/did_logout')

def bugs(request):
    try:
               conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
               conn.set_isolation_level(0)
#               conn.autocommit = True
               conn.commit()
               cursor = conn.cursor()

    except psycopg2.DatabaseError, e:
               return HttpResponse("Cannot connect to db")

    columns = ('txtFullname', 'txtEmail', 'selApp', 'txtDescription', 'txtAtt' )

    try:

           cursor.execute("SELECT * FROM public.indivo_reportbugs");
           conn.commit()
	   result = cursor.fetchall()

    except psycopg2.DatabaseError, e:
           return HttpResponse(e)
           if conn:
              conn.rollback()

           print 'Error %s' % e
    
    return HttpResponse(json.dumps(result)) 


def reportbugs(request):
    if request.method == 'POST':
        txtFullname = request.POST['txtFullname']
        txtEmail = request.POST['txtEmail']
        selApp = request.POST['selApp']
        txtDescription = request.POST['txtDescription']
        hdnImageData = request.POST['hdnImageData']
        filename = ''      
        if 'txtAtt' in request.FILES: 
#        if request.FILES['txtAtt'] is not None:        
         file = request.FILES['txtAtt']

         filename=uuid.uuid4()
         extention = file.name.split('.')[-1]

            #request.FILES['docfile'].name
         path = default_storage.save(settings.MEDIA_ROOT+'/reportbugs_app/'+str(filename)+'.'+extention, ContentFile(file.read()))
         tmp_file = os.path.join(settings.MEDIA_ROOT, path)

         mime = magic.Magic(mime=True)
         m = magic.from_file(tmp_file)
         test = open(settings.MEDIA_ROOT+'/reportbugs_app/'+str(filename)+'.'+extention,'rb')  # kai ssta duo

         response = HttpResponse(content=test)
         if "image" in test:
              response['Content-Type']= 'image/jpeg'
         else:
              response['Content-Type']= ''
         response['Content-Disposition'] = 'filename="%s"' \
                                       % filename
         filename=str(filename)+'.'+extention


        try:
               conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
               conn.set_isolation_level(0)
#               conn.autocommit = True
               conn.commit()
               cursor = conn.cursor()

        except psycopg2.DatabaseError, e:
               return HttpResponse("Cannot connect to db")


#        return HttpResponse("INSERT INTO indivo_reportbugs("+'"'+"txtFullname"+'", "'+"txtEmail"+'", "'+"selApp"+'", "'+"txtDescription"+'", "'+"txtAtt"+'"'+",id)VALUES ("+txtFullname+","+txtEmail+","+selApp+","+selApp+","+txtDescription+","+hdnImageData+")")
        
        try:

           cursor.execute("INSERT INTO indivo_reportbugs("+'"'+"txtFullname"+'", "'+"txtEmail"+'", "'+"selApp"+'", "'+"txtDescription"+'", "'+"txtAtt"+'"'+") VALUES ("+"'"+txtFullname+"'"+","+"'"+txtEmail+"'"+","+"'"+selApp+"'"+","+"'"+txtDescription+"'"+","+"'"+filename+"'"+")")
           conn.commit()

        except psycopg2.DatabaseError, e:
           return HttpResponse(e)
           if conn:
              conn.rollback()

           print 'Error %s' % e

        return HttpResponse('<html><head><script>alert("Problem reported successfully");location.href="reportbugs"</script></head></html>')
    return utils.render_template('ui/reportbugs', {'SETTINGS': settings})


def admin_audits(request):

    api = get_api()

    pilot =''
#    pilot = request.POST['pilot']
    pilot = request.GET.get('pilot')
    german_string = ''
    german_string_apps = ''
    italian_string = ''
    italian_string_apps = '' 
    try:
          conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'");
#          conn.autocommit = True
          conn.set_isolation_level(0)
          conn.commit()
          cursor = conn.cursor()

    except psycopg2.DatabaseError, e:

           print 'Error %s' % e
    if pilot == 'none':
      try:

          cursor.execute("SELECT * FROM indivo_auditlog WHERE timestamp >= '2017-08-31'")
          conn.commit()
          result2 = cursor.fetchall()


      except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()


      result = []
      if result2:
        for r in result2:

             if "@" not in r[5]:

                try:

                  cursor.execute("SELECT account_id FROM indivo_accountauthsystem WHERE username= '"+r[5]+"'")
                  conn.commit()
                  account_id = cursor.fetchall()


                except psycopg2.DatabaseError, e:
                         return HttpResponse(e)
                         if conn:
                            conn.rollback()
                if account_id:
                 try:  

                  cursor.execute("SELECT contact_email FROM indivo_account WHERE account_id= '"+account_id[0][0]+"'")
                  conn.commit()
                  contact_email = cursor.fetchall()


                 except psycopg2.DatabaseError, e:
                         return HttpResponse(e)
                         if conn:
                            conn.rollback()
                 tmp=(r[0],r[1],r[2],r[3],r[4],contact_email[0][0],r[6],r[7],r[8])
                 result.append(tmp)
             else:

                tmp=(r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8])
#               return HttpResponse(tuple(newdoc))
                result.append(tmp)


      res = json.dumps(result,default=json_util.default)
      documents =[]
      documents_r= []
      factids = []
      records_audit = []
      newdoc=[]
      finaldoc=[]
  
      try:
          cursor.execute("SELECT id, req_url,view_func,record_id, effective_principal_email,datetime FROM indivo_audit WHERE req_url LIKE '%reports%'  AND datetime >= '2017-08-31'")
          conn.commit()
	  document_r = cursor.fetchall()

	  for doc in document_r:

                test=(doc[0],'imcportal',doc[1].rsplit('/')[4],doc[2],doc[3],doc[4],'',doc[5],'0')
#		return HttpResponse(tuple(newdoc))
          	finaldoc.append(test)
      except psycopg2.DatabaseError, e:

         return HttpResponse(e)
    
    if pilot == 'german_pilot':
      try:

          cursor.execute("SELECT contact_email FROM indivo_account WHERE pilot= 'german pilot'")
          conn.commit()
          accounts_emails = cursor.fetchall()


      except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()




      try:

          cursor.execute("SELECT account_id FROM indivo_account WHERE pilot= 'german pilot'")
          conn.commit()
          accounts_ids = cursor.fetchall()


      except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()


      for ids in accounts_ids:

         try:

           cursor.execute("SELECT username FROM indivo_accountauthsystem WHERE account_id= '"+ids[0]+"'")
           conn.commit()
           result_username = cursor.fetchall()

           accounts_emails = accounts_emails + result_username


         except psycopg2.DatabaseError, e:
           return HttpResponse(e)
         if conn:
            conn.rollback()

      li = [x[0] for x in accounts_emails]

      for i in li: 
	if i in li[-1]:
           german_string += " effective_principal_email = '"+i+"'"
           german_string_apps +=" patient ='"+i+"'"
  	else:
           german_string+="effective_principal_email = '"+i+"' OR "
           german_string_apps+="patient = '"+i+"' OR "

      if german_string_apps:
         query_apps = "SELECT * FROM indivo_auditlog WHERE timestamp >= '2017-08-31' AND ("+german_string_apps+")"
         
         try:

           cursor.execute(query_apps)
           conn.commit()
           result2 = cursor.fetchall()

	
         except psycopg2.DatabaseError, e:
           return HttpResponse(e)
           if conn:
            conn.rollback()

      else:
         result2 = [] 


      result = []
      if result2:
        for r in result2:

             if "@" not in r[5]:

                try:

                  cursor.execute("SELECT account_id FROM indivo_accountauthsystem WHERE username= '"+r[5]+"'")
                  conn.commit()
                  account_id = cursor.fetchall()


                except psycopg2.DatabaseError, e:
                         return HttpResponse(e)
                         if conn:
                            conn.rollback()
                try:

                  cursor.execute("SELECT contact_email FROM indivo_account WHERE account_id= '"+account_id[0][0]+"'")
                  conn.commit()
                  contact_email = cursor.fetchall()


                except psycopg2.DatabaseError, e:
                         return HttpResponse(e)
                         if conn:
                            conn.rollback()
                tmp=(r[0],r[1],r[2],r[3],r[4],contact_email[0][0],r[6],r[7],r[8])
                result.append(tmp)
             else:

                tmp=(r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8])
#               return HttpResponse(tuple(newdoc))
                result.append(tmp)

      res = json.dumps(result,default=json_util.default)
      documents =[]
      documents_r= []
      factids = []
      records_audit = []
      newdoc=[]
      finaldoc=[]
  
      if german_string:
	 query = "SELECT id, req_url,view_func,record_id, effective_principal_email,datetime FROM indivo_audit WHERE (req_url LIKE '%reports%'  AND datetime >= '2017-08-31') AND ("+german_string+")"

         try:
          cursor.execute(query)
          conn.commit()
          document_r = cursor.fetchall()

          for doc in document_r:

                test=(doc[0],'imcportal',doc[1].rsplit('/')[4],doc[2],doc[3],doc[4],'',doc[5],'0')

                finaldoc.append(test)
         except psycopg2.DatabaseError, e:

            return HttpResponse(e)
      else:
          document_r = ''

   

    if pilot == 'italian_pilot':
      try:

          cursor.execute("SELECT contact_email FROM indivo_account WHERE pilot= 'italian pilot'")
          conn.commit()
          accounts_emails = cursor.fetchall()


      except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()




      try:

          cursor.execute("SELECT account_id FROM indivo_account WHERE pilot= 'italian pilot'")
          conn.commit()
          accounts_ids = cursor.fetchall()


      except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()


      for ids in accounts_ids:

         try:

           cursor.execute("SELECT username FROM indivo_accountauthsystem WHERE account_id= '"+ids[0]+"'")
           conn.commit()
           result_username = cursor.fetchall()

           accounts_emails = accounts_emails + result_username


         except psycopg2.DatabaseError, e:
           return HttpResponse(e)
         if conn:
            conn.rollback()

      li = [x[0] for x in accounts_emails]

      for i in li: 
	if i in li[-1]:
           italian_string += " effective_principal_email = '"+i+"'"
           italian_string_apps +=" patient ='"+i+"'"
  	else:
           italian_string+="effective_principal_email = '"+i+"' OR "
           italian_string_apps+="patient = '"+i+"' OR "

      if italian_string_apps:
         query_apps = "SELECT * FROM indivo_auditlog WHERE timestamp >= '2017-08-31' AND ("+italian_string_apps+")"

         try:

           cursor.execute(query_apps)
           conn.commit()
           result2 = cursor.fetchall()


         except psycopg2.DatabaseError, e:
           return HttpResponse(e)
           if conn:
            conn.rollback()

      else:
         result2 = []

      result = [] 
      if result2:
	for r in result2:

	     if "@" not in r[5]:

		try:

        	  cursor.execute("SELECT account_id FROM indivo_accountauthsystem WHERE username= '"+r[5]+"'")
	          conn.commit()
        	  account_id = cursor.fetchall()


	        except psycopg2.DatabaseError, e:
		         return HttpResponse(e)
	        	 if conn:
	        	    conn.rollback()
		try:

                  cursor.execute("SELECT contact_email FROM indivo_account WHERE account_id= '"+account_id[0][0]+"'")
                  conn.commit()
                  contact_email = cursor.fetchall()


                except psycopg2.DatabaseError, e:
                         return HttpResponse(e)
                         if conn:
                            conn.rollback()
	        tmp=(r[0],r[1],r[2],r[3],r[4],contact_email[0][0],r[6],r[7],r[8])
                result.append(tmp)
	     else:

		tmp=(r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8])
#               return HttpResponse(tuple(newdoc))
                result.append(tmp)

		

      res = json.dumps(result,default=json_util.default)
      documents =[]
      documents_r= []
      factids = []
      records_audit = []
      newdoc=[]
      finaldoc=[]
  
      if italian_string:
	 query = "SELECT id, req_url,view_func,record_id, effective_principal_email,datetime FROM indivo_audit WHERE (req_url LIKE '%reports%'  AND datetime >= '2017-08-31') AND ("+italian_string+")"
	 
         try:
          cursor.execute(query)
          conn.commit()
          document_r = cursor.fetchall()

          for doc in document_r:

                test=(doc[0],'imcportal',doc[1].rsplit('/')[4],doc[2],doc[3],doc[4],'',doc[5],'0')
#               return HttpResponse(tuple(newdoc))
                finaldoc.append(test)
         except psycopg2.DatabaseError, e:

            return HttpResponse(e)
      else:
          document_r = ''

    res = json.dumps(finaldoc+result,default=json_util.default)

    return HttpResponse(res)
    


def audit_per_week(request):

    api = get_api()

    pilot =''
#    pilot = request.POST['pilot']
    app = request.GET.get('app')
    start_date = request.GET.get('start_date') 
    end_date = request.GET.get('end_date')
    pilot = request.GET.get('pilot')
    patient = request.GET.get('patient')
    german_string = '' 
    italian_string = '' 
    german_string_apps = ''
    italian_string_apps = ''   
    res = '' 
    try:
          conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'");
#          conn.autocommit = True
          conn.set_isolation_level(0)
          conn.commit()
          cursor = conn.cursor()

    except psycopg2.DatabaseError, e:

          return HttpResponse(e)
 
    if pilot == 'none':
     if app == 'game' or app == 'game_for_adults' or app == 'imanagemyhealth' or app == 'myhealthavatar':
      try:

#          cursor.execute("SELECT * FROM indivo_auditlog WHERE timestamp >= '2017-08-31'")
          cursor.execute("SELECT date_trunc('week', timestamp) AS "+'"'+"Week"+'"'+" , count(app_name) ,app_name FROM indivo_auditlog WHERE timestamp >= '"+start_date+"' AND timestamp <= '"+end_date+"' and app_name='"+app+"' GROUP BY "+'"'+"Week"+'"'+", app_name ORDER BY "+'"'+"Week"+'"')

          conn.commit()
          result_per_week = cursor.fetchall()


      except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()

      if result_per_week:
           res = json.dumps(result_per_week,default=json_util.default)
     else:

      

      try:
          cursor.execute("SELECT date_trunc('week', datetime) AS "+'"'+"Week"+'"'+" , count(view_func) ,view_func FROM indivo_audit WHERE (req_url LIKE '%reports/"+app+"%'  AND datetime >= '"+start_date+"' AND datetime <= '"+end_date+"')GROUP BY "+'"'+"Week"+'"'+", view_func ORDER BY "+'"'+"Week"+'"')
          conn.commit()
          result_per_week = cursor.fetchall()

      except psycopg2.DatabaseError, e:

         return HttpResponse(e)

      if result_per_week:
           res = json.dumps(result_per_week,default=json_util.default)

    if pilot == 'german_pilot':

     try:

          cursor.execute("SELECT contact_email FROM indivo_account WHERE pilot= 'german pilot'")
          conn.commit()
          accounts_emails = cursor.fetchall()


     except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()




     try:

          cursor.execute("SELECT account_id FROM indivo_account WHERE pilot= 'german pilot'")
          conn.commit()
          accounts_ids = cursor.fetchall()


     except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()


     for ids in accounts_ids:

         try:

           cursor.execute("SELECT username FROM indivo_accountauthsystem WHERE account_id= '"+ids[0]+"'")
           conn.commit()
           result_username = cursor.fetchall()

           accounts_emails = accounts_emails + result_username


         except psycopg2.DatabaseError, e:
           return HttpResponse(e)
         if conn:
            conn.rollback()

     li = [x[0] for x in accounts_emails]

     for i in li:
        if i in li[-1]:
           german_string += " effective_principal_email = '"+i+"'"
           german_string_apps +=" patient ='"+i+"'"
        else:
           german_string+="effective_principal_email = '"+i+"' OR "
           german_string_apps+="patient = '"+i+"' OR "

  

     if app == 'game' or app == 'game_for_adults' or app == 'myhealthavatar' or app == 'imanagemyhealth':

      if german_string_apps:
         query_apps = "SELECT date_trunc('week', timestamp) AS"+ '"'+"Week"+'"'+" , count(app_name) ,app_name FROM indivo_auditlog WHERE (timestamp >= '"+start_date+"' AND timestamp <= '"+end_date+"' and app_name='"+app+"') AND ("+german_string_apps+") GROUP BY"+' "'+"Week"+'"'+", app_name ORDER BY"+ '"'+"Week"+'"'

         try:

           cursor.execute(query_apps)
           conn.commit()
           result_per_week = cursor.fetchall()


         except psycopg2.DatabaseError, e:
           return HttpResponse(e)
           if conn:
            conn.rollback()

      else:
         result_per_week = ''

      if result_per_week:
           res = json.dumps(result_per_week,default=json_util.default)


     else: 
      if german_string:
#         query = "SELECT id, req_url,view_func,record_id, effective_principal_email,datetime FROM indivo_audit WHERE (req_url LIKE '%reports%'  AND datetime >= '2017-08-31') AND ("+german_string+")"
         
         query = "SELECT date_trunc('week', datetime) AS "+'"'+"Week"+'"'+" , count(view_func) ,view_func FROM indivo_audit WHERE (req_url LIKE '%reports/"+app+"%'  AND datetime >= '"+start_date+"' AND datetime <= '"+end_date+"')AND ("+german_string+")GROUP BY "+'"'+"Week"+'"'+", view_func ORDER BY "+'"'+"Week"+'"'
         
         cursor.execute(query)
         conn.commit()
	 try:

           cursor.execute(query)
           conn.commit()
           result_per_week = cursor.fetchall()


         except psycopg2.DatabaseError, e:
           return HttpResponse(e)
           if conn:
            conn.rollback()


      else:
          result_per_week = '' 


     if result_per_week:
           res = json.dumps(result_per_week,default=json_util.default)

    if pilot == 'italian_pilot':

     try:

          cursor.execute("SELECT contact_email FROM indivo_account WHERE pilot= 'italian pilot'")
          conn.commit()
          accounts_emails = cursor.fetchall()


     except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()




     try:

          cursor.execute("SELECT account_id FROM indivo_account WHERE pilot= 'italian pilot'")
          conn.commit()
          accounts_ids = cursor.fetchall()


     except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()
     for ids in accounts_ids:

         try:

           cursor.execute("SELECT username FROM indivo_accountauthsystem WHERE account_id= '"+ids[0]+"'")
           conn.commit()
           result_username = cursor.fetchall()

           accounts_emails = accounts_emails + result_username


         except psycopg2.DatabaseError, e:
           return HttpResponse(e)
         if conn:
            conn.rollback()

     li = [x[0] for x in accounts_emails]

     for i in li:
        if i in li[-1]:
           italian_string += " effective_principal_email = '"+i+"'"
           italian_string_apps +=" patient ='"+i+"'"
        else:
           italian_string+="effective_principal_email = '"+i+"' OR "
           italian_string_apps+="patient = '"+i+"' OR "


     if app == 'game' or app == 'game_for_adults' or app == 'myhealthavatar' or app == 'imanagemyhealth':
      if patient == "yes":
          result_per_week = []
          final_result_list2 = []
          if italian_string_apps:
             for i in li:
	         if '@' not in i:
			try:
		          query_username = "SELECT  account_id FROM public.indivo_accountauthsystem where username='"+str(i)+"'"
	                  cursor.execute(query_username)
        	          conn.commit()
                	  account_id = cursor.fetchall()

		          query_email = "SELECT contact_email FROM public.indivo_account where account_id='"+str(account_id[0][0])+"';"
		          cursor.execute(query_email)
                          conn.commit()
                          email = cursor.fetchall()
			  i = email[0][0]
        	        except psycopg2.DatabaseError, e:
		
                	        return HttpResponse(e)

 #        query = "SELECT id, req_url,view_func,record_id, effective_principal_email,datetime FROM indivo_audit WHERE (req_url LIKE '%reports%'  AND datetime >= '2017-08-31') AND ("+italian_string+")"
		 query_apps = "SELECT date_trunc('week', timestamp) AS"+ '"'+"Week"+'"'+" , count(app_name) ,app_name FROM indivo_auditlog WHERE (timestamp >= '"+start_date+"' AND timestamp <= '"+end_date+"' and app_name='"+app+"') AND ( patient ='"+str(i)+"') GROUP BY"+' "'+"Week"+'"'+", app_name ORDER BY"+ '"'+"Week"+'"'
	         
                 try:
                  cursor.execute(query_apps)
                  conn.commit()
                  result_list = cursor.fetchall()
                  final_result_list2 = result_list

                  demographics_query = 'SELECT role,"cancerDisease", "placeOfResidence", pilot FROM public.indivo_account where contact_email='+"'"+str(i)+"'"

                  cursor.execute(demographics_query)
                  demographics = cursor.fetchall()

		  age_query = 'SELECT  bday, gender  FROM public.indivo_demographics where email='+"'"+str(i)+"'"

                  cursor.execute(age_query)
                  age = cursor.fetchall()
                  age = [list(row) for row in age]

                  demographics = [list(row) for row in demographics]
                  if demographics:
                          final_result_list2.append(demographics[0])

		  if age:
                          final_result_list2.append(age[0])
		  final_result_list = tuple(final_result_list2)
#                   return HttpResponse(app_title.split("/")[-2:])
                  result_per_week.append( final_result_list)

                 except psycopg2.DatabaseError, e:

                        return HttpResponse(e)
          else:
                result_per_week = ''

     


      else:
       if italian_string_apps:
#         query_apps = "SELECT * FROM indivo_auditlog WHERE timestamp >= '2017-08-31' AND ("+italian_string_apps+")"
         query_apps = "SELECT date_trunc('week', timestamp) AS"+ '"'+"Week"+'"'+" , count(app_name) ,app_name FROM indivo_auditlog WHERE (timestamp >= '"+start_date+"' AND timestamp <= '"+end_date+"' and app_name='"+app+"') AND ("+italian_string_apps+") GROUP BY"+' "'+"Week"+'"'+", app_name ORDER BY"+ '"'+"Week"+'"'

         try:

           cursor.execute(query_apps)
           conn.commit()
           result_per_week = cursor.fetchall()


         except psycopg2.DatabaseError, e:
            return HttpResponse(e)
            if conn:
             conn.rollback()

       else:
         result_per_week = ''

       if result_per_week:
           res = json.dumps(result_per_week,default=json_util.default)

     else:


      if patient == "yes":
          result_per_week = []
          final_result_list2 = []
	  if italian_string:
           
	     for i in li:
 #        query = "SELECT id, req_url,view_func,record_id, effective_principal_email,datetime FROM indivo_audit WHERE (req_url LIKE '%reports%'  AND datetime >= '2017-08-31') AND ("+italian_string+")"
	         query = "SELECT date_trunc('week', datetime) AS "+'"'+"Week"+'"'+" , count(view_func), effective_principal_email,req_url FROM indivo_audit WHERE (req_url LIKE '%reports/%'  AND datetime >= '"+start_date+"' AND datetime <= '"+end_date+"')AND ( effective_principal_email ='"+str(i)+"')GROUP BY "+'"'+"Week"+'"'+", view_func,effective_principal_email,req_url ORDER BY "+'"'+"Week"+'"'

        	 try:
	          cursor.execute(query)
        	  conn.commit()
                  result_list = cursor.fetchall()  
                  final_result_list2 = result_list

		  demographics_query = 'SELECT role,"cancerDisease", "placeOfResidence", pilot FROM public.indivo_account where contact_email='+"'"+str(i)+"'"

		  cursor.execute(demographics_query)
                  demographics = cursor.fetchall()


		  age_query = 'SELECT  bday, gender  FROM public.indivo_demographics where email='+"'"+str(i)+"'"

		  cursor.execute(age_query)
		  age = cursor.fetchall()
		  demographics = [list(row) for row in demographics]
		  final_result_list2 = [list(row) for row in final_result_list2]
		  age = [list(row) for row in age]

                  for i in range(len(final_result_list2)):
                    app_title = final_result_list2[i][3]
		    
		    final_result_list2[i][3] = app_title.split("/")[-2:][0]
                    final_result_list2[i][2] = app_title.split("/")[-4:][0]
                  if demographics:
			  final_result_list2.append(demographics[0])
                  if age:
			  final_result_list2.append(age[0])
                  final_result_list = tuple(final_result_list2)


#		    return HttpResponse(app_title.split("/")[-2:])
	          result_per_week.append( final_result_list)

        	 except psycopg2.DatabaseError, e:

            		return HttpResponse(e)
          else:
          	result_per_week = ''

      else:
        if italian_string:
 #        query = "SELECT id, req_url,view_func,record_id, effective_principal_email,datetime FROM indivo_audit WHERE (req_url LIKE '%reports%'  AND datetime >= '2017-08-31') AND ("+italian_string+")"
          query = "SELECT date_trunc('week', datetime) AS "+'"'+"Week"+'"'+" , count(view_func) ,view_func FROM indivo_audit WHERE (req_url LIKE '%reports/"+app+"%'  AND datetime >= '"+start_date+"' AND datetime <= '"+end_date+"')AND ("+italian_string+")GROUP BY "+'"'+"Week"+'"'+", view_func ORDER BY "+'"'+"Week"+'"'

          try:
           cursor.execute(query)
           conn.commit()
           result_per_week = cursor.fetchall()

          except psycopg2.DatabaseError, e:

            return HttpResponse(e)
        else:
          result_per_week = ''

     if result_per_week:
      res = json.dumps(result_per_week,default = myconverter)
#      res = json.dumps(result_per_week,default=json_util.default)

    return HttpResponse(res)
		

def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

def admin_console(request):

     params = {}
     try:
          conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'");
          conn.set_isolation_level(0)
          conn.commit()
          cursor = conn.cursor()

     except psycopg2.DatabaseError, e:

           print 'Error %s' % e

     try:

          cursor.execute("SELECT * FROM indivo_account")
          conn.commit()
          result = cursor.fetchall()


     except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()
     res = json.dumps(result,default=json_util.default)

     try:

          cursor.execute('SELECT app_module, event_name, event_parameters,'+'"'+'timestamp'+'"'+', app_name, country, patient FROM indivo_auditlog where flag=0 ORDER BY timestamp DESC;')
          conn.commit()
          audit = cursor.fetchall()


     except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()
     auditlog = json.dumps(audit,default=json_util.default)
     #surl_credentials = client.get_surl_credentials()
     return utils.render_template('ui/admin_console', {'accounts':res,'auditlog':auditlog})


def send_all(request):

    params = {}
    api = get_api()
    message_id = str(uuid.uuid4())
    subject =''
    subject = request.POST['subject']
    message = ''
    message =request.POST['message']
    try:
          conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'");
#          conn.autocommit = True
          conn.set_isolation_level(0)
          conn.commit()
          cursor = conn.cursor()

    except psycopg2.DatabaseError, e:

           print 'Error %s' % e

    try:

          cursor.execute("SELECT contact_email FROM indivo_account")
          conn.commit()
          result = cursor.fetchall()


    except psycopg2.DatabaseError, e:
         return HttpResponse(e)
         if conn:
            conn.rollback()
    res = json.dumps(result,default=json_util.default)

    for i in result:

         resp, content = api.account_send_message(account_email=i[0],message_id=message_id,body={'subject':subject, 'body':message, 'num_attachments':'1', 'body_type': 'markdown'})
    message = 'Failed'
    if '200' == resp['status']:
           message = 'Success'
    return utils.render_template('ui/send_all_replay',{'message':message})

def register_admin(request):
    if HTTP_METHOD_POST == request.method:
      post = request.POST
      user_hash = {'account_id': post.get('account_id'),
                 'contact_email': post.get('account_id'),        # TODO:the contact_email key is not present in the register form for now, so use the account_id
                     'full_name': post.get('full_name'),
              'primary_secret_p': 0,#set_primary,
            'secondary_secret_p': 0,}#settings.REGISTRATION.get('set_secondary_secret', 1)}
      api = get_api()
      res, content = api.account_create(body=user_hash)

      if '200' == res['status']:
                message = 'You are successfully registered.'

      else:
                return utils.render_template('ui/register_admin', {'ERROR': ErrorStr((content or 'Setup failed')), 'SETTINGS': settings})

      username = post.get('username', '').lower().strip()
      password = post.get('pw1')
      account_id = post.get('account_id')
      params = {'ACCOUNT_ID': account_id, 'PRIMARY_SECRET': 0, 'SECONDARY_SECRET': 0, 'SETTINGS': settings}
      error = None
      if len(username) < 1:
            error = ErrorStr("Username too short")
      if len(password) < (settings.REGISTRATION['min_password_length'] or 8):
            error = ErrorStr("Password too short")
      elif password != post.get('pw2'):
            error = ErrorStr("Passwords do not match")
      if error is not None:
            params['ERROR'] = error
            return utils.render_template('ui/register_admin', params)

        # secrets are ok, passwords check out: Attach the login credentials to the account
      resp, content = api.account_authsystem_add(
            account_email = post.get('account_id'),
            body = {
                  'system': 'password',
                'username': username,
                'password': password
            })


      if '200' == resp['status']:
            resp,content =api.account_set_state(account_email=account_id,body={'state':'active'})
            if resp['status'] != '200':
             # TODO: handle errors
                raise Exception("Error%s"%content)
            try:
               conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
#               conn.autocommit = True
               conn.set_isolation_level(0)
               conn.commit()
               cursor = conn.cursor()

            except psycopg2.DatabaseError, e:
                raise Exception("Error%s"%e)

	    try:

                   cursor.execute( "UPDATE indivo_account SET role='admin' WHERE contact_email='"+account_id+"'" )
                   conn.commit()
            except psycopg2.DatabaseError, e:

                   if conn:
                      conn.rollback()

                   raise Exception('Error %s'%e)
      elif '400' == resp['status']:
            params['ERROR'] = ErrorStr('Username already taken')
            return utils.render_template('ui/register_admin', params)

      fullName =  post.get('full_name')
      email =  post.get('account_id'),
      if '200' == resp['status']:
            if fullName:
                full_name = fullName
                email = email
 #               if siop:
  #                siop = account['siop']
                #dateOfBirth = account['dateOfBirth']
                #sex = account['sex']
                try:
                    split_index = full_name.index(' ')
                    given_name = full_name[0:split_index]
                    family_name = full_name[split_index:]
                   
                except ValueError:
                    given_name = full_name
                    family_name = full_name
                   
                demographics = '''<Demographics xmlns="http://indivo.org/vocab/xml/documents#">
                                    <dateOfBirth>1939-11-15</dateOfBirth>
                                    <gender>female</gender>
                                    <email>%s</email>
                                    <Name>
                                        <familyName>%s</familyName>
                                        <givenName>%s</givenName>
                                    </Name>
                                    
                                </Demographics>''' % (email, family_name, given_name)
                res = _record_create(account_id, demographics)
                if 200 != res.status_code:
                    utils.log("account_init(): Error creating a record after initializing the account, failing silently. The error was: %s" % res.content)
            move_to_setup = True


      params['MESSAGE'] = _("Administrator user added successfully")
      return utils.render_template('ui/register_admin',params)

    return utils.render_template('ui/register_admin', {'SETTINGS': settings})


def change_password(request):
    """
    http://localhost/change_password
    """
    params = {}
    
    # POST: Try to set a new password
    if request.method == HTTP_METHOD_POST:
        account_id = request.POST.get('account_id')
        if account_id:
            params['ACCOUNT_ID'] = account_id
            
            # get old password
            old_password = request.POST.get('old_pw')
            
            # check new passwords
            pw1 = request.POST.get('pw1')
            if len(pw1) >= (settings.REGISTRATION['min_password_length'] or 8):
                pw2 = request.POST.get('pw2')
                if pw1 == pw2:
                    api = get_api(request)
                    resp, content = api.account_password_change(account_email=account_id, body={'old': old_password, 'new': pw1})
                    status = resp['status']
                    
                    # password was reset, log the user in
                    if '200' == status:
                        return HttpResponseRedirect('/login/changed')
                    elif '403' == status:
                        params['ERROR'] = ErrorStr('Wrong old password')
                    else:
                        params['ERROR'] = ErrorStr(content or 'Password change failed')
                else:
                    params['ERROR'] = ErrorStr('Passwords do not match')
            else:
                params['ERROR'] = ErrorStr('Password too short')
        else:
            params['ERROR'] = 'No account_id present'
    
    # GET: Show the form, if we are logged in
    else:
        token = request.session.get('oauth_token_set')
        if not token:
            login_url = "%s?return_url=%s" % (reverse(login), urllib.quote(request.get_full_path()))
            return HttpResponseRedirect(login_url)
        
        account_id = urllib.unquote(token.get('account_id') if token else '')
        params['ACCOUNT_ID'] = account_id
    
    return utils.render_template('ui/change_password', params)

def documentsDownload(request,record_id,document_id):
    IMC_TOKEN = request.META["HTTP_IMC_TOKEN"]
    headers={'IMC-TOKEN':IMC_TOKEN}
    url = 'https://www.iphr.care/api/records/'+record_id+'/documents/'+document_id
    r =requests.get(url,headers=headers,verify=False)
    if r.status_code == 200:
      path = settings.MEDIA_ROOT+'documents_app/'
      xmlStart = r.text.split('</Model>\n</Models>')

      result = r.text.split('"filename">')

      result2= result[1].split('</Field>')
      filename = str(result2[0])
      payload = open(path+filename,'rb')
      image_read=payload.read()
      encoded_string = base64.encodestring(image_read)
#    with open(path+filename, "rb") as file2:
#       encoded_string = base64.encodestring(file2.read())
#       data = file2.read()
#       encoded_string=data.encode("base64")

      xmlFinal = xmlStart[0] +'<Field name="file_base64">' + encoded_string + '</Field>\n</Model>\n</Models>'

      return HttpResponse(xmlFinal)
    else:
      return HttpResponse(r)





def alertAccountsEmail(request):
   projectTitle = request.POST['projectTitle']
   email = request.POST['email']
   uuid_r = request.POST['uuid_r']
   if uuid_r == '95f59b74-15fb-459f-a42b-5c464b3fd607':
    

         result = sendMail([email],'no-reply@www.iphr.care','Your cohort of patients has reached the apropriate criteria','We would like to inform you that the patients for your project with title '+projectTitle+' are ready in order to ask their sharing preferences. Pleace navigate to iMC portal in link https://www.iphr.care',[])

         api = get_api()
         message_id = str(uuid.uuid4())
         resp, content = api.account_send_message(account_email='testadministrator@email.com',message_id=message_id,body={'subject':'Your notification criteria have been met', 'body':'Patients for project '+projectTitle+' are ready in order to ask their sharing preferences', 'num_attachments':'1', 'body_type': 'markdown'})
         return HttpResponse('Success')
   return HttpResponse('Fail')

def alertAccounts(request): 
   #example gia to rest client record_id=04501688-f145-477b-b400-cdf1eeba8fe9,0967b6fc-d56d-4fdd-903f-62dce4d05af3,11c77bb0-e582-4538-9471-d8840c19dbba&project_title=test title&project_description=descr&researcher=resea&count=5
   project_title = request.POST['project_title']
   project_description = request.POST['project_description']   
   researcher =request.POST['researcher']
   count = request.POST['count']
   count_yes = 0
   count_no = 0
   count_pending = 0
   record_ids=request.POST['record_id']
   records_ids= record_ids.split(',')
   api = get_api()
   accounts_ids = []
   accounts_to_be_alerted = []
   records_to_be_alerted = []
   records_yes = ''
   for record in records_ids:

	  res, content = api.record_get_owner(record_id=record)
	  if res['status'] == '200':
	
	    root = ET.fromstring(content)
	    accounts_ids.append(root.attrib['id'])
   number = 0
   for account in accounts_ids:

		  resp, content = api.account_info(account_email=account)
	  	  root_ = ET.fromstring(content)
		  for node in root_.findall('.//sharingPreferences'):
                   if node.text:
        	     if (node.text).strip().lower() != 'yes' and (node.text).strip().lower() != 'no':
	        	 accounts_to_be_alerted.append(account)
                         records_to_be_alerted.append(records_ids[number])
	                 count_pending = count_pending+1
        	     if (node.text).strip().lower() == 'yes':
                	 count_yes = count_yes +1
                         records_yes += records_ids[number]
			 records_yes +=","      
	             if (node.text).strip().lower() == 'no':
        	         count_no = count_no+1
		  number +=1

   finalcount = int(count)-int(count_yes)

#   if finalcount:

   try:
               conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
#               conn.autocommit = True
               conn.set_isolation_level(0)
               conn.commit()
               cursor = conn.cursor()

   except psycopg2.DatabaseError, e:
                   existing_account_i="Cannot connect to db"
  
   try:

                   cursor.execute( "Select id from public.indivo_researchproject where projecttitle='"+project_title+"';" )
                   conn.commit()
                   res = cursor.fetchall()
                   if res:


			 try:

	                   cursor.execute( " delete from public.indivo_researchproject where id='"+str(res[0][0])+"';" )
        	           conn.commit()
			 except psycopg2.DatabaseError, e:
	                    return HttpResponse(e)
   

   except psycopg2.DatabaseError, e:
                    return HttpResponse(e)
    
   try:

                   cursor.execute( "INSERT INTO indivo_researchproject(researcher, researchdescription, projecttitle,count,completed,records)  VALUES ('"+researcher+"', '"+project_description+"', '"+project_title+"','"+str(finalcount)+"','false','"+str(records_yes[:-1])+"')RETURNING id" )
                   conn.commit() 
                   res = cursor.fetchone()
		   ret_id = res[0]

   except psycopg2.DatabaseError, e:
                    return HttpResponse(e)


   iterator = 0
   for acc in accounts_to_be_alerted:
	try:

                   cursor.execute("INSERT INTO indivo_accountsharing(projectid, accountid, answer,recordid) VALUES ('"+str(ret_id)+"', '"+acc+"', 'pending','"+str(records_to_be_alerted[iterator])+"');") 
                   conn.commit()

        except psycopg2.DatabaseError, e:
		    return HttpResponse(e)
        iterator +=1
   
   json_count = '[{"yes": "'+str(records_yes[:-1])+'"},{"no":'+str(count_no)+'},{"dontknow":'+str(count_pending)+'}]'
   return HttpResponse(json_count)
   #return HttpResponse('Completed')

def alert_index_account(request):


   try:
               conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
#               conn.autocommit = True
               conn.set_isolation_level(0)
               conn.commit()
               cursor = conn.cursor()

   except psycopg2.DatabaseError, e:
                   existing_account_i="Cannot connect to db"

   try:

                   cursor.execute("SELECT projectid, accountid from indivo_accountsharing where answer='pending';") 
                   conn.commit()
                   result = cursor.fetchall()
                  # result[0] = result[0] +('test',)
		   #return HttpResponse(result)

   except psycopg2.DatabaseError, e:
                    return HttpResponse(e)

   newresult=[]

   if result:
       for res in result:
           tempres=res
           try:

                   cursor.execute("SELECT researcher, researchdescription, projecttitle FROM indivo_researchproject where id='"+str(res[0])+"';")
                   conn.commit()
                   resu = cursor.fetchall()
                   for r in resu:
                      for n in r: 
                       tempres = tempres + (str(n),)
                   

           except psycopg2.DatabaseError, e:
                    return HttpResponse(e)
           newresult.append(list(tempres))
       finalresult=json.dumps(newresult)
       return HttpResponse(finalresult)
   return HttpResponse('Error')

def update_account_answer(request):
        account_id = request.POST['account_id']
        project_id = request.POST['project_id']
        answer = request.POST['answer']
	try:
               conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
#               conn.autocommit = True
               conn.set_isolation_level(0)
               conn.commit()
               cursor = conn.cursor()

        except psycopg2.DatabaseError, e:
                   return HttpResponse(e)

        try:

                   cursor.execute("UPDATE indivo_accountsharing SET  answer='"+answer+"' WHERE projectid='"+project_id+"' and accountid='"+account_id+"';")
                   conn.commit()

        except psycopg2.DatabaseError, e:
                    return HttpResponse(e)
        return HttpResponse('Success')




def check_saf_researcher(request):

   record_id=request.GET.get('record_id')
   api = get_api()
   res, content = api.record_get_owner(record_id=record_id)
   if res['status'] == '200':

     root = ET.fromstring(content)
     researcher_email = (root.attrib['id'])

    
     try:
               conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
#               conn.autocommit = True
               conn.set_isolation_level(0)
               conn.commit()
               cursor = conn.cursor()

     except psycopg2.DatabaseError, e:
                   existing_account_i="Cannot connect to db"
     try:

                   cursor.execute("SELECT completed FROM indivo_researchproject where researcher='"+researcher_email+"'");
                   conn.commit()
                   res = cursor.fetchall()

     except psycopg2.DatabaseError, e:
                    return HttpResponse(e)
     if res:
	if len(res)==1:
		return HttpResponse(res[0])
        else:

	    for r in res:
	
		if r[0] == 'true':	
		    return HttpResponse('true')

   return HttpResponse('false')

def check_research_project(request):
    
    try:
               conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
#               conn.autocommit = True
               conn.set_isolation_level(0)
               conn.commit()
               cursor = conn.cursor()

    except psycopg2.DatabaseError, e:
                   existing_account_i="Cannot connect to db"
    try:

                   cursor.execute("SELECT id,count FROM indivo_researchproject where completed='false'"); 
                   conn.commit()
                   res = cursor.fetchall()

    except psycopg2.DatabaseError, e:
                    return HttpResponse(e)

    records_yes=''
    if res:
      for r in res:


        total = 0;
        try:

                   cursor.execute("SELECT answer,recordid FROM indivo_accountsharing where projectid='"+str(r[0])+"'");
                   conn.commit()
                   result = cursor.fetchall()

        except psycopg2.DatabaseError, e:
                    return HttpResponse(e)
	if result:

         for resu in result:
	   
           if str(resu[0]) == 'yes':
	      records_yes += str(resu[1])
              records_yes += ','
              total = total+1
     	       
         if int(total) >= int(r[1]):
  
		
           try:

                   cursor.execute("SELECT researcher, projecttitle,records FROM indivo_researchproject where id='"+str(r[0])+"';");
                   conn.commit()
                   resul = cursor.fetchall()
		   sendMail([str(resul[0][0])],'no-reply@www.iphr.care','Your cohort of patients has reached the apropriate criteria','We would like to inform you that the patients for your project with title '+str(resul[0][1])+' are ready. Pleace navigate to iMC portal in link https://www.iphr.care',[])
                   api = get_api()
                   message_id = str(uuid.uuid4())
                   resp, content = api.account_send_message(account_email='testadministrator@email.com',message_id=message_id,body={'subject':'Your cohort of patients has reached the apropriate criteria', 'body':'Patients for project "'+str(resul[0][1])+'" have all shared their infromation', 'num_attachments':'1', 'body_type': 'markdown'})
		   message_id = str(uuid.uuid4())
                  
                   resp, content = api.account_send_message(account_email=str(resul[0][0]),message_id=message_id,body={'subject':'Your cohort of patients has reached the apropriate criteria', 'body':'Patients for project "'+str(resul[0][1])+'" have all shared their infromation', 'num_attachments':'1', 'body_type': 'markdown'})

                   msg = MIMEMultipart()
	           msg['From'] = 'no-reply@www.iphr.care'
                   msg['To'] = str(resul[0][0])
	           msg['Date'] = formatdate(localtime=True)
	           msg['Subject'] = 'Your cohort of patients has reached the apropriate criteria'
 	           msg.attach( MIMEText('Your cohort of patients has reached the apropriate criteria','We would like to inform you that the patients for your project with title '+str(resul[0][1])+' are ready. Pleace navigate to iMC portal in link https://www.iphr.care') )
 	           smtp = smtplib.SMTP("localhost")
                   smtp.sendmail('no-reply@www.iphr.care', str(resul[0][0]), msg.as_string() )
                   record_ids = str(resul[0][2])+','+records_yes
                   data = {'query':str(resul[0][1]),'record_ids':record_ids[:-1]}
                  
	           url = 'https://www.iphr.care/forth/saf/autoanonymize.php'
		   return_value = requests.post(url = url, data = data)

           except psycopg2.DatabaseError, e:
                    return HttpResponse(e)

	   try:

                   cursor.execute("UPDATE indivo_researchproject SET completed='true' WHERE id='"+str(r[0])+"';");
                   conn.commit()

           except psycopg2.DatabaseError, e:
                    return HttpResponse(e)

    # prepei na stalthei ena email ston researcher oti einai etoimo	      
     
    return HttpResponse('Completed')    
 

def enableapps(request,record_id):


	role =request.GET.get('role')

	record_id = request.GET.get('record_id') 


	try:
	       conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
	#               conn.autocommit = True
	       conn.set_isolation_level(0)
	       conn.commit()
	       cursor = conn.cursor()

	except psycopg2.DatabaseError, e:
		   existing_account_i="Cannot connect to db"


	try:
		   cursor.execute( "SELECT enabled FROM indivo_record where id='"+record_id+"'" )
		   conn.commit()
		   enabled = cursor.fetchall()

	except psycopg2.DatabaseError, e:
		return HttpResponse(e)


        return_value='not_updated'


	if (str(enabled[0][0])).lower() == ('FALSE').lower():
		url = 'https://www.iphr.care:443/oauth2/access_token'
		r = requests.post(url,data='client_id=38525ae9102bb34a72ab&client_secret=c4ca8bd3eb7109718380104b1b5bcab9fd45c267&grant_type=password&username=jsmith&password=password.example',verify=True)

		data = json.loads(r.text)
		token_resul=data['access_token']


		headersAdmin={'IMC-TOKEN':str(token_resul),'ADMIN':''}
	#	record_id=str(sys.argv[1])

		#headersAdmin={'IMC-TOKEN':'1d430b8a8da9c50a6dbd','ADMIN':''}
	     

		if role=='patient':

                        url='https://www.iphr.care/api/records/'+record_id+'/apps/allergies@apps.indivo.org/setup'

                        r=requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/problems@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/medications@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/contact@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/psycho-emotional-questionnaires@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/documentsupload@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/measurements@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/labs@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/semanticSearch@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/appointments@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/procedures@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/psyche@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/otherapps@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/algac@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/decisionaid@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/fare@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/mystatistics@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/pdq@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/forum@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)


		if role=='doctor':
			url='https://www.iphr.care/api/records/'+record_id+'/apps/profiler@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/clinicianquestions@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/decisionaid@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)

			url='https://www.iphr.care/api/records/'+record_id+'/apps/semanticManagement@apps.indivo.org/setup'
			r = requests.post(url,headers=headersAdmin,verify=True)
                try:
                   cursor.execute( "UPDATE indivo_record SET enabled='TRUE' WHERE id='"+record_id+"'" )
                   conn.commit()
                   return_value = 'updated' 

                except psycopg2.DatabaseError, e:
                    return HttpResponse(e)



 #  import subprocess
 #  stri=str("python /media/data/hatzimin/web/enableapps.py "+record_id)
 #  r=subprocess.call(stri, shell=True)
        return HttpResponse(return_value)




def documentsUpload(request,record_id):
 
   missing_padding = len(request.FILES['file']) % 4
   logging.debug("fileUpload missing_padding: %s",str(missing_padding))
   if missing_padding != 0:
        data =str(request.FILES['file'])

        #file1= base64.urlsafe_b64decode(data + '=' * (4 - len(data) % 4))   # GIA TO ERROR TOU MISSING PADDING AUTOS O KWDIKAS

#        file2 = base64.b64encode(file2.encode('utf8'))
        file = request.FILES['file']
        image_read = file.read()
        file_64 = base64.encodestring(image_read)


        file2 = image_read

#        file_base64 = base64.b64encode(file2)


#        file2 = base64.b64encode(file2.decode('utf8'))
        #file2 = file.encode('utf-8').strip()
#        file2 = file.read(1)
   else:
        file = request.FILES['file']
        image_read = file.read()

        file_64 = base64.encodestring(image_read)
        file2 = image_read
       # file2 = file.read(1)
        #file2 = file1.encode('utf-8').strip()


   #logging.debug("fileUpload file: %s",str(file))
   IMC_TOKEN = request.META["HTTP_IMC_TOKEN"]
   logging.debug("upload file inside")
   logging.debug("fileUpload imc token: %s",str(IMC_TOKEN))
   title = request.POST['title']
#   registered_date=request.POST['registered_date']
   file_set_id=request.POST['file_set_id']
   type_of_file=request.POST['type_of_file']
   file_id=request.POST['file_id']
   organisation=request.POST['organisation']
   doctor=request.POST['doctor']
   diagnosis=request.POST['diagnosis']
   reasons=request.POST['reasons']
   comments=request.POST['comments']
   logging.debug("fileUpload title: %s",str(title))
   headers={'IMC-TOKEN':IMC_TOKEN}
 
   r = ''
   if file2:
#   if file:
            file.seek(0)
            extention = file.name.split('.')[-1]

            filename=str(uuid.uuid4())
            today = datetime.date.today()
            ts = time.time()
            registered_date = ''
            registered_date = request.POST['registered_date']
            if registered_date == '':
                registered_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')
            data='<?xml version="1.0" encoding="utf-8" ?><Models xmlns="http://indivo.org/vocab/xml/documents#"><Model name="Filedocument"><Field name="title">'+title+'</Field> <Field name="registered_date">'+registered_date+'</Field><Field name="filename">'+filename+'.'+extention+'</Field><Field name="file_set_id">'+file_set_id+'</Field><Field name="type_of_file">'+type_of_file+'</Field><Field name="file_id">'+file_id+'</Field><Field name="organisation">'+organisation+'</Field><Field name="doctor">'+doctor+'</Field><Field name="diagnosis">'+diagnosis+'</Field><Field name="reasons">'+reasons+'</Field><Field name="comments">'+comments+'</Field><Field name="file_base64">'+file_64+'</Field></Model></Models>'


            r = requests.post('https://www.iphr.care/api/records/'+record_id+'/documents/', data=data,verify=True, headers=headers)
            if r.status_code == 200:
             #request.FILES['docfile'].name
               path = default_storage.save(settings.MEDIA_ROOT+'/documents_app/'+str(filename)+'.'+extention, ContentFile(file.read()))
               tmp_file = os.path.join(settings.MEDIA_ROOT, path)
               mime = magic.Magic(mime=True)
               m = magic.from_file(tmp_file)
               #m=magic.open(magic.MAGIC_MIME)
               #m.load()
               #test=(m.file(settings.MEDIA_ROOT+'/documents_app/'+str(filename)+'.'+extention))
               test_file = open(settings.MEDIA_ROOT+'/documents_app/'+str(filename)+'.'+extention,'rb')


            else:
                return HttpResponse(r.text) 
   if r != '':
      return HttpResponse(r)
   else:
      return HttpResponse('File is empty')



def exportRDFServer(request):
    try:
       username=request.POST['username']
    except Exception:
        username= None
    try:
       password=request.POST['password']
    except Exception:
       password= None
    try:
       email=request.POST['email']
    except Exception:
        email= None
    #s = requests.Session()
    argList = []
    argList.append(username)

    argList.append(password)

    argList = []
    argList.append(username)

    argList.append(password)
    argList.append(email)
    os.system('python /media/data/hatzimin/web/indivo_ui_server/ui/connectAvatarRdf.py %s' % ' '.join(argList))
    with open ("/media/data/hatzimin/avatarResults/"+email+".txt", "r") as myfile:
       data=myfile.read().replace('\n', '')
    return HttpResponse(data)


def terms(request):
    if HTTP_METHOD_POST == request.method:
        if not settings.REGISTRATION.get('enable', False):
            return utils.render_template('ui/error', {'error_message': ErrorStr('Registration disabled'), 'error_status': 403})

        # create the account
        post = request.POST
        set_primary = settings.REGISTRATION.get('set_primary_secret', 1)
        user_hash = {'account_id': post.get('account_id'),
                 'contact_email': post.get('account_id'),        # TODO:the contact_email key is not present in the register form for now, so use the account_id
                     'full_name': post.get('full_name'),
              'primary_secret_p': set_primary,
            'secondary_secret_p': settings.REGISTRATION.get('set_secondary_secret', 1)}
        api = get_api()


        res, content = api.account_create(body=user_hash)


        # on success, forward to page according to the secrets that were or were not generated
        if '200' == res['status']:
            account_xml = content or '<root/>'
            account = utils.parse_account_xml(account_xml)
            account_id = account.get('id')
            if not set_primary:
                return utils.render_template(LOGIN_PAGE, {'MESSAGE': _('You have successfully registered.') + ' ' + _('After an administrator has approved your account you may login.'), 'SETTINGS': settings})

            # display the secondary secret if there is one
            has_secondary_secret = (None != account.get('secret') and len(account.get('secret')) > 0)
            
           
            return HttpResponseRedirect('/accounts/%s/send_secret/sent' % account_id)
        return utils.render_template('ui/terms', {'ERROR': ErrorStr((content or 'Setup failed')), 'SETTINGS': settings})
    return utils.render_template('ui/terms', {'SETTINGS': settings})


def user_manual(request):
    return utils.render_template('ui/user_manual',{'SETTINGS': settings})

def terms_settings(request):
    return utils.render_template('ui/terms_settings',{'SETTINGS': settings})


def register(request):
    """
    http://localhost/change_password
    Returns the register template (GET) or creates a new account (POST)
    """
    if HTTP_METHOD_POST == request.method:
        if not settings.REGISTRATION.get('enable', False):
            return utils.render_template('ui/error', {'error_message': ErrorStr('Registration disabled'), 'error_status': 403})
        
        # create the account
        post = request.POST
	full_name= post.get('full_name').encode('ascii', 'xmlcharrefreplace')
        set_primary = settings.REGISTRATION.get('set_primary_secret', 1)
        user_hash = {'account_id': post.get('account_id'),
                 'contact_email': post.get('account_id'),        # TODO:the contact_email key is not present in the register form for now, so use the account_id
                     'full_name': full_name,
                     'sharingPreferences': post.get('sharingPreferences'),
		     'role': post.get('role'),
                     'cancerDisease': post.get('cancerDisease'),
                     'placeOfResidence': post.get('placeOfResidence'),
                     'speciality':post.get('speciality'),
                     'pilot':post.get('pilot'),
                     'health_organisation':post.get('health_organisation'),
                     'address_organisation':post.get('address_organisation'),
              'primary_secret_p': set_primary,
            'secondary_secret_p': settings.REGISTRATION.get('set_secondary_secret', 1)}
        api = get_api()
       
        
        res, content = api.account_create(body=user_hash)

        
        # on success, forward to page according to the secrets that were or were not generated
        if '200' == res['status']:
            account_xml = content or '<root/>'
            account = utils.parse_account_xml(account_xml)
            account_id = account.get('id')
            if not set_primary:
                return utils.render_template(LOGIN_PAGE, {'MESSAGE': _('You have successfully registered.') + ' ' + _('After an administrator has approved your account you may login.'), 'SETTINGS': settings})
            
            # display the secondary secret if there is one
            has_secondary_secret = (None != account.get('secret') and len(account.get('secret')) > 0)
            if has_secondary_secret:
                return utils.render_template('ui/register', {'SETTINGS': settings, 'ACCOUNT_ID': account_id, 'SECONDARY': account.get('secret'), 'MESSAGE': _('You have successfully registered.') + ' ' + _('At the link sent to your email address, enter the following confirmation code:')})
            return HttpResponseRedirect('/accounts/%s/send_secret/sent' % account_id)
        return utils.render_template('ui/register', {'ERROR': ErrorStr((content or 'Setup failed')), 'SETTINGS': settings})
    return utils.render_template('ui/register', {'SETTINGS': settings})


def send_secret(request, account_id, status):
    """
    http://localhost/accounts/[foo@bar.com/]send_secret/[(sent|wrong)]
    """
    params = {'ACCOUNT_ID': account_id}
    
    if HTTP_METHOD_GET == request.method:
        if account_id:
            if 'wrong' == status:
                params['ERROR'] = ErrorStr('Wrong secret')
            elif 'sent' == status:
                params['MESSAGE'] = _('Use the link sent to your email address to proceed with account activation')
    
    elif HTTP_METHOD_POST == request.method:
        account_id = request.POST.get('account_id', '')
        params['ACCOUNT_ID'] = account_id
        
        # re-send the primary secret and display the secondary, if needed
        if request.POST.get('re_send', False):
            api = get_api()
            resp, content = api.account_resend_secret(account_email=account_id)
            
            if '404' == resp['status']:
                params['ERROR'] = ErrorStr('Unknown account')
            elif '200' != resp['status']:
                params['ERROR'] = ErrorStr(content or 'Error')
            
            # re-sent the primary, display a secondary if there is one
            else:
                params['MESSAGE'] = _('The activation email has been sent')
                
                resp, content = api.account_info(account_email=account_id)
                status = resp['status']
                if '404' == status:
                    params['ERROR'] = ErrorStr('Unknown account')
                elif '200' != status:
                    params['ERROR'] = ErrorStr(resp.response.get('response_data', 'Server Error'))
                else:
                    account_xml = content or '<root/>'
                    account = utils.parse_account_xml(account_xml)
                    has_secondary_secret = (None != account.get('secret') and len(account.get('secret')) > 0)
                    if has_secondary_secret:
                        params['MESSAGE'] += '. ' + ('At the link sent to your email address, enter the following confirmation code:')
                        params['SECONDARY'] = account.get('secret')
        else:
            params['MESSAGE'] = _('Use the link sent to your email address to proceed with account activation')
    
    return utils.render_template('ui/send_secret', params)


def account_init(request, account_id, primary_secret):
    """
    http://localhost/accounts/foo@bar.com/init/icmloNHxQrnCQKNn
    Legacy: http://localhost/indivoapi/accounts/foo@bar.com/initialize/icmloNHxQrnCQKNn
    """
    api = get_api()
    try_to_init = False
    move_to_setup = False
    
    # is this account already initialized?
    resp, content = api.account_info(account_email=account_id)
    status = resp['status']
    if '404' == status:
        return utils.render_template(LOGIN_PAGE, {'ERROR': ErrorStr('Unknown account')})
    if '200' != status:
        return utils.render_template('ui/error', {'error_status': status, 'error_message': ErrorStr(content or 'Server Error')})
    
    account_xml = content or '<root/>'
    account = utils.parse_account_xml(account_xml)
    account_state = account.get('state')
    account_is_uninitialized = ('uninitialized' == account_state)		# TODO: Rewrite server to not set uninitialized upon password reset
    has_auth_system = (len(account.get('auth_systems', [])) > 0)		# TODO: Try to avoid upon account-init rewrite
    has_primary_secret = (len(primary_secret) > 0)      				# TODO: Get this information from the server (API missing as of now)
    secondary_secret = ''
    has_secondary_secret = (None != account.get('secret') and len(account.get('secret')) > 0)
    can_autocreate_record = True if 'uninitialized' == account_state else False     # TODO: Better: check whether the account has no records
    
    # if the account is already active, show login IF at least one auth-system is attached
    if not account_is_uninitialized:
        if 'active' == account_state:
            if has_auth_system:
                return utils.render_template(LOGIN_PAGE, {'MESSAGE': _('Your account is now active, you may log in below'), 'SETTINGS': settings})
            else:
                move_to_setup = True
        else:
            return utils.render_template(LOGIN_PAGE, {'ERROR': ErrorStr('This account is %s' % account_state), 'SETTINGS': settings})
    
    # bail out if the primary secret is wrong
    if has_primary_secret:
        resp, content = api.account_check_secrets(account_email=account_id, primary_secret=primary_secret)
        if '200' != resp['status']:
            return HttpResponseRedirect('/accounts/%s/send_secret/wrong' % account_id)
    
    # GET the form; if we don't need a secondary secret, continue to the 2nd step automatically
    if HTTP_METHOD_GET == request.method:
        if not has_secondary_secret:
            try_to_init = True
    
    # POSTed the secondary secret
    if HTTP_METHOD_POST == request.method:
        secondary_secret = request.POST.get('conf1') + request.POST.get('conf2')
        try_to_init = True
    
    # try to initialize
    if try_to_init and not move_to_setup:
        data = {}
        if has_secondary_secret:
            data = {'secondary_secret': secondary_secret}
        resp, content = api.account_initialize(account_email = account_id,
                                 primary_secret = primary_secret,
                                           body = data)
        status = resp['status']
        siop='' 
        # on success also create the first record if we have a full_name and is enabled in settings
        if '200' == status:
            if can_autocreate_record and settings.REGISTRATION['autocreate_record'] and account.has_key('fullName') and len(account['fullName']) > 0:
                full_name = account['fullName']
                email = account['contactEmail']
 #               if siop:
  #                siop = account['siop']
                #dateOfBirth = account['dateOfBirth']
                #sex = account['sex']
                try:
                    split_index = full_name.index(' ')
                    given_name = full_name[0:split_index]
                    family_name = full_name[split_index:]
                    siop = siop
                except ValueError:
                    given_name = full_name
                    family_name = full_name
                    siop = siop
                demographics = '''<Demographics xmlns="http://indivo.org/vocab/xml/documents#">
                                    <dateOfBirth>1939-11-15</dateOfBirth>
                                    <gender>female</gender>
                                    <email>%s</email>
                                    <Name>
                                        <familyName>%s</familyName>
                                        <givenName>%s</givenName>
                                    </Name>
                                    <siop>%s</siop>
                                </Demographics>''' % (email, family_name, given_name,siop)
                res = _record_create(account_id, demographics)
                if 200 != res.status_code:
                    utils.log("account_init(): Error creating a record after initializing the account, failing silently. The error was: %s" % res.content)
            move_to_setup = True
        elif '404' == status:
            return utils.render_template(LOGIN_PAGE, {'ERROR': ErrorStr('Unknown account')})
        elif '403' == status:
            return utils.render_template('ui/account_init', {'ACCOUNT_ID': account_id, 'PRIMARY_SECRET': primary_secret, 'ERROR': ErrorStr('Wrong confirmation code')})
        else:
            utils.log("account_init(): Error initializing an account: %s" % content)
            return utils.render_template('ui/account_init', {'ACCOUNT_ID': account_id, 'PRIMARY_SECRET': primary_secret, 'ERROR': ErrorStr('Setup failed')})
    
    # proceed to setup if we have the correct secondary secret
    params = {'ACCOUNT_ID': account_id, 'PRIMARY_SECRET': primary_secret, 'SETTINGS': settings}
    if move_to_setup and (not has_secondary_secret or len(secondary_secret) > 0):
        resp, content = api.account_check_secrets(account_email=account_id, primary_secret=primary_secret, body={'secondary_secret': secondary_secret})
        status = resp['status']
        if '200' == status:
            return HttpResponseRedirect('/accounts/%s/setup/%s/%s' % (account_id, primary_secret, secondary_secret))
        if '403' == status:
            params['ERROR'] = ErrorStr('Wrong confirmation code')
        else:
            params['ERROR'] = content or 'Server Error'
    return utils.render_template('ui/account_init', params)


def account_setup(request, account_id, primary_secret, secondary_secret):
    """
    http://localhost/accounts/foo@bar.com/setup/taOFzInlYlDKLbiM
    """
    api = get_api()
    
    # is this account already initialized?
    resp, content = api.account_info(account_email=account_id)
    status = resp['status']
    if '404' == status:
        return utils.render_template(LOGIN_PAGE, {'ERROR': ErrorStr('Unknown account')})
    if '200' != status:
        return utils.render_template('ui/error', {'error_status': status, 'error_message': ErrorStr(content or 'Server Error')})
    
    account_xml = content or '<root/>'
    account = utils.parse_account_xml(account_xml)
    account_state = account.get('state')
    has_primary_secret = (len(primary_secret) > 0)      # TODO: Get this information from the server (API missing as of now)
    has_secondary_secret = (None != account.get('secret') and len(account.get('secret')) > 0)
    
    # if the account is already active, show login IF at least one auth-system is attached
    if 'active' == account_state:
        if len(account['auth_systems']) > 0:
            return utils.render_template(LOGIN_PAGE, {'MESSAGE': _('Your account is now active, you may log in below'), 'SETTINGS': settings})
    elif 'uninitialized' != account_state:
        return utils.render_template(LOGIN_PAGE, {'ERROR': ErrorStr('This account is %s' % account_state), 'SETTINGS': settings})
    
    # received POST data, try to setup
    params = {'ACCOUNT_ID': account_id, 'PRIMARY_SECRET': primary_secret, 'SECONDARY_SECRET': secondary_secret, 'SETTINGS': settings}
    if HTTP_METHOD_POST == request.method:
        post = request.POST
        username = post.get('username', '').lower().strip()
        password = post.get('pw1')
        secondary_secret = post.get('secondary_secret', '')
        
        # verify PRIMARY secret first and send back to "resend secret" page if it is wrong
        resp, content = api.account_check_secrets(account_email=account_id, primary_secret=primary_secret)
        if '200' != resp['status']:
            return HttpResponseRedirect('/accounts/%s/send_secret/wrong' % account_id)
        else:
            argList = []
            argList.append(username)
            account_id = account_id
            argList.append(password)
            argList.append(account_id)
            os.system('python /media/data/hatzimin/web/indivo_ui_server/ui/createUserOauth2.py %s' % ' '.join(argList))
    
        # verify SECONDARY secret as well, if there is one
        if has_secondary_secret:
            resp, content = api.account_check_secrets(account_email=account_id, primary_secret=primary_secret, body={'secondary_secret': secondary_secret})
            if '200' != resp['status']:
                params['ERROR'] = ErrorStr('Wrong confirmation code')
                return utils.render_template('ui/account_init', params)
        
        # verify passwords
        error = None
        if len(username) < 1:
            error = ErrorStr("Username too short")
        if len(password) < (settings.REGISTRATION['min_password_length'] or 8):
            error = ErrorStr("Password too short")
        elif password != post.get('pw2'):
            error = ErrorStr("Passwords do not match")
        if error is not None:
            params['ERROR'] = error
            return utils.render_template('ui/account_setup', params)
        
        # secrets are ok, passwords check out: Attach the login credentials to the account
        resp, content = api.account_authsystem_add(
            account_email = account_id,
            body = {
                  'system': 'password',
                'username': username,
                'password': password
            })
        
        if '200' == resp['status']:
            try:
               conn = psycopg2.connect("dbname='indivo' user='indivo' host='localhost' password='indivo'")
#               conn.autocommit = True
               conn.set_isolation_level(0)
               conn.commit()
               cursor = conn.cursor()

            except psycopg2.DatabaseError, e:
                   existing_account_i="Cannot connect to db"


            try:

                   cursor.execute( "SELECT account_id FROM indivo_account where contact_email='"+account_id+"'" )
                   conn.commit()
                   result = cursor.fetchall()

            except psycopg2.DatabaseError, e:
                   url=e
                   if conn:
                        conn.rollback()

                        print 'Error %s' % e
            if result:
             try:

                   cursor.execute( "SELECT id FROM indivo_record where owner_id='"+str(result[0][0])+"'" )
                   conn.commit()
                   result_rec = cursor.fetchall()

             except psycopg2.DatabaseError, e:
                   url=e
                   return HttpResponse(e)
                   if conn:
                        conn.rollback()

                        print 'Error %s' % e
          
            if result:
               url='https://www.iphr.care:8004/registration.php?username='+username+'&record='+str(result_rec[0][0]) #forum 
               r = requests.post(url)

            # everything's OK, log this person in, hard redirect to change location
            resp, content = tokens_get_from_server(request, username, password)
            if resp['status'] != '200':
                return utils.render_template(LOGIN_PAGE, {'ERROR': ErrorStr(e.strerror), 'RETURN_URL': request.POST.get('return_url', '/'), 'SETTINGS': settings})
            return HttpResponseRedirect('/')
        elif '400' == resp['status']:
            params['ERROR'] = ErrorStr('Username already taken')
            return utils.render_template('ui/account_setup', params)
        params['ERROR'] = ErrorStr('account_init_error')
        return utils.render_template('ui/account_setup', params)
    
    # got no secondary_secret, go back to init step which will show a prompt for the secondary secret
    if has_secondary_secret and not secondary_secret:
        return HttpResponseRedirect('/accounts/%s/init/%s' % (account_id, primary_secret))
    return utils.render_template('ui/account_setup', params)


def forgot_password(request):
    """
    http://localhost/forgot_password
    """
    params = {'SETTINGS': settings}
    
    if request.method == HTTP_METHOD_POST:
        email = request.POST.get('account_id')
        #MERGE dev_landing did more secondary secret handling
        api = get_api()
        # get account id from email (which we are assuming is contact email)
        resp, content = api.account_forgot_password(account_email=email)
        status = resp['status']
        
        # password was reset, show secondary secret
        if '200' == status:
            e = ET.fromstring(content or '<root/>')
            if settings.PASSWORD_RESET_REQUIRE_SECONDARY:
               params['SECONDARY_SECRET'] = e.text
        
        # password was reset, show secondary secret if needed
        if '200' == status:
            params['EMAIL_SENT'] = True
            if settings.PASSWORD_RESET_REQUIRE_SECONDARY:
	
                e = ET.fromstring(content or '<root/>')
                if not e.text or 'None' == e.text:
                    utils.log('Password reset requires a secondary secret, but this account currently does not have one!')
                    # TODO: Tell the server to generate a secondary secret!
                    # If you arrive here, account generation was not setup properly because it should have created a secondary secret
                    # We return an arbitrary secondary secret as the server will accept any secondary secret in this case
                    e.text = 290385
                
                params['SECONDARY_SECRET'] = e.text
                
        # error resetting, try to find out why
        else:
            if '404' == status:
                params['ERROR'] = ErrorStr('Unknown account')
            else:
                params['ERROR'] = ErrorStr(content or 'Password reset failed')
            params['ACCOUNT_ID'] = email
            if 'Account has not been initialized' == content:
                params['UNINITIALIZED'] = True

    return utils.render_template('ui/forgot_password', params)


def reset_password(request, account_id, primary_secret):
    """
    http://localhost/accounts/foo@bar.com/reset_password/taOFzInlYlDKLbiM
    """
    params = {'ACCOUNT_ID': account_id, 'PRIMARY_SECRET': primary_secret, 'SETTINGS': settings}
    
    if HTTP_METHOD_POST == request.method:
        secondary_secret = request.POST.get('conf1', '') + request.POST.get('conf2', '')
        check_params = {}
        if settings.PASSWORD_RESET_REQUIRE_SECONDARY:
            check_params = { 'secondary_secret': secondary_secret }
        
        # check the validity of the primary and secondary secrets
        api = get_api()
        resp, content = api.account_check_secrets(account_email=account_id, primary_secret=primary_secret, body={
            'secondary_secret': secondary_secret
        })
        
        # secrets are valid, set the new password:
        if '200' == resp['status']:
            params['SECONDARY_SECRET'] = secondary_secret
            
            # get account info
            resp, content = api.account_info(account_email = account_id)
            account = utils.parse_account_xml(content or '<root/>')
            
            # check passwords
            pw1 = request.POST.get('pw1')
            if len(pw1) >= (settings.REGISTRATION['min_password_length'] or 8):
                pw2 = request.POST.get('pw2')
                if pw1 == pw2:
                    resp, content = api.account_password_set(account_email=account_id, body={'password': pw1})
                    #MERGE dev_landing scramble comment
                    # password was reset, log the user in
                    if '200' == resp['status']:
                        # reset the primary secret to void the reset email
                        api.put('/accounts/%s/primary-secret' % account_id)
                        
                        try:
                            try:
                                username = account['auth_systems'][0]['username']      # TODO: I don't like this...
                                tokens_get_from_server(request, username, pw1)
                            except Exception as e:
                                params['ERROR'] = ErrorStr(str(e))                     # We'll never see this
                            return HttpResponseRedirect(reverse(index))
                        
                        except Exception as e:
                            params['ERROR'] = ErrorStr(str(e))
                        except IOError as e:
                            params['ERROR'] = ErrorStr(e.strerror)
                    else:
                        params['ERROR'] = ErrorStr(content or 'Password reset failed')
                else:
                    params['ERROR'] = ErrorStr('Passwords do not match')
            else:
                params['ERROR'] = ErrorStr('Password too short')
        
        # wrong secrets (primary or secondary)
        elif '403' == resp['status']:
            if settings.PASSWORD_RESET_REQUIRE_SECONDARY:
                params['ERROR'] = ErrorStr('Wrong confirmation code')
            else:
                params['ERROR'] = ErrorStr('Wrong secret')
        else:
            params['ERROR'] = ErrorStr(content or 'Wrong confirmation code')
    
    return utils.render_template('ui/reset_password', params)


def account_name(request, account_id):
    """
    http://localhost/accounts/foo@bar.com/name
    """
    api = get_api()
    resp, content = api.account_info(account_email=account_id)
    status = resp['status']
    dict = {'account_id': account_id}
    if '404' == status:
        dict['error'] = ErrorStr('Unknown account').str()
    elif '200' != status:
        dict['error'] = ErrorStr(ret.response.get('response_data', 'Server Error')).str()
    else:
        account = utils.parse_account_xml(content)
        dict['name'] = account.get('fullName')
    
    return HttpResponse(simplejson.dumps(dict))


##
##  Record Carenet Handling
##
def record_create(request):
    """
    GET+POST to /records/
    GET:  Show the "record_create" template
    POST: Try to create a record
    """
    # is adding records enabled?
    if not settings.ALLOW_ADDING_RECORDS:
        return HttpResponseForbidden(ErrorStr('Adding records is disabled').str())
    
    # are we logged in?
    account_id = request.session.get('account_id')
    if not account_id:
        url = "%s?return_url=%s" % (reverse(login), urllib.quote(request.get_full_path()))
        return HttpResponseRedirect(url)
    
    after_create_url = request.POST.get('after_create_url', request.GET.get('after_create_url', ''))
    params = {'AFTER_CREATE_URL': after_create_url, 'ALLOW_ADDING_RECORDS': settings.ALLOW_ADDING_RECORDS}
    
    # POST, try to create a record
    if HTTP_METHOD_POST == request.method:
        ret = _record_create(account_id, request.raw_post_data)
        if 200 == ret.status_code:
            if after_create_url:
                return HttpResponseRedirect(after_create_url)
            elif 'json' == request.POST.get('dataType'):
                return ret
            
            params['MESSAGE'] = _('Successfully created new record')
        else:
            params['ERROR'] = ErrorStr(ret.content).str()
    
    # Not POST and not GET
    elif HTTP_METHOD_GET != request.method:
        return HttpResponseBadRequest()
    
    return utils.render_template('ui/record_create', params)



def jarWrapper(*args):
    process = Popen(['java', '-jar']+list(args), stdout=PIPE, stderr=PIPE)
    ret = []
    stdout, stderr = process.communicate()
    return stdout




def _record_create(account_id, demographics):
    """
    Returns an HttpResponse according to the result
    """
    api = get_api()
    res, content = api.record_create(body=demographics)
    status = res['status']
    
    # success, parse XML and change owner to current user
    if '200' == status:
        tree = ET.fromstring(content or '<Record/>')
        if tree is not None:
            record_id = tree.attrib.get('id')
#            res, content = api.record_set_owner(record_id=record_id, body=account_id)
            res, content = api.record_set_owner(record_id=record_id, body=account_id, content_type='text/plain')
            status = res['status']
            if '200' == status:
                record = {'record_id': record_id, 'label': tree.attrib.get('label')}
                path = os.path.dirname(os.path.realpath(__file__))
                filename = os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/" + 'linkingPseudonyms.jar')
                writeFileN = os.path.join(os.path.dirname(os.path.realpath(__file__)) + "/" +'file.py')
                f = open( writeFileN, 'w' )
                f.write( 'dict = ' + demographics + '\n' )
                f.close()
                args = [filename, demographics, record_id] # Any number of args to be passed to the jar file

                result = jarWrapper(*args)
		api.record_pha_setup(record_id=record_id,pha_email = 'calendar@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'problems@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'allergies@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'medications@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'forum@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'algac@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'fare@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'psyche@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'decisionaid@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'otherapps@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'contact@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'seriousgames@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'documentsupload@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'measurements@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'labs@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'semanticSearch@apps.indivo.org')
		api.record_pha_setup(record_id=record_id,pha_email = 'appointments@apps.indivo.org')
		api.record_pha_setup(record_id=record_id,pha_email = 'procedures@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'forum@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'pdq@apps.indivo.org')
                api.record_pha_setup(record_id=record_id,pha_email = 'mystatistics@apps.indivo.org')
                return HttpResponse(simplejson.dumps(record))
    
    # failed
    if '403' == status:
        return HttpResponseForbidden()
    return HttpResponseBadRequest(ErrorStr(content or 'Error creating record').str())


def record_carenet_create(request, record_id):
    """
    Create a new carenet for the given record. POST data must have a name, which must not yet exist for this record
    POST /records/{record_id}/carenets/
    """
    if HTTP_METHOD_POST == request.method:
        name = request.POST.get('name')
        if name:
            api = get_api(request)
            resp, content = api.carenet_create(record_id=record_id, body={'name': name})
            status = resp['status']
            default_name = _('New carenet')
            has_default_name = (default_name == name)
            
            # if we tried to create a carenet with "New carenet" and it already existed, try again with "New carenet-1" and so on to not annoy the user
            if has_default_name:
                i = 0
                while '200' != status and 'Carenet name is already taken' == content:       # todo: Hardcoded server resp here, improve (server should return a 409, maybe?)
                    i += 1
                    name = '%s-%d' % (default_name, i)
                    resp, content = api.carenet_create(record_id=record_id, body={'name': name})
                    status = resp['status']
            
            # success
            if '200' == status:
                nodes = ET.fromstring(content or '<root/>').findall('Carenet')
                tree = nodes[0] if len(nodes) > 0 else None
                if tree is not None:
                    tree.attrib['has_default_name'] = '1' if has_default_name else '0'
                    return HttpResponse(ET.tostring(tree))
            
            return HttpResponseBadRequest(ErrorStr(content or 'Error creating carenet').str())
    
    return HttpResponseBadRequest()


##
##  Carenet Handling
##
def carenet_rename(request, carenet_id):
    """
    POST 'name' to /carenets/{carenet_id}/rename
    """
    if HTTP_METHOD_POST == request.method:
        name = request.POST.get('name')
        if name:
            api = get_api(request)
            resp, content = api.carenet_rename(carenet_id=carenet_id, body={'name': name})
            status = resp['status']
            if '200' == status:
                return HttpResponse(content);
            elif '403' == status:
                return HttpResponseForbidden('You do not have permission to rename carenets')
            return HttpResponseBadRequest(ErrorStr(content or 'Error renaming carenet').str())
    
    return HttpResponseBadRequest()


def carenet_delete(request, carenet_id):
    """
    DELETE /carenets/{carenet_id}
    """
    if HTTP_METHOD_DELETE == request.method:
        api = get_api(request)
        resp, content = api.carenet_delete(carenet_id=carenet_id)
        status = resp['status']
        if '200' == status:
            return HttpResponse('ok')
        if '403' == status:
            return HttpResponseForbidden('You do not have permission to delete carenets')
        return HttpResponseBadRequest(ErrorStr(content or 'Error deleting carenet').str())
    
    return HttpResponseBadRequest()


##
##  Apps
##
def launch_app(request, app_id):
    """ Entry point for a given app.

    If the app does not exist (or another exception occurrs), will render /ui/error with the given error message. On
    success, renders /ui/record_select after the user has logged in. Selecting a record will redirect to launch_app_complete.
    
    """
    
    # make the user login first
    login_url = "%s?return_url=%s" % (reverse(login), urllib.quote(request.get_full_path()))
    account_id = urllib.unquote(request.session.get('account_id', ''))
    if not account_id:
        return HttpResponseRedirect(login_url)
        
    # logged in, check for existence of app
    api = get_api(request)
    resp, content = api.pha(pha_email=app_id)
    status = resp['status']
    if '404' == status:
        return utils.render_template('ui/error', {'error_message': ErrorStr('No such App').str(), 'error_status': status})
        
    # read account records
    error_message = None
    resp, content = api.record_list(account_email=account_id)
    status = resp['status']
    
    if '404' == status:
        error_message = ErrorStr('Unknown account').str()
    elif '403' == status:
        return HttpResponseRedirect(login_url)
    elif '200' != status:
        error_message = ErrorStr(content or 'Error getting account records').str()
    if error_message:
        return utils.render_template('ui/error', {'error_message': error_message, 'error_status': status})
    
    # parse records XML
    records_xml = content or '<root/>'
    records_extracted = [[r.get('id'), r.get('label')] for r in ET.fromstring(records_xml).findall('Record')]
    records = []
    for rec_id, rec_label in records_extracted:
        rec_dict = { 'record_id': rec_id, 'carenet_id' : '' }           # TODO: Carenets are not yet supported
        records.append([rec_id, rec_label])

    return utils.render_template('ui/record_select', {'SETTINGS': settings, 'APP_ID': app_id, 'RECORD_LIST': records})


def launch_app_complete(request, app_id):
    """ Prepare an app's start url for launch, and redirect to it. 

    If this is a POST, then enable the app first (because it was just authorized)
    """

    # make the user login first
    login_url = "%s?return_url=%s" % (reverse(login), urllib.quote(request.get_full_path()))
    account_id = urllib.unquote(request.session.get('account_id', ''))
    if not account_id:
        return HttpResponseRedirect(login_url)

    # If we were just authorized, enable the app
    if request.method == 'POST':
        record_id = request.POST.get('record_id', '')
        carenet_id = ''
        api = get_api(request)
        if record_id:
            resp, content = api.record_pha_enable(record_id=record_id, pha_email=app_id)
            status = resp['status']
            if status != '200':
                error_message = ErrorStr("Error enabling the app")
                return utils.render_template('ui/error', {'error_message': error_message, 'error_status': status})
            
    if request.method == 'GET':
        record_id = request.GET.get('record_id', '')
        carenet_id = request.GET.get('carenet_id', '')

    params_dict = {'record_id':record_id, 'carenet_id':carenet_id}

    # logged in, get information about the desired app
    api = get_api(request)
    resp, content = api.pha(pha_email=app_id)
    status = resp['status']
    error_message = None
    if '404' == status:
        error_message = ErrorStr('No such App').str()
    elif '200' != status:
        error_message = ErrorStr(content or 'Error getting app info').str()
    
    # success, find start URL template
    else:
        app_info_json = content or ''
        app_info = simplejson.loads(app_info_json)
        if not app_info:
            error_message = ErrorStr('Error getting app info')
        else:
            start_url = app_info.get('index')    
            start_url = _interpolate_url_template(app_info.get('index'), params_dict)
            if not start_url:
                error_message = ErrorStr('Error getting app info: no start URL')

    if error_message is not None:
        return utils.render_template('ui/error', {'error_message': error_message, 'error_status': status})

    # get SMART credentials for the request
    api = get_api(request)
    resp, content = api.get_connect_credentials(account_email=account_id, pha_email=app_id, body=params_dict)
    status = resp['status']
    if status == '403':
        if carenet_id:
            error_message = ErrorStr("This app is not enabled to be run in the selected carenet.")
        elif record_id:
            return utils.render_template('ui/authorize_record_launch_app',
                                         {'CALLBACK_URL': '/apps/%s/complete/'%app_id,
                                          'RECORD_ID': record_id,
                                          'TITLE': _('Authorize "{{name}}"?').replace('{{name}}', app_info['name'])
})
    elif status != '200':
        error_message = ErrorStr("Error getting account credentials")
    else:
        oauth_header = etree.XML(content).findtext("OAuthHeader")
        if not oauth_header:
            error_message = ErrorStr("Error getting account credentials")

    if error_message is not None:
        return utils.render_template('ui/error', {'error_message': error_message, 'error_status': status})

    # append the credentials and redirect
    querystring_sep = '&' if '?' in start_url else '?'
    start_url += querystring_sep + "oauth_header=" + oauth_header
    return HttpResponseRedirect(start_url)
    
##
##  Helpers
##
def indivo_api_call_get(request, relative_path):
    """
    take the call, forward it to the Indivo server with oAuth signature using
    the session-stored oAuth tokens OR connect tokens passed in via the request
    """

    if DEBUG:
        utils.log('indivo_api_call_get: ' + request.path)
    if not tokens_p(request):
        utils.log('indivo_api_call_get: No oauth_token or oauth_token_secret... sending to login')
        res = HttpResponse("Unauthorized")
        res.status_code = 401
        return res

    # Add a leading slash onto the relative path
    relative_path = "/" + relative_path
    method = request.method

    # Pull in the GET / POST data
    query_dict = copy.copy(request.GET)
    post_dict = copy.copy(request.POST)
    post_data = post_dict or request.raw_post_data
    
    # Parse the Authorization headers for a connect token, if available
    oauth_request = OauthRequest.from_request('GET', settings.INDIVO_UI_SERVER_BASE, headers=request.META)
    if oauth_request:
        connect_token = oauth_request['connect_token'] or None
        connect_secret = retrieve_connect_secret(request, connect_token)
    else:
        connect_token = connect_secret = None

    # Get the API, signed with a connect token if available, and the session token otherwise
    if connect_token and connect_secret:
        oauth_token = {
            'oauth_token': connect_token,
            'oauth_token_secret': connect_secret
            }
        api = get_api()
        api.update_token(oauth_token)
    else:
        api = get_api(request)
        
    # Make the call, and return the response
    if method == 'GET':
        resp, content = api.get(relative_path, body=query_dict, **(query_dict or {}))       # the body=query_dict is needed to actually have GET params forwarded to the server (pp, 9/24/2012)
    elif method == 'POST':
        # TODO: content type for post?
        resp, content = api.post(relative_path, body=post_data, **(query_dict or {}))
    elif method == 'PUT':
        resp, content = api.put(relative_path, body=post_data, **(query_dict or {}))
    elif method == 'DELETE':
        resp, content = api.delete(relative_path, **(query_dict or {}))
    
    return HttpResponse(content, status=resp['status'], content_type=resp['content-type'])

def indivo_api_call_delete_record_app(request):
    """
    sort of like above but for app delete
    """
    if request.method != HTTP_METHOD_POST:
        return HttpResponseRedirect('/')
    
    if DEBUG:
        utils.log('indivo_api_call_delete_record_app: ' + request.path + ' ' + request.POST['app_id'] + ' ' + request.POST['record_id'])
    
    if not tokens_p(request):
        utils.log('indivo_api_call_delete_record_app: No oauth_token or oauth_token_secret... sending to login')
        return HttpResponseRedirect('/login')
    
    # update the IndivoClient object with the tokens stored in the django session
    api = get_api(request)
    
    # get the app id from the post, and return to main
    resp, content = api.pha_record_delete(record_id=request.POST['record_id'], pha_email=request.POST['app_id'])
    
    return HttpResponse(resp['status'])


##
##  Authorization
##
def authorize(request):
    """
    If we arrive here via GET:
        If user has no valid token:
            Redirect to login with return_url set to the request URL
        For not yet approved apps:
            Return JSON with some info data, ui_server will then have the user click "OK"
        For already approved apps:
            Silently approve and proceed
    
    If we arrive here via POST:
        Approve the request token in 'oauth_token' for the record id in 'record_id' and redirect to:
        after_auth?oauth_token=<access_token>&oauth_verifier=<oauth_verifier>
    
    app_info (the response_data from the get_request_token_info call) looks something like:
    
    <RequestToken token="LNrHRM1OA6ExcSyq22O0">
        <record id="cface90b-6ca0-4368-827a-2ccd5979ffb7"/>
        <carenet />
        <kind>new</kind>
        <App id="indivoconnector@apps.indivo.org">
            <name>Indivo Connector</name>
            <description>None</description>
            <autonomous>True</autonomous>
    
            <autonomousReason>This app connects to your record to load new data into it while you sleep.</autonomousReason>
    
            <frameable>True</frameable>
            <ui>True</ui>
        </App>
    
        <Permissions>
        </Permissions>
    
    </RequestToken>
    """
    
    # if we don't have a valid token then go to login
    if not tokens_p(request):
        url = "%s?return_url=%s" % (reverse(login), urllib.quote(request.get_full_path()))
        return HttpResponseRedirect(url)
    
    api = get_api(request)
    request_token = request.REQUEST.get('oauth_token')
    callback_url = request.REQUEST.get('oauth_callback')
    
    # process GETs (initially adding an app and a normal call for this app)
    if request.method == HTTP_METHOD_GET and request_token is not None:
        
        # claim request token and check return value
        resp, content = api.request_token_claim(reqtoken_id=request_token)
# TODO: check into case of no response.  Does this make sense now?
#        if not resp or not resp.response: 
#            return utils.render_template('ui/error', {'error_message': 'no response to claim_request_token'})
        
        response_status = resp['status']
        if response_status != '200':
            response_message = content or 'bad response to claim_request_token'
            return utils.render_template('ui/error', {'error_status': response_status, 'error_message': ErrorStr(response_message)})
        
        # get info on the request token
        resp, app_info = api.request_token_info(reqtoken_id=request_token)
        e = ET.fromstring(app_info)
        record_id = e.find('record').attrib.get('id', None)
        carenet_id = e.find('carenet').attrib.get('id', None)
        name = e.findtext('App/name')
        app_id = e.find('App').attrib['id']
        kind = e.findtext('kind')
        description = e.findtext('App/description')
        if description == 'None': description = None # remove me after upgrade of template if tags in django 1.2
        autonomous = e.findtext('App/autonomous')
        if autonomous == 'True': 
            autonomous = True
            autonomousReason = e.findtext('App/autonomousReason')
        else:
            autonomous = False
            autonomousReason = ''
        
        # the "kind" param lets us know if this is app setup or a normal call
        if kind == 'new':
            title = _('Authorize "{{name}}"?').replace('{{name}}', name)
            
            if record_id:
                # single record
                resp, record_xml = api.record(record_id = record_id)
                record_node = ET.fromstring(record_xml)
                RECORDS = [[record_node.attrib['id'], record_node.attrib['label']]]
                
                #carenet_els = ET.fromstring(api.get_record_carenets(record_id = record_id).response['response_data']).findall('Carenet')
                #carenets = [{'id': c.attrib['id'], 'name': c.attrib['name']} for c in carenet_els]
                carenets = None
            else:
                resp, records_xml = api.record_list(account_email=urllib.unquote(request.session['account_id']))
                RECORDS = [[r.get('id'), r.get('label')] for r in ET.fromstring(records_xml).findall('Record')]
                carenets = None
            
            # render a template if we have a callback and thus assume the request does not come from chrome UI
            request.session['oauth_callback'] = callback_url
            return utils.render_template('ui/authorize_record', {'REQUEST_TOKEN': request_token,
                                                                      'CALLBACK_URL': callback_url,
                                                                         'RECORD_ID': record_id,
                                                                             'TITLE': title})
        
        elif kind == 'same':
            # return HttpResponse('fixme: kind==same not implimented yet')
            # in this case we will have record_id in the app_info
            return _approve_and_redirect(request, request_token, record_id, carenet_id)
            
        else:
            return utils.render_template('ui/error', {'error_message': 'bad value for kind parameter'})
    
    
    # process POST -- authorize the given token for the given record_id
    elif request.method == HTTP_METHOD_POST \
        and request.POST.has_key('oauth_token') \
        and request.POST.has_key('record_id'):
        
        resp, content = api.request_token_info(reqtoken_id=request_token)
        e = ET.fromstring(content)
        
        record_id = e.find('record').attrib.get('id', None)
        carenet_id = e.find('carenet').attrib.get('id', None)
        #name = e.findtext('App/name')
        app_id = e.find('App').attrib['id']
        #kind = e.findtext('kind')
        #description = e.findtext('App/description')
        query_params = {
         'limit': 100,
         'offset': 0,
         #'order_by': 'startDate',
         'status': 'active',
        }
        # get record info
        #record_id = request.session['record_id']
        #resp, content = client.record(record_id=record_id)
        #if resp['status'] != '200':
            # TODO: handle errors
        #    raise Exception("Error reading Record info: %s"%content)
        #record = parse_xml(content)


        # read problems
        #resp, content = client.generic_list(record_id=record_id, data_model="Problem", body=query_params)
        #if resp['status'] != '200':
            # TODO: handle errors
        #    raise Exception("Error reading problems: %s"%content)
        #probs = simplejson.loads(content)
        #for pr in probs:
        #    problem_idd = pr['id']
        #    api.carenet_document_placement(carenet_id = carenet_id,record_id=record_id,document_id=problem_idd) 
        offline_capable = request.POST.get('offline_capable', False)
        if offline_capable == "0":
            offline_capable = False
        
        # authenticate for this record
        if request.POST.has_key('record_id'):
            location = _approve_and_redirect(request, request_token, request.POST['record_id'], offline_capable = offline_capable)
        
        approved_carenet_ids = request.POST.getlist('carenet_id')
        
        # go through the carenets and add the app to the record
        for approved_carenet_id in approved_carenet_ids:
            api.carenet_apps_create(carenet_id = approved_carenet_id, app_email = app_id)
            api.autoshare_create(carenet_id = carenet_id,record_id=record_id,body={'type':'Problem'})
#            api.autoshare_delete(carenet_id = approved_carenet_id,record_id=record_id,body={'type':'Problem'})       
        return location
    
    return HttpResponse('bad request method or missing param in request to authorize')


def authorize_cancel(request):
    """docstring for authorize_cancel"""
    pass


def _approve_and_redirect(request, request_token, record_id=None, carenet_id=None, offline_capable=False):
    """
    carenet_id is the carenet that an access token is limited to.
    """
    api = get_api(request)
    data = {}
    if record_id:
        data['record_id'] = record_id
    if carenet_id:
        data['carenet_id'] = carenet_id
    if offline_capable:
        data['offline'] = 1
    
    resp, content = api.request_token_approve(reqtoken_id=request_token, body=data)
    status = resp['status']
    if '200' == status:
        # strip location= (note: has token and verifer)
        location = urllib.unquote(content[9:])
        return HttpResponseRedirect(location)
    if '403' == status:
        return HttpResponseForbidden(content)
    return HttpResponseBadRequest(content)


def _interpolate_url_template(url, variables):
    """ Interpolates variables into a url which has placeholders enclosed by curly brackets """
    
    new_url = url
    for key in variables:
        new_url = re.sub('{\s*' + key + '\s*}', variables.get(key), new_url)
    
    return new_url


def localize_jmvc_template(request, *args, **kwargs):
    """
    localize JMVC's .ejs templates using django's template engine
    """
    # get static response
    response = serve(request, *args, **kwargs)
    
    # pass it to the template engine
    response_text = response.content
    template = Template(response_text)
    response_localized = template.render(Context({}))
     
    return HttpResponse(response_localized)
