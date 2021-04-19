# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '28 Jan 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

import unittest
from cci_tagger.dataset.dataset_tree import DatasetJSONMappings


class TestDatasetTree(unittest.TestCase):
    TEST_FILE = './test_json_files'
    EXPECTED = {
        '/path/1/a/b/c': {
            'dataset': '/path/1',
            'mapping': {
                "ecv": {
                    "GHRSST": "sea surface temperature"
                },
                "freq": {
                    "daily": "day",
                    "P01D": "day"
                },
                "institute": {
                    "DTU Space - Div. of Geodynamics": "DTU Space",
                    "DTU Space - Div. of Geodynamics and NERSC": "DTU Space"
                },
                "level": {
                    "level-3": "l3"
                },
                "platform": {
                    "ERS2": "ERS-2",
                    "ENV": "ENVISAT"
                },
                "sensor": {
                    "AMSR-E": "AMSRE",
                    "ATSR2": "ATSR-2"
                },
                "version": {
                    "03.02.": "03.02"
                }
            },
            'defaults': {
                "platform": "Nimbus-7",
                "sensor": "MERIS"
            },
            'realisation': 'r2',
            'overrides': {
                "freq": "day"
            }
        },

        '/path/2/ab/c': {
            'dataset': '/path/2',
            'mapping': {
                "ecv": {
                    "GHRSST": "sea surface temperature"
                },
                "freq": {
                    "daily": "day",
                    "P01D": "day"
                },
                "institute": {
                    "DTU Space - Div. of Geodynamics": "DTU Space",
                    "DTU Space - Div. of Geodynamics and NERSC": "DTU Space"
                },
                "level": {
                    "level-3": "l3"
                },
                "platform": {
                    "ERS2": "ERS-2",
                    "ENV": "ENVISAT"
                },
                "sensor": {
                    "AMSR-E": "AMSRE",
                    "ATSR2": "ATSR-2"
                },
                "version": {
                    "03.02.": "03.02"
                }
            },
            'defaults': {
                "platform": "Nimbus-7",
                "sensor": "MERIS"
            },
            'realisation': 'r1',
            'overrides': {
                "freq": "day"
            }
        },
        '/path/3/abx': {
            'dataset': None,
            'mapping': None,
            'defaults': None,
            'realisation': 'r1',
            'overrides': None
        }
    }

    @classmethod
    def setUpClass(cls):
        cls.tree = DatasetJSONMappings(cls.TEST_FILE)

    def test_get_dataset(self):

        for path in self.EXPECTED:
            ds = self.tree.get_dataset(path)
            self.assertEqual(ds, self.EXPECTED[path]['dataset'])

    def test_get_user_defined_mapping(self):

        for path in self.EXPECTED:
            mapping = self.tree.get_user_defined_mapping(self.EXPECTED[path]['dataset'])

            expected = self.EXPECTED[path]['mapping']
            if expected:
                self.assertDictEqual(mapping, expected)
            else:
                self.assertIsNone(mapping)

    def test_get_user_defined_defaults(self):

        for path in self.EXPECTED:
            defaults = self.tree.get_user_defined_defaults(self.EXPECTED[path]['dataset'])

            expected = self.EXPECTED[path]['defaults']
            if expected:
                self.assertDictEqual(defaults, expected)
            else:
                self.assertIsNone(defaults)

    def test_get_user_defined_overrides(self):

        for path in self.EXPECTED:
            overrides = self.tree.get_user_defined_overrides(self.EXPECTED[path]['dataset'])

            expected = self.EXPECTED[path]['overrides']
            if expected:
                self.assertDictEqual(overrides, expected)
            else:
                self.assertIsNone(overrides)

    def test_get_dataset_realisation(self):

        for path in self.EXPECTED:
            realisation = self.tree.get_dataset_realisation(self.EXPECTED[path]['dataset'])
            self.assertEqual(realisation, self.EXPECTED[path]['realisation'])

if __name__ == '__main__':
    unittest.main()