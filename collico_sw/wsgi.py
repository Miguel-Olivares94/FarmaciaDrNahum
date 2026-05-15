import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collico_sw.settings_prod')

_django_app = get_wsgi_application()


def application(environ, start_response):
    # Responder 200 al healthcheck de Railway sin pasar por Django.
    # Railway envía Host: healthcheck.railway.app — Django lo rechaza con
    # DisallowedHost antes de que ALLOWED_HOSTS pueda ayudar.
    if (environ.get('HTTP_HOST') == 'healthcheck.railway.app'
            and environ.get('PATH_INFO', '/') == '/'):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'OK']
    return _django_app(environ, start_response)
