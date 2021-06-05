#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8


from meerschaum.utils.prompt import prompt
from meerschaum.config import get_plugin_config, write_plugin_config
GOOGLE_CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
FACEBOOK_CONF_DICT = {
    'api_base_url': 'https://graph.facebook.com/v10.0/',
    'access_token_url': 'https://graph.facebook.com/v10.0/oauth/access_token',
    'authorize_url': 'https://www.facebook.com/v10.0/dialog/oauth',
    'userinfo_endpoint': 'me?fields=id,name,first_name,middle_name,last_name,email,website,gender,locale',
    #  'response_type': 'token',
    #  'state': "{st=state123abc,ds=123456789}",
}


def get_sso_config(*args, **kw):
    _cf = get_plugin_config(*args, warn=False, **{k:v for k in kw if k != 'warn'})
    if _cf is None:
        _prepend = prompt('Prepend path to /sso (blank for the root to be /sso):')
        _google_id = prompt('Google Client ID:')
        _google_secret = prompt('Google Client Secret:', is_password=True)
        _google_callback = prompt('Google Callback URL:')

        _facebook_id = prompt('Facebook App ID:')
        _facebook_secret = prompt('Facebook App Secret:')
        _facebook_callback = prompt('Facebook Callback URL:')

        _cf = {
            'prepend' : _prepend,
            'google' : {
                'id' : _google_id, 'secret' : _google_secret, 'callback' : _google_callback,
            },
            'facebook' : {
                'id' : _facebook_id, 'secret' : _facebook_secret, 'callback' : _facebook_callback,
            },
        }
        write_sso_config(_cf)
    return get_plugin_config(*args, **kw)

def write_sso_config(config, **kw):
    write_plugin_config(config)
