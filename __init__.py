#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
Meerschaum plugin to add SSO login functionality to the API.
"""

__version__ = '0.0.1'
required = ['authlib', 'httpx']
from meerschaum.plugins import api_plugin

@api_plugin
def init(app):
    import json
    from fastapi import FastAPI
    from starlette.config import Config
    from starlette.requests import Request
    from starlette.middleware.sessions import SessionMiddleware
    from starlette.responses import HTMLResponse, RedirectResponse
    from authlib.integrations.starlette_client import OAuth, OAuthError
    from .config import get_sso_config, GOOGLE_CONF_URL
    from meerschaum import get_connector

    prepend_path = get_sso_config('prepend')
    google_client_id = get_sso_config('google', 'id')
    google_client_secret = get_sso_config('google', 'secret')
    google_callback_url = get_sso_config('google', 'callback')

    oauth = OAuth()
    oauth.register(
        name='google',
        client_id=google_client_id,
        client_secret=google_client_secret,
        server_metadata_url=GOOGLE_CONF_URL,
        client_kwargs={
            'scope': 'openid email profile',
        },
    )
    app.add_middleware(SessionMiddleware, secret_key=google_client_secret)

    sso_google_path = prepend_path + '/sso/google'

    @app.get(sso_google_path)
    async def login_sso(request: Request):
        redirect_uri = google_callback_url
        return await oauth.google.authorize_redirect(request, redirect_uri)

    @app.get(sso_google_path + '/callback')
    async def google_callback(request: Request):
        token = await oauth.google.authorize_access_token(request)
        user = await oauth.google.parse_id_token(request, token)

        conn = get_connector('sql', 'wedding_s')
        q = f"SELECT address FROM \"people-with-contact-info\" WHERE email = '{user.email}'"
        address = conn.value(q)

        response = RedirectResponse('/login_success')
        response.set_cookie(key='login_name', value=user.name)
        response.set_cookie(key='login_email', value=user.email)
        response.set_cookie(key='login_address', value=address)
        return response

