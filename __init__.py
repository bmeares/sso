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
    from urllib.parse import quote
    from typing import Optional
    from fastapi import FastAPI, Response, Cookie, Header
    from starlette.config import Config
    from starlette.requests import Request
    from starlette.middleware.sessions import SessionMiddleware
    from starlette.responses import HTMLResponse, RedirectResponse
    from authlib.integrations.starlette_client import OAuth, OAuthError
    from .config import get_sso_config, GOOGLE_CONF_URL
    from meerschaum import get_connector

#    staging_port = get_sso_config('staging_port')

    prepend_path = get_sso_config('prepend')
    google_client_id = get_sso_config('google', 'id')
    google_client_secret = get_sso_config('google', 'secret')
    google_callback_slug = get_sso_config('google', 'callback')
#    google_callback_url_s = get_sso_config('google', 'callback_s')

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
    redirect_target = '/'

    @app.get(sso_google_path)
    async def login_sso(request: Request, referer: Optional[str] = Header(None)):
        redirect_full_uri = ':'.join(str(referer).split(':')[0:2]) 
        redirect_base_uri = '/'.join(redirect_full_uri.split('/')[0:3])
        redirect_uri = redirect_base_uri + google_callback_slug

        print(redirect_base_uri + ' -> ' + redirect_uri)

        return await oauth.google.authorize_redirect(request, redirect_uri)

    @app.get(sso_google_path + '/callback')
    async def google_callback(request: Request):
        token = await oauth.google.authorize_access_token(request)
        user = await oauth.google.parse_id_token(request, token)

        conn = get_connector('sql', 'wedding_s')
        q = f"SELECT address FROM \"people-with-contact-info\" WHERE email = '{user.email}'"
        address = quote(conn.value(q))

        response = RedirectResponse(redirect_target)
        response.set_cookie(key='login_name', value=quote(user.name))
        response.set_cookie(key='login_email', value=quote(user.email))
        response.set_cookie(key='login_address', value=address)
        return response

