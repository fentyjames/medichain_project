"""
MediChain Django Project Settings
A scalable cross-chain Layer-2 blockchain framework for privacy-preserving 
and interoperable healthcare data exchange using zero-knowledge proofs.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-7&@&3jmiuam6hkb1a#*jzm403p#(!*9%w+w%s+$9b-krhwj#$&'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'blockchain',
    'healthcare',
    'cross_chain',
    'zk_proofs',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'blockchain.middleware.ZKProofMiddleware',
    'blockchain.middleware.CrossChainMiddleware',
]

ROOT_URLCONF = 'medichain_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'medichain_project.wsgi.application'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'medichain_db',
#         'USER': 'postgres',
#         'PASSWORD': 'master011',
#         'HOST': 'localhost',
#         'PORT': '5433',
#     },
#     'blockchain': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'blockchain_db.sqlite3',
#     }
# }

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'medichain_db',
#         'USER': 'postgres',
#         'PASSWORD': 'master011',
#         'HOST': 'localhost',
#         'PORT': '5433',
#     },
#     'blockchain': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'blockchain_db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'medichain_db',
        'USER': 'postgres',
        'PASSWORD': 'master011',
        'HOST': 'localhost',
        'PORT': '5433',
    }
}

#DATABASE_ROUTERS = ['medichain_project.db_router.BlockchainRouter']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# MediChain Specific Settings
MEDICHAIN_CONFIG = {
    'BLOCKCHAIN_NETWORKS': [
        {'id': 'ethereum_main', 'name': 'Ethereum Mainnet', 'chain_id': 1, 'rpc_url': 'https://mainnet.infura.io/v3/'},
        {'id': 'polygon', 'name': 'Polygon', 'chain_id': 137, 'rpc_url': 'https://polygon-rpc.com'},
        {'id': 'hyperledger', 'name': 'Hyperledger Fabric', 'chain_id': 999, 'rpc_url': 'http://localhost:7051'},
    ],
    'ROLLUP_BATCH_SIZE': 50,
    'ZK_PROOF_TYPE': 'zk_snark',
    'CROSS_CHAIN_RELAY_INTERVAL': 1.0,
    'IPFS_GATEWAY': 'https://ipfs.io/ipfs/',
    'ENCRYPTION_ALGORITHM': 'AES-256-GCM',
    'HASH_FUNCTION': 'SHA-256',
    'CONSENSUS_MECHANISM': 'PBFT',
    'BLOCK_TIME': 12,
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
