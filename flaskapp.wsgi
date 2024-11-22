#!/usr/bin/python
import logging
import os
import sys
logging.basicConfig(stream=sys.stderr)
venv_site_packages = '/var/www/FlaskApp/virtualenv/lib/python3.12/site-packages'
sys.path.insert(0, venv_site_packages)
sys.path.insert(0, "/var/www/FlaskApp/")
os.environ['TEST'] = 'test'
def application(environ, start_response):
    for key in ['TEST']:
        os.environ[key] = environ.get(key, '')
    from FlaskApp import app as _application
    _application.secret_key='secret'
    return _application(environ, start_response)

