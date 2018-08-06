from django.conf.urls.defaults import *
from views import *
import settings
from django.conf import settings as rootsettings

urlpatterns = patterns('',
   # authentication
   (r'^start_auth', start_auth),
   (r'^after_auth', after_auth),

   # screens
   (r'^clinicianquestions/codelookup$', code_lookup),

   # TESTING
   (r'^clinicianquestions/test$', test_message_send),

   (r'^clinicianquestions/$', clinicianquestion_list),
   (r'^clinicianquestions/delete/(?P<clinicianquestion_id>[^/]+)', archived_clinicianquestion),
   (r'^clinicianquestions/edit/(?P<clinicianquestion_id>[^/]+)', edit_clinicianquestion),
   (r'^clinicianquestions/share_step$',share_step),

   (r'^clinicianquestions/restore/(?P<clinicianquestion_id>[^/]+)', restore_clinicianquestion),
   (r'^clinicianquestions/new$', new_clinicianquestion),
   (r'^clinicianquestions/archived$', archived_clinicianquestions),
   (r'^clinicianquestions/(?P<clinicianquestion_id>[^/]+)', one_clinicianquestion),
    # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
)
