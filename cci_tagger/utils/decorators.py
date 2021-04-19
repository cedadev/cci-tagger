# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '11 Feb 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

from functools import wraps
import pathlib

def fpath_as_pathlib(path_arg):
    """
    Decorator function to make sure that supplied file path is a pathlib.Path object
    :param f:
    :return:
    """
    def wrapper(f):
        @wraps(f)
        def wrapped(*f_args, **f_kwargs):

            # Get the path variable
            path_var = f_kwargs.get(path_arg)

            # Convert to path object if not already
            if not isinstance(path_var,pathlib.Path):
                f_kwargs[path_arg] = pathlib.Path(path_var)

            return f(*f_args, **f_kwargs)
        return wrapped
    return wrapper