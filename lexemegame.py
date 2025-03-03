# -*- coding: utf-8 -*-
# Source:
#   https://wikitech.wikimedia.org/wiki/Help:Toolforge/My_first_Flask_OAuth_tool

import flask
import mwoauth
import os
import requests
import tomllib


app = flask.Flask(__name__)

# Load configuration from TOML file
__dir__ = os.path.dirname(__file__)
with open(os.path.join(__dir__, 'config.toml'), 'rb') as f:
    app.config.update(tomllib.load(f))


@app.route('/')
def index():
    greeting = app.config['GREETING']
    username = flask.session.get('username', None)

    if "oauth_verifier" in flask.request.args and \
         "oauth_token" in flask.request.args:
        # Redirect internally to `/oauth-callback` with the full query string
        return flask.redirect(flask.url_for("oauth_callback", **flask.request.args))
    else:
        return flask.render_template(
            'index.html', username=username, greeting=greeting)


@app.route('/login')
def login():
    """Initiate an OAuth login.
    
    Call the MediaWiki server to get request secrets and then redirect the
    user to the MediaWiki server to sign the request.
    """
    consumer_token = mwoauth.ConsumerToken(
        app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'])
    try:
        redirect, request_token = mwoauth.initiate(
            app.config['OAUTH_MWURI'], consumer_token)
    except Exception:
        app.logger.exception('mwoauth.initiate failed')
        return flask.redirect(flask.url_for('index'))
    else:
        flask.session['request_token'] = dict(zip(
            request_token._fields, request_token))
        return flask.redirect(redirect)


@app.route('/oauth-callback')
def oauth_callback():
    """OAuth handshake callback."""
    if 'request_token' not in flask.session:
        flask.flash(u'OAuth callback failed. Are cookies disabled?')
        return flask.redirect(flask.url_for('index'))

    consumer_token = mwoauth.ConsumerToken(
        app.config['CONSUMER_KEY'], app.config['CONSUMER_SECRET'])

    try:
        access_token = mwoauth.complete(
            app.config['OAUTH_MWURI'],
            consumer_token,
            mwoauth.RequestToken(**flask.session['request_token']),
            flask.request.query_string)

        identity = mwoauth.identify(
            app.config['OAUTH_MWURI'], consumer_token, access_token)    
    except Exception:
        app.logger.exception('OAuth authentication failed')
    
    else:
        flask.session['access_token'] = dict(zip(
            access_token._fields, access_token))
        flask.session['username'] = identity['username']

    return flask.redirect(flask.url_for('index'))


@app.route('/logout')
def logout():
    """Log the user out by clearing their session."""
    flask.session.clear()
    return flask.redirect(flask.url_for('index'))


@app.route("/userinfo")
def userinfo():
    """Fetch user info from Wikidata."""
    if "access_token" not in flask.session:
        return flask.redirect(flask.url_for("login"))

    params = {
        "action": "query",
        "meta": "userinfo",
        "format": "json"
    }
    response = requests.get(app.config['OAUTH_MWURI'], params=params)
    return str(response)


@app.route("/get-senses", methods=["POST"])
def get_senses():
    """Fetch senses for a given lexeme ID from Wikidata."""
    if "access_token" not in flask.session:
        return flask.jsonify({"error": "Unauthorized. Please log in."}), 401

    data = flask.request.get_json()
    lexeme_id = data.get("lexeme_id")

    if not lexeme_id or not lexeme_id.startswith("L"):
        return flask.jsonify({"error": "Invalid lexeme ID. Must start with 'L'."}), 400

    wikidata_api_url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbgetentities",
        "ids": lexeme_id,
        "format": "json"
    }

    response = requests.get(wikidata_api_url, params=params)
    result = response.json()

    if "entities" not in result or lexeme_id not in result["entities"]:
        return flask.jsonify({"error": "Lexeme not found."}), 404

    lexeme_data = result["entities"][lexeme_id]

    senses = []
    if "senses" in lexeme_data:
        for sense in lexeme_data["senses"]:
            sense_id = sense.get("id", "Unknown")
            glosses = sense.get("glosses", {})
            sense_texts = {lang: glosses[lang]["value"] for lang in glosses}
            senses.append({"id": sense_id, "texts": sense_texts})

    return flask.jsonify({"lexeme_id": lexeme_id, "senses": senses})


if __name__ == "__main__":
    app.run(debug=True, port=5555)
