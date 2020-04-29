
## Install

```bash
virtualenv venv --python=python3
source venv/bin/activate
python -m pip install -r requirements.txt --upgrade
```

## Development

Run development server as:

```bash
FLASK_ENV=development flask run
```

## Production

To run the application on production you should use the uwsgi server. Run it like:

```bash
uwsgi uwsgi.ini
```
