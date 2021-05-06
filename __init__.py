#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
Meerschaum plugin to add SSO login functionality to the API.
"""

from meerschaum.api import app
from .config import get_sso_config
from fastapi_sso.sso.google import GoogleSSO
from starlette.requests import Request
client_id = '60263884711-6a9e84d0eii8epp9mokc7lfv6a0kpmnd.apps.googleusercontent.com'
client_secret = 'fUTLiqLkAmfq0oi8nmyTvryz'

google_client_id = get_sso_config('google', 'id')
google_client_secret = get_sso_config('google', 'secret')
google_sso = GoogleSSO(google_client_id, google_client_secret, 'http://localhost:8000/sso/google/callback')

required = ['fastapi-sso']

@app.get('/sso/google')
async def test_sso():
    return await google_sso.get_login_redirect()

@app.get('/sso/google/callback')
async def google_callback(request: Request):
    print(request.cookies)
    user = await google_sso.verify_and_process(request)
    return {'message' : 'success!'}
    #  return {
        #  "id": user.id,
        #  "picture": user.picture,
        #  "display_name": user.display_name,
        #  "email": user.email,
        #  "provider": user.provider,
    #  }

