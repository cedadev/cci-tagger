# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '05 Feb 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

from abc import ABC, abstractmethod


class FileHandler(ABC):

    @abstractmethod
    def extract_facet_labels(self, proc_level):
        return
