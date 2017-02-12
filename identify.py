#!/usr/bin/env python
# -*- coding: UTF-8 -*-


import tornado.web
import functools

def identify(roles=None):
    def deco_(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.current_user:
                raise tornado.web.HTTPError(403, reason="missing user")
            if isinstance(roles, str):
                if self.current_user.role == roles:
                    return func(*args, **kwargs)
            elif isinstance(roles, list):
                if self.current_user.role in roles:
                    return func(self, *args, **kwargs)
            else:
                raise tornado.web.HTTPError(403, reason="unauthurized")
        return wrapper
    return deco_
                


