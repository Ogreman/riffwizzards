import datetime
import email
import os

import flask
import iso8601
import lxml.html as lxh
import requests
from flask_cacheify import init_cacheify


app = flask.Flask(__name__, template_folder='templates')
app.debug = os.environ.get('DEBUG', False)
app.cache = init_cacheify(app)
app.timeout_mins = int(os.environ.get('CACHE_TIMEOUT_MINS', 10))
app.scrape_url = os.environ.get('SCRAPE_URL', '')
app.download_url = os.environ.get('MIXCLOUD_DOWNLOAD_URL', '')
app.max_items = int(os.environ.get('MAX_ITEMS', 10))
mixcloud_user_url = f"https://api.mixcloud.com/{os.environ.get('MIXCLOUD_USER', 'riffwizzards')}/"
mixcloud_cast_url = f"https://api.mixcloud.com/{os.environ.get('MIXCLOUD_USER', 'riffwizzards')}/cloudcasts/"


@app.template_filter('get_stream_url')
def stream_url(value, scrape=False):
    if scrape:
        response = requests.get(f'{app.scrape_url}{value}')
        html = lxh.fromstring(response.text)
        return html.cssselect('div p a')[-1].text
    return f'{app.download_url}{value}'


@app.template_filter('itunes_compatible_image_url')
def itunes_image_url(value):
    return f"{value.replace('https:', 'http:').replace('300x300', '1400x1400')}?.jpg"


@app.template_filter('parse_date')
def parse_8601_2822(value):
    return email.utils.format_datetime(iso8601.parse_date(value))


@app.route('/itunes.rss')
@app.cache.cached(timeout=1 if app.debug else 60 * app.timeout_mins)
def itunes():
    rss_xml = flask.render_template('itunes.xml',
                                    items=requests.get(mixcloud_cast_url).json()['data'][:app.max_items],
                                    user=requests.get(mixcloud_user_url).json(),
                                    now=email.utils.format_datetime(datetime.datetime.utcnow()),
                                    )
    response = flask.make_response(rss_xml)
    response.headers['Content-Type'] = 'application/rss+xml'
    return response


@app.route('/feed.rss')
@app.cache.cached(timeout=1 if app.debug else 60 * app.timeout_mins)
def feed():
    rss_xml = flask.render_template('standard.xml',
                                    items=requests.get(mixcloud_cast_url).json()['data'][:app.max_items],
                                    user=requests.get(mixcloud_user_url).json(),
                                    now=email.utils.format_datetime(datetime.datetime.utcnow()),
                                    )
    response = flask.make_response(rss_xml)
    response.headers['Content-Type'] = 'application/rss+xml'
    return response


@app.route('/')
def index():
    return flask.redirect(f"https://mixcloud.com/{os.environ.get('MIXCLOUD_USER', 'riffwizzards')}")


@app.after_request
def apply_accept(response):
    response.headers['Accept-Ranges'] = 'bytes'
    return response


if __name__ == "__main__":
    app.run(debug=app.debug)
