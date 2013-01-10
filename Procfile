web: python prosperime/manage.py collectstatic --noinput; gunicorn prosperime.wsgi
celeryd: python prosperime/manage.py celeryd -E -B --loglevel=INFO