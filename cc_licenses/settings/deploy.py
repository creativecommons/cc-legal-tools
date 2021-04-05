# Settings for live deployed environments: vagrant, staging, production, etc
# Standard library
import os

from .base import *  # noqa: F403

os.environ.setdefault("CACHE_HOST", "127.0.0.1:11211")
os.environ.setdefault("BROKER_HOST", "127.0.0.1:5672")

#: deploy environment - e.g. "staging" or "production"
ENVIRONMENT = os.environ["ENVIRONMENT"]


DEBUG = False

if "DATABASE_URL" in os.environ:
    # Dokku
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

    # Third-party
    import dj_database_url

    # Update database configuration with $DATABASE_URL.
    db_from_env = dj_database_url.config(conn_max_age=500)
    DATABASES["default"].update(db_from_env)  # noqa: F405

    # Disable Django's own staticfiles handling in favour of WhiteNoise, for
    # greater consistency between gunicorn and `./manage.py runserver`. See:
    # http://whitenoise.evans.io/en/stable/django.html#using-whitenoise-in-development
    INSTALLED_APPS.remove("django.contrib.staticfiles")  # noqa: F405
    INSTALLED_APPS.extend(  # noqa: F405
        ["whitenoise.runserver_nostatic", "django.contrib.staticfiles"]
    )

    MIDDLEWARE.remove(  # noqa: F405
        "django.middleware.security.SecurityMiddleware"
    )
    MIDDLEWARE = [  # noqa: F405
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
    ] + MIDDLEWARE  # noqa: F405

    # Allow all host headers (feel free to make this more specific)
    ALLOWED_HOSTS = ["*"]

    # Simplified static file serving.
    # https://warehouse.python.org/project/whitenoise/
    STATICFILES_STORAGE = (
        "whitenoise.storage.CompressedManifestStaticFilesStorage"
    )

else:
    SECRET_KEY = os.environ["SECRET_KEY"]

    DATABASES["default"]["NAME"] = os.environ.get("DB_NAME", "")  # noqa: F405
    DATABASES["default"]["USER"] = os.environ.get("DB_USER", "")  # noqa: F405
    DATABASES["default"]["HOST"] = os.environ.get("DB_HOST", "")  # noqa: F405
    DATABASES["default"]["PORT"] = os.environ.get("DB_PORT", "")  # noqa: F405
    DATABASES["default"]["PASSWORD"] = os.environ.get(  # noqa: F405
        "DB_PASSWORD", ""
    )


STATIC_ROOT = os.getenv(
    "STATIC_ROOT", os.path.join(ROOT_DIR, "static")  # noqa: F405
)

MEDIA_ROOT = os.getenv(
    "MEDIA_ROOT", os.path.join(ROOT_DIR, "media")  # noqa: F405
)

EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", False)
# use TLS or SSL, not both:
assert not (EMAIL_USE_TLS and EMAIL_USE_SSL)
if EMAIL_USE_TLS:
    default_smtp_port = 587
elif EMAIL_USE_SSL:
    default_smtp_port = 465
else:
    default_smtp_port = 25
EMAIL_PORT = os.environ.get("EMAIL_PORT", default_smtp_port)
EMAIL_SUBJECT_PREFIX = os.getenv(
    "EMAIL_SUBJECT_PREFIX", "[CC-Licenses %s] " % ENVIRONMENT.title()
)
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", "noreply@%(DOMAIN)s" % os.environ
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

CSRF_COOKIE_SECURE = True

SESSION_COOKIE_SECURE = True

SESSION_COOKIE_HTTPONLY = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
if os.environ.get("DOMAIN", None) is not None:
    ALLOWED_HOSTS.append(os.environ["DOMAIN"])

# Use template caching on deployed servers
for backend in TEMPLATES:  # noqa: F405
    if backend["BACKEND"] == "django.template.backends.django.DjangoTemplates":
        default_loaders = ["django.template.loaders.filesystem.Loader"]
        if backend.get("APP_DIRS", False):
            default_loaders.append(
                "django.template.loaders.app_directories.Loader"
            )
            # Django gets annoyed if you both set APP_DIRS True and specify
            # your own loaders
            backend["APP_DIRS"] = False
        loaders = backend["OPTIONS"].get("loaders", default_loaders)
        for loader in loaders:
            if (
                len(loader) == 2
                and loader[0] == "django.template.loaders.cached.Loader"
            ):
                # We're already caching our templates
                break
        else:
            backend["OPTIONS"]["loaders"] = [
                ("django.template.loaders.cached.Loader", loaders)
            ]

# Uncomment if using celery worker configuration
# CELERY_SEND_TASK_ERROR_EMAILS = True
# BROKER_URL = (
#     "amqp://cc_licenses_%(ENVIRONMENT)s:%(BROKER_PASSWORD)s@%(BROKER_HOST)s/"
#     "cc_licenses_%(ENVIRONMENT)s"
#     % os.environ
# )

# Environment overrides
# These should be kept to an absolute minimum
if ENVIRONMENT.upper() == "LOCAL":
    # Don't send emails from the Vagrant boxes
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
