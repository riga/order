# coding: utf-8

"""
Helpers for tests.
"""


__all__ = ["skip_if", "has_module"]


import functools
import importlib


def skip_if(b):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs) if not b else None
        return wrapper
    return decorator


def has_module(name):
    try:
        importlib.import_module(name)
    except ImportError:
        return False
    else:
        return True
