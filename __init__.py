#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
Meerschaum plugin to add SSO login functionality to the API.
"""

__version__ = '0.0.1'
required = ['authlib', 'httpx',]
from meerschaum.plugins import api_plugin
from typing import Union

@api_plugin
def init(app):
    import json
    import httpx
    from fastapi import FastAPI
    from starlette.config import Config
    from starlette.requests import Request
    from starlette.middleware.sessions import SessionMiddleware
    from starlette.responses import HTMLResponse, RedirectResponse
    from authlib.integrations.starlette_client import OAuth, OAuthError
    from .config import get_sso_config, GOOGLE_CONF_URL, FACEBOOK_CONF_DICT
    from meerschaum import get_connector

    prepend_path = get_sso_config('prepend')
    google_client_id = get_sso_config('google', 'id')
    google_client_secret = get_sso_config('google', 'secret')
    google_callback_url = get_sso_config('google', 'callback')
    facebook_app_id = get_sso_config('facebook', 'id')
    facebook_app_secret = get_sso_config('facebook', 'secret')
    facebook_callback_url = get_sso_config('facebook', 'callback')

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
    oauth.register(
        name='facebook',
        client_id=facebook_app_id,
        client_secret=facebook_app_secret,
        redirect_uri=facebook_callback_url,
        client_kwargs={
            'scope': 'email',
        },
        **FACEBOOK_CONF_DICT
    )
    app.add_middleware(SessionMiddleware, secret_key=google_client_secret)

    sso_google_path = prepend_path + '/sso/google'
    sso_facebook_path = prepend_path + '/sso/facebook'

    def get_address_from_email(email: str) -> Union[str, None]:
        """
        Return a physical address linked to an email address.
        """
        conn = get_connector('sql', 'wedding_s')
        q = f"SELECT address FROM \"people-with-contact-info\" WHERE email = '{email}'"
        return conn.value(q)

    def get_email_from_name(name: str) -> Union[str, None]:
        """
        Return an email address from a real name.
        """
        conn = get_connector('sql', 'wedding_s')
        fname = name.split(' ')[0]
        lname = ' '.join(name.split(' ')[1:])
        q = (
            "SELECT email FROM \"people-with-contact-info\" "
            + f"WHERE first = '{fname}' AND last = '{lname}'"
        )
        return conn.value(q)

    @app.get(sso_google_path)
    async def google_login(request: Request):
        redirect_uri = google_callback_url
        return await oauth.google.authorize_redirect(request, redirect_uri)

    @app.get(sso_google_path + '/callback')
    async def google_callback(request: Request):
        token = await oauth.google.authorize_access_token(request)
        user = await oauth.google.parse_id_token(request, token)
        address = get_address_from_email(user.email)

        response = RedirectResponse('/login_success')
        response.set_cookie(key='login_name', value=user.name)
        response.set_cookie(key='login_email', value=user.email)
        response.set_cookie(key='login_address', value=address)
        return response

    @app.get(sso_facebook_path)
    async def facebook_login(request: Request):
        return await oauth.facebook.authorize_redirect(request, facebook_callback_url)

    @app.get(sso_facebook_path + '/callback')
    async def facebook_callback(request: Request):
        token = await oauth.facebook.authorize_access_token(request)
        print(token)
        access_token = token.get('access_token', None)
        async with httpx.AsyncClient() as client:
            r = await client.get('https://graph.facebook.com/me?fields=id,name,email', params={'access_token': access_token})
        user_dict = r.json()
        name = user_dict.get('name', None)
        ### TODO handle missing name
        email = get_email_from_name(name)
        ### TODO handle missing email
        address = get_address_from_email(str(email))

        response = RedirectResponse('/login_success')
        response.set_cookie(key='login_name', value=name)
        response.set_cookie(key='login_email', value=email)
        response.set_cookie(key='login_address', value=address)
        return response

