from django.conf.urls.defaults import *
from views import *
import settings
from django.conf import settings as rootsettings

urlpatterns = patterns('',
   # authentication
   (r'^start_auth', start_auth),
   (r'^after_auth', after_auth),

   # screens
   (r'^documentsupload/codelookup$', code_lookup),

   # TESTING
   (r'^documentsupload/test$', test_message_send),

   (r'^documentsupload/$', documents_upload),
   (r'^documentsupload/documentsupload$', documents_upload),

   (r'^documentsupload/restore/(?P<document_id>[^/]+)', restore_document),
   (r'^documentsupload/new$', new_document),
   (r'^documentsupload/archived$', archived_documents),

   (r'^documentsupload/delete/(?P<document_id>[^/]+)', archived_document),
   (r'^documentsupload/details/(?P<document_id>[^/]+)', details),

   (r'^documentsupload/(?P<document_id>[^/]+)', one_document),


    # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
    
    )
