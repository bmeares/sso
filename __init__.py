#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
Meerschaum plugin to add SSO login functionality to the API.
"""

import json
from meerschaum.api import app
from fastapi import FastAPI
from starlette.config import Config
from starlette.requests import Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError
from .config import get_sso_config

prepend_path = get_sso_config('prepend')
google_client_id = get_sso_config('google', 'id')
google_client_secret = get_sso_config('google', 'secret')
google_callback_url = get_sso_config('google', 'callback')

GOOGLE_CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
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

required = ['authlib', 'httpx']
prepend_path = '/api'
sso_google_path = prepend_path + '/sso/google'

@app.get(sso_google_path)
async def login_sso(request: Request):
    #  redirect_uri = sso_google_path + '/callback'
    redirect_uri = google_callback_url
    print(redirect_uri)
    return await oauth.google.authorize_redirect(request, redirect_uri)
    #  return await google_sso.get_login_redirect()

@app.get(sso_google_path + '/callback')
async def google_callback(request: Request):
    #  print(request.cookies)
    #  user = await google_sso.verify_and_process(request)
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    return user
    #  return {'message' : 'success!'}
    #  return {
        #  "id": user.id,
        #  "picture": user.picture,
        #  "display_name": user.display_name,
        #  "email": user.email,
        #  "provider": user.provider,
    #  }

