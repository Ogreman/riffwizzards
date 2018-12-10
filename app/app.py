import datetime
import email
import os

import flask
import iso8601
import requests
from flask_cacheify import init_cacheify


app = flask.Flask(__name__, template_folder='templates')
app.debug = os.environ.get('DEBUG', False)
app.cache = init_cacheify(app)
app.timeout_mins = os.environ.get('CACHE_TIMEOUT_MINS', 10)
mixcloud_user_url = os.environ.get('MIXCLOUD_USER_URL', 'https://api.mixcloud.com/riffwizzards/')
mixcloud_cast_url = os.environ.get('MIXCLOUD_CAST_URL', 'https://api.mixcloud.com/riffwizzards/cloudcasts/')


@app.template_filter('parse_date')
def parse_8601_2822(value):
    return email.utils.format_datetime(iso8601.parse_date(value))


@app.route('/feed.rss')
@app.cache.cached(timeout=1 if app.debug else 60 * app.timeout_mins)
def feed():
    rss_xml = flask.render_template('rss.xml',
                                    items=requests.get(mixcloud_cast_url).json()['data'],
                                    user=requests.get(mixcloud_user_url).json(),
                                    now=email.utils.format_datetime(datetime.datetime.utcnow()),
                                    )
    response = flask.make_response(rss_xml)
    response.headers['Content-Type'] = 'application/rss+xml'
    return response


@app.route('/')
def index():
    return flask.redirect('https://mixcloud.com/riffwizzards')


if __name__ == "__main__":
    app.run(debug=app.debug)
