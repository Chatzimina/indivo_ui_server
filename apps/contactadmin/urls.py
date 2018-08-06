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
   (r'^contactadmin/codelookup$', code_lookup),

   # TESTING
   (r'^contactadmin/test$', test_message_send),
   
   (r'^contactadmin/$', procedure_list),
   (r'^reply/$', reply),
   (r'^contactadmin/new$', new_problem),
   (r'^contactadmin/contactadmin$', contactadmin),  
    # static
    ## WARNING NOT FOR PRODUCTION
   (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
)
