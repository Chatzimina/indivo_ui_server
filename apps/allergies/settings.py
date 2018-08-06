from django.conf import settings # top-level setttings

SUBMODULE_NAME = 'allergies'
INDIVO_SERVER_OAUTH = {
  'consumer_key': SUBMODULE_NAME+'@apps.indivo.org',
  'consumer_secret': SUBMODULE_NAME
}
INDIVO_SERVER_LOCATION = settings.INDIVO_SERVER_LOCATION
INDIVO_UI_SERVER_BASE = settings.INDIVO_UI_SERVER_BASE
INDIVO_IP = settings.INDIVO_IP
# JMVC_HOME = settings.SERVER_ROOT_DIR + '/apps/'+SUBMODULE_NAME+'/jmvc/'
# JS_HOME = JMVC_HOME + SUBMODULE_NAME + '/'

APP_HOME = 'apps/'+SUBMODULE_NAME
TEMPLATE_PREFIX = SUBMODULE_NAME + '/templates'
STATIC_HOME = '/'+APP_HOME+'/static'
#STATIC_URL =  '/'+APP_HOME+'/static/'
MEDIA_ROOT = '/media/data/hatzimin/web/indivo_ui_server/apps/allergies/images'

MEDIA_URL = '/images/'


#MEDIA_ROOT = '/home/hatzimin/web/indivo_ui_server/apps/allergies/images'
#MEDIA_URL = 'http://iapetus.ics.forth.gr:8000/'
