# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '19 Feb 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'


import argparse
import json
from cci_tagger.conf.constants import ALL_FACETS
from functools import wraps
from io import StringIO


class TextColours:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestResults:

    @property
    def errors(self):
        return len(self.get_errors())

    @property
    def failed(self):
        return bool(self.errors)

    @property
    def warnings(self):
        return len(self.get_warnings())

    def __init__(self, name):
        self.name = name
        self.REPORT = {}

    def __repr__(self):

        with StringIO('') as report:
            report.write(f'\n\t{TextColours.BOLD}TEST: {self.name}')
            if not self.errors:
                report.write(f'{TextColours.OKGREEN} ...OK')

            else:
                report.write(f'\n\n\t\t{TextColours.BOLD}{TextColours.FAIL}ERRORS: {self.errors}')
                report.write(f'\n\t\t{TextColours.BOLD}{TextColours.FAIL}---------')

                for error in self.get_errors():
                    report.write(f'\n\t\t{TextColours.FAIL}{error}')

            if self.warnings:
                report.write(f'{TextColours.BOLD}{TextColours.WARNING}\n\n\t\tWARNINGS: {self.warnings}')
                report.write(f'{TextColours.BOLD}{TextColours.WARNING}\n\t\t---------')

                for warning in self.get_warnings():
                    report.write(f'{TextColours.BOLD}{TextColours.WARNING}\n\t\t{warning}')

            report.write(TextColours.ENDC)
            content = report.getvalue()

        return content

    def add_error(self, message):
        """
        Add an error to the test report
        :param message: Message to add
        """
        if 'error' in self.REPORT:
            self.REPORT['errors'].append(message)
        else:
            self.REPORT['errors'] = [message]

    def add_warning(self, message):
        """
        Add a warning to the test report
        :param message: Message to add
        """

        if 'warning' in self.REPORT:
            self.REPORT['warnings'].append(message)
        else:
            self.REPORT['warnings'] = [message]

    def get_errors(self):
        """
        Return the list of errors
        :return:
        """
        return self.REPORT.get('errors',[])

    def get_warnings(self):
        """
        Return the list of warnings
        :return:
        """
        return self.REPORT.get('warnings',[])


def test_results(func):
    """
    :return:
    """
    @wraps(func)
    def wrapper(*args):
        test_results = TestResults(func.__name__)
        return func(*args, results=test_results)
    return wrapper


