# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '30 Jul 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

from cci_tagger.facets import Facets
import argparse
import json


def get_args():
    parser = argparse.ArgumentParser('Dump facet object for use by lotus')
    parser.add_argument('output', help='Output file')
    return parser.parse_args()


def main():
    args = get_args()
    facets = Facets()

    with open(args.output, 'w') as writer:
        json.dump(facets.to_json(), writer)


if __name__ == '__main__':
    main()
