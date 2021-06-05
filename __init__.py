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
    import hashlib
    from urllib.parse import quote
    from typing import Optional
    from fastapi import FastAPI, Response, Cookie, Header
    import httpx
    from starlette.config import Config
    from starlette.requests import Request
    from starlette.middleware.sessions import SessionMiddleware
    from starlette.responses import HTMLResponse, RedirectResponse
    from authlib.integrations.starlette_client import OAuth, OAuthError
    from .config import get_sso_config, GOOGLE_CONF_URL, FACEBOOK_CONF_DICT
    from meerschaum import get_connector
    from meerschaum.api import get_uvicorn_config

    canonical_host = get_sso_config('canonical_hostname')
    prepend_path = get_sso_config('prepend')
    google_client_id = get_sso_config('google', 'id')
    google_client_secret = get_sso_config('google', 'secret')
    google_callback_slug = get_sso_config('google', 'callback')
    facebook_app_id = get_sso_config('facebook', 'id')
    facebook_app_secret = get_sso_config('facebook', 'secret')
    facebook_callback_slug = get_sso_config('facebook', 'callback')

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
        redirect_uri=facebook_callback_slug,
        client_kwargs={
            'scope': 'email',
        },
        **FACEBOOK_CONF_DICT
    )
    app.add_middleware(SessionMiddleware, secret_key=google_client_secret)

    sso_google_path = prepend_path + '/sso/google'
    sso_facebook_path = prepend_path + '/sso/facebook'
    redirect_target = '/'

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
            "SELECT first, last, id FROM people "
            + f"WHERE first = '{fname}' AND last = '{lname}'"
        )
        print(q)

        if(conn.value(q) == None or True):
            fakeemail = fname + lname + '@mazlinandaaron.com'
            return fakeemail

        return conn.value(q)

    def get_host_from_referer(referer: Union[str, None]):
        """
        Parse the host section of a url from a full url referer.
        """
        if referer == None:
            return canonical_host
        redirect_full_uri = ':'.join(str(referer).split(':')[0:2]) 
        redirect_base_uri = '/'.join(redirect_full_uri.split('/')[0:3])
        return redirect_base_uri

    def record_login_hash(name: str, email: str):
        """
        Record the current login checksum to the database for validation calls later
        """
        conn = get_connector('sql', 'wedding_s')
        pattern = f'{quote(name)}TO{quote(email)}INTO{canonical_host}'
        print(pattern)
        result = hashlib.md5(pattern.encode()).hexdigest()

        login_exists = conn.value(f'SELECT * FROM session WHERE key="{result}"')
        if login_exists == None:
            conn.value(f'INSERT INTO session (key, login_email) VALUES("{result}", "{email}")')
            print(f'inserted key for user at {email}')

        return result

    @app.get(prepend_path)
    async def testConnection():
        return "<h1>SSO is alive</h1>"

    @app.get(sso_google_path)
    async def google_login(request: Request, referer: Optional[str] = Header(None)):
        redirect_base = get_host_from_referer(referer)
        redirect_uri = redirect_base + google_callback_slug
        if redirect_base.find('staging') != -1:
            print(str(referer) + ' -> ' + redirect_uri)
        return await oauth.google.authorize_redirect(request, redirect_uri)

    @app.get(sso_google_path + '/callback')
    async def google_callback(request: Request):
        token = await oauth.google.authorize_access_token(request)
        user = await oauth.google.parse_id_token(request, token)

        login_token = record_login_hash(user.name, user.email)

        response = RedirectResponse(redirect_target)
        response.set_cookie(key='login_provider', value='google', secure=True)
        response.set_cookie(key='login_name', value=quote(user.name), secure=True)
        response.set_cookie(key='login_email', value=quote(user.email), secure=True)
        response.set_cookie(key='login_id', value=login_token, secure=True)
        response.set_cookie(key='login_name_verified', value=True, secure=True)
        response.set_cookie(key='login_email_verified', value=True, secure=True)
        return response

    @app.get(sso_facebook_path)
    async def facebook_login(request: Request, referer: Optional[str] = Header(None)):
        redirect_base = get_host_from_referer(referer)
        redirect_uri = redirect_base + facebook_callback_slug
        if redirect_base.find('staging') != -1:
            print(str(referer) + ' -> ' + redirect_uri)
        return await oauth.facebook.authorize_redirect(request, redirect_uri)

    @app.get(sso_facebook_path + '/callback')
    async def facebook_callback(request: Request):
        token = await oauth.facebook.authorize_access_token(request)
        access_token = token.get('access_token', None)
        async with httpx.AsyncClient() as client:
            r = await client.get('https://graph.facebook.com/me?fields=id,name,email', params={'access_token': access_token})
        name_verified = True
        email_verified = False

        user_dict = r.json()
        name = user_dict.get('name', None)
        ### TODO handle missing name
        email = user_dict.get('email', None)
        if email == None:
            email = get_email_from_name(name) 
        else:
            email_verified = True
        ### TODO handle missing email

        login_token = record_login_hash(name, email if email != None else 'FB-NO-EMAIL')

        response = RedirectResponse(redirect_target)
        response.set_cookie(key='login_provider', value='facebook', secure=True)
        response.set_cookie(key='login_name', value=quote(name), secure=True)
        response.set_cookie(key='login_email', value=quote(email), secure=True)
        response.set_cookie(key='login_id', value=login_token, secure=True)
        response.set_cookie(key='login_name_verified', value=str(name_verified), secure=True)
        response.set_cookie(key='login_email_verified', value=str(email_verified), secure=True)
        return response

