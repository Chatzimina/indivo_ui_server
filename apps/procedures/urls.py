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
   (r'^procedures/codelookup$', code_lookup),

   # TESTING
   (r'^procedures/test$', test_message_send),
   
   (r'^procedures/$', procedure_list),
   (r'^procedures/new$', new_problem),
   
 
   (r'^procedures/archived$', archived_procedures),
   (r'^procedures/restore/(?P<procedure_id>[^/]+)', restore_procedure),
   (r'^procedures/delete/(?P<procedure_id>[^/]+)', delete_procedure),
   (r'^procedures/edit/(?P<procedure_id>[^/]+)', edit_procedure),
#   (r'^procedure/restore/(?P<procedure_id>[^/]+)', restore_procedure), 
   (r'^procedures/(?P<procedure_id>[^/]+)', one_procedure),

    # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
)
