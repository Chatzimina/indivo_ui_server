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
   (r'^measurements/codelookup$', code_lookup),

   # TESTING
   (r'^measurements/test$', test_message_send),
   
   (r'^measurements/$', measurement_list),
   (r'^measurements/new$', new_measurement),
   
 
   (r'^measurements/archived$', archived_measurements),
   (r'^measurements/restore/(?P<measurement_id>[^/]+)', restore_measurement),
   (r'^measurements/delete/(?P<measurement_id>[^/]+)', delete_measurement),
   (r'^measurements/edit/(?P<measurement_id>[^/]+)', edit_measurement),
#   (r'^procedure/restore/(?P<procedure_id>[^/]+)', restore_procedure), 
   (r'^measurements/(?P<measurement_id>[^/]+)', one_measurement),

    # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
)
