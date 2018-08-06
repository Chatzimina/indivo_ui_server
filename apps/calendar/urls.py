from django.conf.urls.defaults import *
from views import *
import settings
from django.conf import settings as rootsettings

urlpatterns = patterns('',
   # authentication
   (r'^start_auth', start_auth),
   (r'^after_auth', after_auth),

   # screens
   (r'^calendar/codelookup$', code_lookup),

   # TESTING
   (r'^calendar/test$', test_message_send),

   (r'^calendar/$', problem_list),
   (r'^calendar/delete/(?P<problem_id>[^/]+)', archived_problem),
   (r'^calendar/edit/(?P<problem_id>[^/]+)', edit_problem),
   (r'^calendar/restore/(?P<problem_id>[^/]+)', restore_problem),
   (r'^calendar/new$', new_problem),
   (r'^calendar/new_problem_calendar$',new_problem_calendar),
   (r'^calendar/new_procedure_calendar$',new_procedure_calendar),
   (r'^calendar/new_medication_calendar$',new_medication_calendar),
   (r'^calendar/new_appointment_calendar$',new_appointment_calendar),
   (r'^calendar/share_step$',share_step),
   (r'^calendar/archived$', archived_problems),
   (r'^calendar/(?P<problem_id>[^/]+)', one_problem),
    # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
)
