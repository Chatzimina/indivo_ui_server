from django.conf.urls.defaults import *
from views import *
import settings
from django.conf import settings as rootsettings

urlpatterns = patterns('',
   # authentication


   (r'^start_auth', start_auth),
   (r'^after_auth', after_auth),

   # screens
   (r'^appointments/codelookup$', code_lookup),

   # TESTING
   (r'^appointments/test$', test_message_send),

   (r'^appointments/$', appointment_list),
   (r'^appointments/delete/(?P<appointment_id>[^/]+)', archived_appointment),
   (r'^appointments/edit/(?P<appointment_id>[^/]+)', edit_appointment),

   (r'^appointments/restore/(?P<appointment_id>[^/]+)', restore_appointment),
   (r'^appointments/new$', new_appointment),
   (r'^appointments/archived$', archived_appointments),
   (r'^appointments/(?P<appointment_id>[^/]+)', one_appointment),
    # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
)