class TestJSONFile:

    REQUIRED_KEYS = {'datasets'}
    ACCEPTABLE_KEYS = {'datasets', 'filters', 'mappings', 'defaults', 'realisations', 'overrides', 'aggregations'}
    FILTER_KEYS = {'pattern','realisation'}
    FACET_KEYS = set(ALL_FACETS)

    def __init__(self, file, verbosity=0):
        self.file = file
        self.data = None
        self.verbosity = verbosity
        self.failed = False


    def _read_file(self):
        with open(self.file, encoding='utf-8') as reader:
            data = json.load(reader)
        return data

    @staticmethod
    def _check_type(label, object, expected, results):
        is_object = isinstance(object,expected)
        if not is_object:
            results.add_error(f'{label} object should be a {expected}. Got {type(object)} instead.')

        return is_object

    @staticmethod
    def _check_valid_keys(observed, expected, results):
        """
        Give some feedback on unexpected keys
        :param observed: Object which can be converted to set and provide list of observed values
        :param expected: Expected values
        """

        key_set = set(observed)

        diff = key_set.difference(expected)
        if diff:
            results.add_warning(f'Unexpected keys. {diff} will be ignored')

            if isinstance(observed, dict):
                for key in diff:
                    if observed.get(key):
                        results.add_error(f'Invalid key "{key}" has a value. This key will be ignored as it is invalid. If you are expecting to use this key, check the name.')

    @test_results
    def test_json_formatting(self, results):
        """
        Check whether file will load as correct JSON
        """

        try:
            self._read_file()
        except Exception as e:
            results.add_error(f'File format error - {e}')

        return results

    @test_results
    def test_json_keys(self, results):
        """
        Checks the top level keys and evaluates:
        - JSON file has all required keys
        - All keys are valid keys
        """
        keys_in_file = set(self.data.keys())

        # Check required key
        if not keys_in_file.issuperset(self.REQUIRED_KEYS):
            results.add_error(f'Required keys {self.REQUIRED_KEYS} not present')

        # Check for invalid keys
        unacceptable_keys = keys_in_file.difference(self.ACCEPTABLE_KEYS)
        if unacceptable_keys:
            results.add_error(f'Invalid sections. {unacceptable_keys} are not valid section keys')

        return results

    @test_results
    def test_datasets(self, results):
        """
        Checks that the datasets key and evaluates:
        - Datasets key returns a list
        - There is at least 1 dataset
        - Dataset values are strings
        """
        datasets = self.data.get('datasets')

        if datasets is None:
            return results

        # Check datasets key returns a list
        if not self._check_type('Datasets', datasets, list, results):
            return results

        # Check for at least one dataset
        if not datasets:
            results.add_error(f'There should be at least 1 dataset')

        # Check datasets are strings
        for dataset in datasets:
            if not isinstance(dataset, str):
                results.add_error(f'Datasets should be strings. {dataset} is not a string')

        return results

    @test_results
    def test_filters(self, results):
        """
        Checks that the filters key and evaluates:
         - Key returns a dict
         - Dataset filters match datasets listed
         - The dataset filters are a list of dicts
         - The dataset filters include the keys 'pattern' and 'realisation'
        """

        filters = self.data.get('filters')
        if filters is None:
            return results

        # Test key returns a dict
        if not self._check_type('Filters', filters, dict, results):
            return results

        # Test datasets match datasets listed
        filter_datasets = set(filters.keys())
        root_datasets = set(self.data.get('datasets',{}))

        if not filter_datasets.issubset(root_datasets):
            diff = filter_datasets.difference(root_datasets)
            results.add_error(f'Unexpected dataset. Filters should match to a dataset specified in datasets section. {diff} does not match')

        # Test filters are list of dicts
        for ds, filters in filters.items():

            is_list = isinstance(filters, list)
            if not is_list:
                results.add_error('Dataset filter should be a list. Check example_json')
                return results

            # Test dataset filters include required keys
            for filter in filters:
                filter_keys = set(filter.keys())

                if not filter_keys.issuperset(self.FILTER_KEYS):
                    diff = self.FILTER_KEYS.difference(filter_keys)
                    results.add_error(f'Missing required keys {diff}')

                diff = filter_keys.difference(self.FILTER_KEYS)
                if diff:
                    results.add_warning(f'Unexpected keys. {diff} will be ignored')

        return results

    @test_results
    def test_mappings(self, results):
        """
        Checks mappings key and evaluates:
        - Checks mapping section is dict
        - Checks all the keys listed are valid
        """
        mappings = self.data.get('mappings')
        if mappings is None:
            return results

        # Check mapping section is dict
        if not self._check_type('Mappings', mappings, dict, results):
            return results

        valid_mapping_keys = self.FACET_KEYS.union({'merged'})

        # Check all keys are valid
        self._check_valid_keys(mappings, valid_mapping_keys, results)

        return results

    @test_results
    def test_defaults(self, results):
        """
        Checks the defaults key and evaluates:
        - Check key returns a dictionary
        - Checks all the keys listed are valid
        - Checks values are strings
        """
        defaults = self.data.get('defaults')
        if defaults is None:
            return results

        # Check key returns a dict
        if not self._check_type('Defaults', defaults, dict, results):
            print(results.__dict__)
            return results

        # Check keys are valid
        self._check_valid_keys(defaults, self.FACET_KEYS, results)

        # Check values are strings
        for default in defaults:
            if not isinstance(default, str):
                results.add_error(f' Defaults should be strings. {default} is not a string')

        return results

    @test_results
    def test_realisations(self, results):
        """
        Checks the realisations key and evaluates:
        - Check realisation key returns a dict
        - All datasets listed are in the datasets section
        - Check all realisations are strings
        """
        realisations = self.data.get('realisations')
        if realisations is None:
            return results

        # Check if key returns a dict
        if not self._check_type('Realisations', realisations, dict, results):
            return results

        # Check datasets are listed in the main dataset section
        realisation_datasets = set(realisations.keys())
        root_datasets = set(self.data.get('datasets',{}))

        # Check all datasets are listed in datasets section
        if not realisation_datasets.issubset(root_datasets):
            diff = realisation_datasets.difference(root_datasets)
            results.add_error(f'Unexpected dataset. Realisation datasets should match to a dataset specified in datasets section. {diff} does not match')

        # Check all realisations are strings
        for realisation in realisations:
            if not isinstance(realisation, str):
                results.add_error(f'Realisations should be strings. {realisation} is not a string')

        return results

    @test_results
    def test_overrides(self, results):
        """
        Checks the overrides section and evaluates:
        - Check overrides returns a dict
        - All the keys listed are valid
        - All the key values are lists
        """
        overrides = self.data.get('overrides')
        if overrides is None:
            return results

        # Check overrides returns a dict
        if not self._check_type('Overrides', overrides, dict, results):
            return results

        # Check all keys listed are valid
        self._check_valid_keys(overrides, self.FACET_KEYS, results)

        return results

    @test_results
    def test_aggregations(self, results):
        """
        Checks the aggregations section
        - Check aggregations returns a list
        - Check each item of list is a dict
        - Check each dict has a pattern key
        - Check if each dict has a wms, that the value is a JSON. boolean
        :param results:
        :return:
        """

        aggregations = self.data.get('aggregations')

        if aggregations is None:
            return results

        # Check aggregations returns a list
        if not self._check_type('Aggregations', aggregations, list, results):
            return results

        # Check each item of list is a dict
        for agg_filter in aggregations:
            if not self._check_type('Aggregation filter', agg_filter, dict, results):
                return results

            # Check each dict has a pattern key
            self._check_valid_keys(agg_filter, ('pattern','wms'), results)

            if not agg_filter.get('pattern'):
                results.add_error(f'Aggregation filter does not have required key: "pattern"')

            # Check if each dict has a wms, that the value is a boolean
            if agg_filter.get('wms'):
                self._check_type('Aggregation WMS', agg_filter.get('wms'), bool, results)

        return results

    def run_test(self, callable):

        # Get the test
        test = getattr(self, callable)

        # Get the results
        results = test()

        # Display the results
        if results.failed or self.verbosity >0:
            print(results)

            if results.failed:
                self.failed = True

    def run(self):

        try:
            self.test_json_formatting()
        except Exception:
            print('CRITICAL: The file cannot be read so no other tests will work')
            raise

        # Load the data
        self.data = self._read_file()

        # Run the tests
        tests = [func for func in dir(self) if func.startswith('test_') and callable(getattr(self, func))]

        for test in tests:
            self.run_test(test)

    @classmethod
    def cmd(cls):
        parser = argparse.ArgumentParser(description='Check whether a given JSON file matches the expected format'
                                                     'to be used with the CCI tagger')

        parser.add_argument('json_file', help='JSON file to test', nargs='+')
        parser.add_argument('-v', '--verbose', help='Verbosity', action='count', default=0)

        args = parser.parse_args()

        files = args.json_file

        print(f'Found {len(files)} files')

        TEST_FAILED = False

        for file in files:
            print(f'\n\n{TextColours.BOLD}Testing {file}', end=" ")

            tjf = cls(file, verbosity=args.verbose)
            tjf.run()
            if not tjf.failed:
                print(f'{TextColours.OKGREEN}...OK{TextColours.ENDC}')
            else:
                TEST_FAILED = True
                print()

        if TEST_FAILED:
            exit(1)

if __name__ == '__main__':
    TestJSONFile.cmd()

