from django.conf.urls.defaults import *
from views import *
import settings
from django.conf import settings as rootsettings
from django.conf.urls.static import static

urlpatterns = patterns('',
   # authenticationarchived
   (r'^start_auth', start_auth),
   (r'^after_auth', after_auth),

   # screens
   (r'^allergies/codelookup$', code_lookup),

   # TESTING
   (r'^allergies/test$', test_message_send),

   (r'^allergies/$', allergies_list),
   (r'^allergies/new$', new_allergy),

   (r'^allergies/delete/(?P<allergy_id>[^/]+)', archived_allergy),
   (r'^allergies/edit/(?P<allergy_id>[^/]+)', edit_allergy),
   (r'^allergies/restore/(?P<allergy_id>[^/]+)', restore_allergy),
   (r'^allergies/archived$', archived_allergies), 
   (r'^allergies/(?P<allergy_id>[^/]+)', one_allergy), 
  # static
    ## WARNING NOT FOR PRODUCTION
   (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': rootsettings.SERVER_ROOT_DIR + settings.STATIC_HOME}),
#   (r'^static/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.MEDIA_ROOT}),
)
 #  urlpatterns += patterns('django.views.static',
  #      (r'media/(?P<path>.*)', 'serve', {'document_root': settings.MEDIA_ROOT}),
   # )


