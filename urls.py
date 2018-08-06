from django.conf.urls.defaults import *
from django.conf import settings


urlpatterns = patterns('',
    # HARDCODED APP PATHS!! (keep in alpha order)
    (r'^apps/allergies/',       include('apps.allergies.urls')),
    (r'^apps/labs/',            include('apps.labs.urls')),
    (r'^apps/medications/',     include('apps.medications.urls')),
    (r'^apps/problems/',        include('apps.problems.urls')),
    (r'^apps/startpage/',        include('apps.startpage.urls')),
    (r'^apps/otherapps/',        include('apps.otherapps.urls')),
    (r'^apps/clinicianquestions/',        include('apps.clinicianquestions.urls')),
    (r'^apps/procedures/',      include('apps.procedures.urls')),
    (r'^apps/recomlinks/',      include('apps.recomlinks.urls')),
    (r'^apps/calendar/',      include('apps.calendar.urls')),
    (r'^apps/contact/',      include('apps.contact.urls')),
    (r'^apps/contactadmin/',      include('apps.contactadmin.urls')),
    (r'^apps/exportData/',      include('apps.exportData.urls')),
    (r'^apps/mystatistics/',      include('apps.mystatistics.urls')),
   (r'^apps/editDemographics/',      include('apps.editDemographics.urls')),
    (r'^apps/appointments/',      include('apps.appointments.urls')),
    (r'^apps/measurements/',      include('apps.measurements.urls')),
    (r'^apps/documentsupload/',      include('apps.documentsupload.urls')),
    (r'^', include('ui.urls')),  # Everything else to indivo
    (r'^i18n/', include('django.conf.urls.i18n')),
    (r'^indivo_files/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes':True}),


)
