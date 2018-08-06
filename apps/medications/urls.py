from django.conf.urls.defaults import *
from views import *
import settings
from django.conf import settings as rootsettings

urlpatterns = patterns('',
   # authentication
   (r'^start_auth', start_auth),
   (r'^after_auth', after_auth),

   # screens
   (r'^medications/codelookup$', code_lookup),

   # TESTING
   #(r'^medications/test$', test_message_send),

   (r'^medications/$', medication_list),
   (r'^medications/delete/(?P<medication_id>[^/]+)', archived_medication),
   (r'^medications/edit/(?P<medication_id>[^/]+)', edit_medication),
   (r'^medications/restore/(?P<medication_id>[^/]+)', restore_medication),

   (r'^medications/new$', new_medication),
   (r'^medications/archived$', archived_medications),
   (r'^medications/addFill/(?P<medication_id>[^/]+)', add_fill),
   (r'^medications/(?P<medication_id>[^/]+)', one_medication),


   # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
)
