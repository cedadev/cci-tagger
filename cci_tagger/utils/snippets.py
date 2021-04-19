# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '13 Feb 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

from collections import namedtuple

def get_file_subset(path_gen, max_number):
    """
    Get a subset of file from a generator
    :param path_gen: pathlib.Path.glob
    :param max_number: int
    :return: list of pathlib.Path objects
    """

    filelist = []
    while len(filelist) < max_number:

        try:
            next_path = next(path_gen)
            if next_path.is_file():
                filelist.append(next_path)

        except StopIteration:
            break

    return filelist

TaggedDataset = namedtuple('TaggedDataset', ['drs','labels','uris'])

