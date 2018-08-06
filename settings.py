# the two places where we point to apps are:
# 1. in TEMPLATE_DIRS
# 2. through hardcoded URL routes in the file ref'd by ROOT_URLCONF

SERVER_ROOT_DIR = '/media/data/hatzimin/web/indivo_ui_server'
INDIVO_SERVER_LOCATION = "http://www.iphr.care:8000"#http://139.91.210.59:8000"
INDIVO_UI_SERVER_BASE = "https://www.iphr.care:443"#139.91.210.59:443"
INDIVO_IP= "http://www.iphr.care:8084"#139.91.210.59:8084"
INDIVO_URL= "www.iphr.care:"#139.91.210.59"
STATIC_HOME=SERVER_ROOT_DIR + '/apps/documentsupload/static'
MEDIA_ROOT =  '/media/data/hatzimin/web/indivo_server/indivo_files/'
MEDIA_URL='indivo_files/'
APP_HOME = '/media/data/hatzimin/web/indivo_server'


#SERVER_ROOT_DIR = '/home/hatzimin/web/indivo_ui_server'
#INDIVO_SERVER_LOCATION = "http://139.91.210.63:8000"#http://139.91.210.59:8000"
#INDIVO_UI_SERVER_BASE = "http://139.91.210.63:80"#139.91.210.59:443"
#INDIVO_IP= "http://139.91.210.63:8084"#139.91.210.59:8084"
#INDIVO_URL= "127.0.0.1"#139.91.210.59"
#STATIC_HOME=SERVER_ROOT_DIR + '/apps/documentsupload/static'
#MEDIA_ROOT =  '/home/hatzimin/web/indivo_server/indivo_files/'
#MEDIA_URL='indivo_files/'
#INDIVO_UI_SERVER_BASE = 'http://iapetus-forth-dev-pmed.custodix.com'
# we need to put absolute paths here for the UI server's template AND
# each app's /jmvc/ directory otherwise the UI server will not load the jmvc
# start page. The django.template.loaders.app_directories.Loader is no help
# to us since it looks for a statically named /templates/ directory.
TEMPLATE_DIRS = (
    SERVER_ROOT_DIR + "/templates",
    SERVER_ROOT_DIR + '/apps/allergies/jmvc/',
    SERVER_ROOT_DIR + '/apps/immunizations/jmvc/',
    SERVER_ROOT_DIR + '/apps/labs/jmvc/',
    SERVER_ROOT_DIR + '/apps/medications/jmvc/',

    SERVER_ROOT_DIR + '/apps/contact/',   
    SERVER_ROOT_DIR + '/apps/mystatistics/',
#    SERVER_ROOT_DIR + '/apps/donnorsTool/',
    SERVER_ROOT_DIR + '/apps/bulkimport/',
    SERVER_ROOT_DIR + '/apps/editDemographics/',
    SERVER_ROOT_DIR + '/apps/getSuggestions/',
    SERVER_ROOT_DIR + '/apps/emotionalProfiler/',
#     SERVER_ROOT_DIR + '/apps/exportRDFAvatar/',
    SERVER_ROOT_DIR + '/apps/edss/',
    SERVER_ROOT_DIR + '/apps/appointments/',
    SERVER_ROOT_DIR + '/apps/measurements/',

     SERVER_ROOT_DIR + '/apps/documentsupload/',
    # SERVER_ROOT_DIR + '/apps/problems/templates',
    SERVER_ROOT_DIR + '/apps/'  # the problems app is a non-jmvc app and has a different template path
)

DEBUG = True
TEMPLATE_DEBUG = True
HIDE_HEALTHFEED = True 
HIDE_INBOX = False
HIDE_GET_MORE_APPS = False				# currently unfunctional
HIDE_APP_SETTINGS = False
HIDE_SHARING = False
CONSUMER_KEY='chrome'
CONSUMER_SECRET='chrome'
ROOT_URLCONF = 'urls'

# allow to signup via web?
REGISTRATION = {
	'enable': True,						# True or False
	'set_primary_secret': 1,			# 0 or 1. If 0, administrators will have to approve accounts. If set to 1, make sure the server has SEND_MAIL enabled!
	'set_secondary_secret': 1,			# 0 or 1. Can only be 1 if primary is also 1
	'min_password_length': 8,
	'autocreate_record': True, 			# if True creates a first record based on account name and email automatically
}

# allow user to add records?
ALLOW_ADDING_RECORDS = True

# handling of user secrets
PASSWORD_RESET_REQUIRE_SECONDARY = False

#  quick and dirty private labeling (optional)
# BRANDING = {
#   'short_name': 'gpp',
#   'pretty_name': 'Gene Partnership',
#   'pretty_name_prepend': 'The',
#   'header_template': 'ui/header_gpp.html',
#   'footer_template': 'ui/footer_gpp.html',
#   'logo_image_src': '/jmvc/ui/resources/images/branding/gpp_three_loop_96x31.png',
#   'logo_image_big_src': '/jmvc/ui/resources/images/branding/gpp_three_loop_big.png'
# }

TIME_ZONE = 'UTC'
SESSION_COOKIE_NAME = "indivo_ui_sessionid"
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True
SECRET_KEY = 'indivo'

DEFAULT_CHARSET = 'utf-8'




LANGUAGES = (

    ('en', 'English'),
    ('el', 'Greek'),
    ('de', 'German'),
    ('it','Italian'),
    ('ens','English'),

)

DEFAULT_LANGUAGE = 1
# don't forget comma here. just love the python tuple!
TEMPLATE_LOADERS = ('django.template.loaders.filesystem.Loader',)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

     'django.middleware.locale.LocaleMiddleware',  #EAN THELOUME NA PAIRNEI TIS RUTHMISEIS TOU BROWSER
)



LOCALE_PATHS = (
    '/media/data/hatzimin/web/indivo_ui_server/locale/', 
)
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'ui'
)
# use file based sessions for now - fixme: security?
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = SERVER_ROOT_DIR + "/sessions"
