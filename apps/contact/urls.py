from django.conf.urls.defaults import *
from views import *
import settings
from django.conf import settings as rootsettings

urlpatterns = patterns('',
   # authentication
   (r'^start_auth', start_auth),
   (r'^after_auth', after_auth),
   

   #(r'^labs/new/$', new_lab),
   # screens
   (r'^contact/codelookup$', code_lookup),

   # TESTING
   (r'^contact/test$', test_message_send),
   
   (r'^contact/$', procedure_list),
   (r'^contact/new$', new_problem),
    (r'^contact/contact$', contact),  
    # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
)
