#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8


from meerschaum.utils.prompt import prompt
from meerschaum.config import get_plugin_config, write_plugin_config
GOOGLE_CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'

def get_sso_config(*args, **kw):
    _cf = get_plugin_config(*args, warn=False, **{k:v for k in kw if k != 'warn'})
    if not _cf:
        _prepend = prompt('Prepend path to /sso (blank for the root to be /sso):')
        _id = prompt('Google Client ID:')
        _secret = prompt('Google Client Secret:', is_password=True)
        _callback = prompt('Google Callback URL:')
        _cf = {
            'prepend' : _prepend,
            'google' : {
                'id' : _id, 'secret' : _secret, 'callback' : _callback
            },
        }
        write_sso_config(_cf)
    return get_plugin_config(*args, **kw)

def write_sso_config(config, **kw):
    write_plugin_config(config)
