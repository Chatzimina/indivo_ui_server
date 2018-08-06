from django.conf.urls.defaults import *
from views import *
import settings
from django.conf import settings as rootsettings

urlpatterns = patterns('',
   # authentication
   (r'^start_auth', start_auth),
   (r'^after_auth', after_auth),

   # screens
#   (r'^editDemographics/codelookup$', code_lookup),

   # TESTING
   (r'^editDemographics/test$', test_message_send),

   (r'^editDemographics/$', problem_list),
#   (r'^editDemographics/delete/(?P<problem_id>[^/]+)', archived_problem),
#   (r'^editDemographics/edit/(?P<problem_id>[^/]+)', edit_problem),
   (r'^editDemographics/updateDemographics$', updateDemographics),
#   (r'^editDemographics/restore/(?P<problem_id>[^/]+)', restore_problem),
#   (r'^editDemographics/new$', new_problem),
#   (r'^editDemographics/archived$', archived_problems),
#   (r'^editDemographics/(?P<problem_id>[^/]+)', one_problem),
    # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
)
