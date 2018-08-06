from django.conf.urls.defaults import *
from views import *
import settings
from django.conf import settings as rootsettings

urlpatterns = patterns('',
   # authentication
   (r'^start_auth', start_auth),
   (r'^after_auth', after_auth),

   # screens
   (r'^exportData/codelookup$', code_lookup),

   # TESTING
   (r'^exportData/test$', test_message_send),

   (r'^exportData/$', allergies_list),
   (r'^exportData/downloadData$', downloadData),
    (r'^exportData/exportrdf$', exportrdf),

   (r'^exportData/allxml$', allxml),
   (r'^exportData/allxml2$', allxml2),
   (r'^exportData/connectDWH$', connectDWH),
   (r'^exportData/problems$', problems),
   (r'^exportData/proceduresxml$', proceduresxml),
   (r'^exportData/labsxml$', labsxml),
   (r'^exportData/(?P<problem_id>[^/]+)', one_problem),

    # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
)
