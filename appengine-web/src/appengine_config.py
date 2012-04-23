webapp_django_version = '1.2'
COOKIE_KEY = '9f11da07b5aa57af46d8fbc57a31894c1cd72f47ee4533ee6b2be7dd29bb94409ae7176b17d90c5d9102280be8e36f6476433f3f8a0b6c953b70f8429743fff1'

from gaesessions import SessionMiddleware
import datetime

from django.template import add_to_builtins
add_to_builtins('templatetags.goldframe_templates')

def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = SessionMiddleware(app, cookie_key=COOKIE_KEY, lifetime=datetime.timedelta(weeks=4), no_datastore=True)
    app = recording.appstats_wsgi_middleware(app)
    return app

