from django.conf.urls.defaults import *
from views import *
import settings
from django.conf import settings as rootsettings

# all this is under apps/labs
urlpatterns = patterns('',
    # authentication
    (r'^start_auth', start_auth),
    (r'^after_auth', after_auth),
    

   

     # screens
    (r'^codelookup$', code_lookup),
     
       # TESTING
    #(r'^test$', test_message_send), 
    #(r'^labs/new/$', new_lab),
    (r'^labs$', list_labs),
    (r'^new$', new_lab),
    #(r'^labs/new/$', new_lab),
    #(r'^lab/delete/(?P<lab_id>[^/]+)/$', archived_lab),
    #(r'^new/$', new_lab),

    (r'^delete/(?P<lab_id>[^/]+)/$', archived_lab),
    (r'^edit/(?P<lab_id>[^/]+)', edit_lab),
    #(r'^labs/new/$', new_lab),
    (r'^lab/(?P<lab_id>[^/]+)/$', show_lab), 
    (r'^restore/(?P<lab_id>[^/]+)', restore_lab),
    #(r'^labs/new/$', new_lab),
    (r'^archived$', archived_labs),
    (r'^lab/(?P<lab_id>[^/]+)', one_lab),
    #(r'^labs$', list_labs), 
    #(r'^delete/(?P<lab_id>[^/]+)/', archived_lab),

   

    # static
    ## WARNING NOT FOR PRODUCTION
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
    #(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_HOME}),
    #(r'^new$', new_lab),
    # (r'^labs/(?P<med_id>[^/]+)', one_med),
    #(r'^$', lambda request: index()),
    (r'^jmvc/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.JMVC_HOME}),
    (r'^(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.JS_HOME})
)


