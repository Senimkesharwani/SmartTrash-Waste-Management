import os
from pathlib import Path
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ Security settings
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-placeholder')

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# ✅ Installed apps
INSTALLED_APPS = [
    'django.contrib.admin',             # Admin panel
    'django.contrib.auth',              # Authentication system
    'django.contrib.contenttypes',      # Required for auth
    'django.contrib.sessions',          # Session support
    'django.contrib.messages',          # Flash messages
    'django.contrib.staticfiles',       # Static file management
    'main_app',                         # Your custom app
]

# ✅ Middleware stack
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # Session handling
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Enables request.user
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ✅ URL and WSGI setup
ROOT_URLCONF = 'waste_project.urls'
WSGI_APPLICATION = 'waste_project.wsgi.application'

# ✅ Templates setup
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'main_app' / 'templates'],  # Points to your templates folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ✅ Database (if using MongoDB, this can be used as a reference)
# Note: Django's ORM won’t work with MongoDB directly unless you use Djongo or PyMODM.
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')

# ✅ Static files (CSS, JS, images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'main_app' / 'static']

# ✅ Media files (optional, for uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ✅ Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ✅ Session and login configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Stores sessions in DB
APPEND_SLASH = True  # ✅ Recommended True for URL consistency

# ✅ Optional email and time settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
TIME_ZONE = 'Asia/Kolkata'
USE_TZ = True


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
