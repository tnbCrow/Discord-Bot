from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'corsheaders',

    'escrow',
    'core',
]

CORS_ALLOW_ALL_ORIGINS = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = 'static'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Constants
TNBC_MULTIPLICATION_FACTOR = 100000000  # 10^8
TNBC_TRANSACTION_FEE = 2 * TNBC_MULTIPLICATION_FACTOR
CROW_BOT_FEE = 2  # In Percentage

TNBCROW_BOT_ACCOUNT_NUMBER = os.environ['TNBCROW_BOT_ACCOUNT_NUMBER']
SIGNING_KEY = os.environ['SIGNING_KEY']
PROHIBITED_ACCOUNT_NUMBERS = [TNBCROW_BOT_ACCOUNT_NUMBER]
CHECK_TNBC_CONFIRMATION = os.environ['CHECK_TNBC_CONFIRMATION']
BANK_IP = os.environ['BANK_IP']

BOT_MANAGER_ID = os.environ['BOT_MANAGER_ID']
TRADE_CHANNEL_ID = os.environ['TRADE_CHANNEL_ID']
OFFER_CHANNEL_ID = os.environ['OFFER_CHANNEL_ID']
DISPUTE_CHANNEL_ID = os.environ['DISPUTE_CHANNEL_ID']
AGENT_ROLE_ID = os.environ['AGENT_ROLE_ID']
ADMIN_ROLE_ID = os.environ['ADMIN_ROLE_ID']
GUILD_ID = os.environ['GUILD_ID']
TRADE_CHAT_CATEGORY_ID = os.environ['TRADE_CHAT_CATEGORY_ID']
RECENT_TRADE_CHANNEL_ID = os.environ['RECENT_TRADE_CHANNEL_ID']
MVP_SITE_API_KEY = os.environ['MVP_SITE_API_KEY']
COLD_WALLET_ACCOUNT_NUMBER = os.environ['COLD_WALLET_ACCOUNT_NUMBER']
