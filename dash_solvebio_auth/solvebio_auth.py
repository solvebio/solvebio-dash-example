from __future__ import absolute_import

import json
import flask

from .oauth import OAuthBase

from solvebio import SolveClient


class SolveBioAuth(OAuthBase):
    AUTH_COOKIE_NAME = 'dash_solvebio_auth'
    TOKEN_COOKIE_NAME = 'solvebio_oauth_token'

    DEFAULT_SOLVEBIO_DOMAIN = 'https://my.solvebio.com'

    def __init__(self, app, app_url, client_id,
                 solvebio_domain=DEFAULT_SOLVEBIO_DOMAIN):
        super(SolveBioAuth, self).__init__(app, app_url, client_id)

        self._solvebio_domain = solvebio_domain

    def html(self, script):
        return ('''
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>Log In</title>
            </head>
            <body>
              <div id="react-root"></div>
            </body>
            <script id="_auth-config" type="application/json">
            {}
            </script>
            <script type="text/javascript">{}</script>
            </html>
        '''.format(
            json.dumps({
                'oauth_client_id': self._oauth_client_id,
                'solvebio_domain': self._solvebio_domain,
                'requests_pathname_prefix':
                    self._app.config['requests_pathname_prefix']
            }),
            script)
        )

    def check_view_access(self, oauth_token):
        client = SolveClient(token=oauth_token, token_type='Bearer')
        try:
            client.User.retrieve()
            return True
        except:
            return False

    def login_api(self):
        oauth_token = flask.request.get_json()['access_token']
        client = SolveClient(token=oauth_token, token_type='Bearer')
        user = client.User.retrieve()
        response = flask.Response(
            json.dumps(user),
            mimetype='application/json',
            status=200
        )

        self.set_cookie(
            response=response,
            name='solvebio_oauth_token',
            value=oauth_token,
            max_age=None
        )

        return response
