#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8


from meerschaum.utils.prompt import prompt
from meerschaum.config import get_plugin_config, write_plugin_config

def get_sso_config(*args, **kw):
    _cf = get_plugin_config(*args, warn=False, **{k:v for k in kw if k != 'warn'})
    if not _cf:
        _id = prompt('Google Client ID:')
        _secret = prompt('Google Client Secret:', is_password=True)
        _cf = {'google' : {'id' : _id, 'secret' : _secret}}
        write_sso_config(_cf)
    return get_plugin_config(*args, **kw)

def write_sso_config(config, **kw):
    write_plugin_config(config)
