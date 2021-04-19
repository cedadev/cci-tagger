# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '04 Feb 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

import pathlib
from cci_tagger.conf import constants
from cci_tagger.file_handlers.handler_factory import HandlerFactory
import re
from cci_tagger.utils import fpath_as_pathlib
from cci_tagger.utils.snippets import get_file_subset
import logging
import verboselogs

verboselogs.install()
logger = logging.getLogger(__name__)


class Dataset(object):

    ESACCI = 'ESACCI'
    DRS_ESACCI = 'esacci'
    MULTIPLATFORM = False

    def __init__(self, dataset, dataset_json_mappings, facets):
        """

        :param dataset:
        :param dataset_json_mappings:
        """

        self.id = dataset
        self._facets = facets

        # File listing for the DRS datasets
        self.file_map = {}

        # Store all the tags which come from the dataset
        self.dataset_uris = {}

        self.not_found_messages = set()

        # JSON file loader
        self.dataset_json_mappings = dataset_json_mappings
        self.dataset_defaults = dataset_json_mappings.get_user_defined_defaults(dataset)
        self.dataset_mappings = dataset_json_mappings.get_user_defined_mapping(dataset)
        self.dataset_overrides = dataset_json_mappings.get_user_defined_overrides(dataset)

    def process_dataset(self, max_file_count=0):
        """
        Main entry point to process a dataset.

        The max file count kwarg can be used for testing on a smaller subset
        of files. When this parameter is set > 1, the file list is restricted
        to netCDF files.
        :param max_file_count: default: 0. How many netCDF files to try and scan (int)
        :return: URIs for each facet (dict), Files mapped to DRS ID (dict)
        """

        # Get a list of files in the dataset
        file_list = self._get_dataset_files(max_file_count)

        logger.info(f'Dataset: {self.id}\n Processing {len(file_list)} files')

        # There are no files
        if not file_list:
            logger.error(f'No files found for {self.id}')
            return

        for file in file_list:
            file_tags = self.get_file_tags(filepath=file)
            self._update_dataset_uris(file_tags)

            self._update_drs_filelist(file_tags, file)

        return self.dataset_uris, self.file_map # URIs for MOLES, {} of files organised into datasets

    def generate_ds_id(self, drs_facets, filepath):
        """
        Turn the drs labels into an identifier

        :param drs_facets: Bag of labels
        :param filepath: Filepath of the file to generate ID for. Used to
        match against filters.

        :return: ID
        """
        MISSING_VALUES = False

        ds_id = self.DRS_ESACCI

        for facet in constants.DRS_FACETS:

            facet_value = drs_facets.get(facet)

            if not facet_value:
                MISSING_VALUES = True
                if filepath.endswith(('.nc','.prj','.shp','.shx')):
                    logger.error(f'Missing DRS facet: {facet} in {self.id} for file: {filepath}')
                else:
                    logger.warning(f'Missing DRS facet: {facet} in {self.id} for file: {filepath}')


            else:

                facet_value = str(drs_facets[facet]).replace('.', '-')
                facet_value = facet_value.replace(' ', '-')
                facet_value = facet_value.replace('/', '-')

                if facet is constants.FREQUENCY:
                    facet_value = facet_value.replace('month', 'mon')
                    facet_value = facet_value.replace('year', 'yr')

                ds_id = f'{ds_id}.{facet_value}'

        # Get realisation
        realisation = self.dataset_json_mappings.get_dataset_realisation(self.id, filepath)
        dsid = f'{ds_id}.{realisation}'

        # Don't generate a DRS ID if there are missing values or
        # the files have been marked for exclusion from DRS
        if MISSING_VALUES or realisation == constants.EXCLUDE_REALISATION:
            return

        return dsid

    def get_drs_labels(self, drs_labels):
        """
        Convert the URIs into human readable labels for the DRS.

        :param uris: Labels generated from each URI (dict)
        :return: Label string for each facet (dict)
        """
        drs_labels = drs_labels.copy()

        for facet in drs_labels:
            # Add the multi labels
            if facet in constants.MULTILABELS:

                terms = drs_labels.get(facet)

                if terms:
                    if len(terms) > 1:
                        drs_labels[facet] = constants.MULTILABELS.get(facet)

                    # Platform is a little different because there can be 1 URI
                    # but that could be from a programme which contains multiple
                    # platforms
                    elif facet is constants.PLATFORM and self.MULTIPLATFORM:
                        drs_labels[facet] = constants.MULTILABELS.get(facet)

                    # Convert single item lists into a string
                    else:
                        drs_labels[facet] = drs_labels[facet][0]

            # Make sure facet values are strings not lists
            elif type(drs_labels[facet]) is list:
                if drs_labels[facet]:
                    drs_labels[facet] = drs_labels[facet][0]

        return drs_labels

    @fpath_as_pathlib('filepath')
    def get_file_tags(self, filepath):
        """
        Extract the URIs from the vocab server which matches the terms
        found in the file path and the file metadata.

        The file must be a pathlib.Path object so is checked by a decorator.
        :param file: Filepath (str | pathlib.Path)
        :return: URIs (dict)
        """
        # Set the multi platform flag
        self.MULTIPLATFORM = False

        # Get default tags
        file_tags = self.dataset_defaults.copy()

        # Get tags from filepath
        tags_from_filename = self._parse_file_name(filepath)
        file_tags.update(tags_from_filename)

        # Get tags from file metadata
        tags_from_metadata = self._scan_file(filepath, file_tags)

        # Process file tags from the metadata for multivalues
        processed_labels = self._process_file_attributes(tags_from_metadata)
        file_tags.update(processed_labels)

        # Apply mappings
        mapped_values = self._apply_mapping(file_tags)

        # Apply any overrides
        mapped_values = self._apply_overrides(mapped_values)

        # convert tags to URIs
        uris = self._convert_terms_to_uris(mapped_values)

        return uris

    def _apply_mapping(self, file_tags):
        """
        Take set of file tags and map them based on user JSON files

        :param file_tags: Tags extracted from the files
        :return: Bag of mapped tags
        """
        mapped_values = {}

        for facet, values in file_tags.items():

            if type(values) is list:
                mapped_values[facet] = [self._get_mapping(facet, val) for val in values]

            elif type(values) is str:
                mapped_values[facet] = [self._get_mapping(facet, values)]

        return mapped_values

    def _apply_overrides(self, mapped_tags):
        """
        Apply any hard overrides which have been defined in the JSON files.
        This will take it as is, so you will need to make sure that overrides are
        legit!

        :param mapped_tags: Fields to apply overrides to
        :return: mapped_tags with overrides applies (dict)
        """

        if self.dataset_overrides:
            for facet, value in self.dataset_overrides.items():
                mapped_tags[facet] = value

        return mapped_tags

    def _convert_terms_to_uris(self, mapped_labels):
        """
        Get the terms which have been extracted from the file and turn them
        into a bag or URIs which have been validated by the vocab server.

        :param mapped_labels: Mapped labels
        :return:
        """

        uri_bag = {}

        # Filename facets
        for facet in [constants.PROCESSING_LEVEL, constants.ECV, constants.DATA_TYPE, constants.PRODUCT_STRING]:
            # Get the terms
            terms = mapped_labels.get(facet)

            if terms:
                # Make sure input is a list
                if type(terms) is str:
                    terms = [terms]

                # Retrieve set of URIs. Put them in a set to remove duplicates
                uris = set()
                for term in terms:

                    # Clean any leading/trailing whitespace
                    term = term.strip()

                    # Get the URI for the term
                    uri = self._get_term_uri(facet, term)
                    if uri:
                        uris.add(uri)
                    else:
                        self._log_attr_not_found(facet, term)

                    # Add broader terms for processing level
                    if facet is constants.PROCESSING_LEVEL:
                        broader_proc_level_uri = self._facets.get_broader_proc_level(uri)

                        if broader_proc_level_uri:
                            uri_bag[constants.BROADER_PROCESSING_LEVEL] = {broader_proc_level_uri}

                if uris:
                    uri_bag[facet] = uris

        # Metadata facets
        for facet in constants.ALLOWED_GLOBAL_ATTRS:

            # If processing level is 2, FREQUENCY has a set value
            if facet is constants.FREQUENCY:
                proc_level = mapped_labels.get(constants.PROCESSING_LEVEL, [])
                proc_test = [bool('2' in item) for item in proc_level]

                if proc_level and any(proc_test):
                    uri_bag[constants.FREQUENCY] = {constants.LEVEL_2_FREQUENCY}
                    continue

            terms = mapped_labels.get(facet)

            if terms:
                # Make sure input is a list
                if type(terms) is str:
                    terms = [terms]

                uris = set()
                for term in terms:

                    # Strip any trailing/leading whitespace
                    term = term.strip()

                    # Ignore N/A values
                    if term == 'N/A':
                        continue

                    # Get the URI from the vocab service
                    uri = self._get_term_uri(facet, term)

                    if uri:
                        uris.add(uri)

                        if facet is constants.PLATFORM:
                            # Add the broader terms
                            plt_group = self._get_programme_group(uri)
                            if plt_group:
                                group_from_bag = uri_bag.get(constants.PLATFORM_GROUP, set())
                                group_from_bag.update(plt_group)
                                uri_bag[constants.PLATFORM_GROUP] = group_from_bag

                    # If platform does not return a URI try to get platform programmes tags
                    elif facet is constants.PLATFORM:
                        programme_tags = self._get_platform_as_programme(term)
                        if programme_tags:

                            # Update the multi-platform flag as we have added a group or
                            # programme to this list. Even if that results in a single
                            # URI, it encompasses > 1 platform
                            self.MULTIPLATFORM = True
                            uris.update(programme_tags)

                        else:
                            # Programme tags not found for term
                            self._log_attr_not_found(facet, term)

                    else:
                        # URI not found for term
                        self._log_attr_not_found(facet, term)

                if uris:
                    uri_bag[facet] = uris

        # Add product version
        if mapped_labels.get(constants.PRODUCT_VERSION):
            uri_bag[constants.PRODUCT_VERSION] = mapped_labels[constants.PRODUCT_VERSION]

        return uri_bag


    @staticmethod
    def _get_data_from_filename1(file_segments):
        """
        Extract data from the file name of form 1.

        @param file_segments (List(str)): file segments

        @return a dict where:
                key = facet name
                value = file segment

        """
        return {
            constants.PROCESSING_LEVEL: file_segments[2].split('_')[0],
            constants.ECV: file_segments[2].split('_')[1],
            constants.DATA_TYPE: file_segments[3],
            constants.PRODUCT_STRING: file_segments[4]
        }

    @staticmethod
    def _get_data_from_filename2(file_segments):
        """
        Extract data from the file name of form 2.

        @param file_segments (List(str)): file segments

        @return a dict where:
                key = facet name
                value = file segment

        """
        return {
            constants.PROCESSING_LEVEL: file_segments[2],
            constants.ECV: file_segments[1],
            constants.DATA_TYPE: file_segments[3],
            constants.PRODUCT_STRING: file_segments[4]
        }

    def _get_dataset_files(self, max_file_count):
        """
        Get files from the dataset. Will return a list including all file types
        unless the max_file_count parameter > 0. This assumes you are testing and
        are only interested in netCDF so will return the first n netCDF files

        :param max_file_count: Used for testing. Max number of netCDF files. Default: 0
        :return: list of files
        """
        path = pathlib.Path(self.id)

        # Can ask for all files because this returns a generator and has not done
        # any work yet.
        all_files = path.glob('**/*')

        if max_file_count > 0:
            # Only want a small number of netcdf files for testing
            all_netcdf = path.glob('**/*.nc')

            filelist = get_file_subset(all_netcdf, max_file_count)

            if not filelist:
                filelist = get_file_subset(all_files, max_file_count)

            return filelist

        # Return all files from the dataset recursively
        return [item for item in all_files if item.is_file()]

    def _get_mapping(self, facet, term):
        """
        Convert the term to lower case and get the mapped value from the
        user JSON files. Will return the original term in lowercase if no
        mapping is found.

        :param facet: The facet to match against (string)
        :param term: The term to be mapped (string)
        :return: Mapped term or lowercase term (string)
        """

        # Make sure term is lowercase and remove any whitespace
        term = term.lower().strip()

        # Check to see if there are any mappings for this facet in this dataset
        facet_map = self.dataset_mappings.get(facet)

        if facet_map:

            # Loop through the possible mappings and match the lowercase
            # term against he lowercase key in the mapping to remove
            # ambiguity.
            for key in facet_map:
                if term == key.lower():
                    return facet_map[key].lower()

        return term

    def _get_platform_as_programme(self, platform):
        tags = []

        # check if the platform is really a platform programme
        if platform in self._facets.get_programme_labels():
            programme_uri = self._get_term_uri(constants.PLATFORM_PROGRAMME, platform)
            tags.append(programme_uri)

            try:
                group = self._facets.get_programmes_group(programme_uri)
                if group:
                    group_uri = self._get_term_uri(constants.PLATFORM_GROUP, group)
                    tags.append(group_uri)

            except KeyError:
                # not all programmes have groups
                pass

        # check if the platform is really a platform group
        elif platform in self._facets.get_group_labels():
            group_uri = self._get_term_uri(constants.PLATFORM_GROUP, platform)
            tags.append(group_uri)

        return tags

    def _get_programme_group(self, term_uri):
        # now add the platform programme and group
        tags = []

        programme = self._facets.get_platforms_programme(term_uri)
        if programme:
            programme_uri = self._get_term_uri(constants.PLATFORM_PROGRAMME, programme)
            tags.append(programme_uri)

            group = self._facets.get_programmes_group(programme_uri)
            if group:
                group_uri = self._get_term_uri(constants.PLATFORM_GROUP, group)
                tags.append(group_uri)

        return tags

    def _get_term_uri(self, facet, term):
        """
        Take the term and return the URI from the Vocab service
        :param facet: global attribute, facet
        :param term: The term to check against the vocab service
        :return: The correct URI for the term
        """

        facet = facet.lower()
        term_l = term.lower()

        # Check the pref labels
        if term_l in self._facets.get_labels(facet):
            return self._facets.get_labels(facet)[term_l].uri

        # Check the alt labels
        elif term_l in self._facets.get_alt_labels(facet):
            return self._facets.get_alt_labels(facet)[term_l].uri

    def _log_attr_not_found(self, facet, term):
        """
        Create a log and record the term not found in the vocab server
        This is used to create a report of all the terms not in the vocab server

        :param facet: (str) Facet being processed
        :param term: (str) term being processed
        """
        self.not_found_messages.add(f'{facet}: {term}')
        logger.warning(f'Invalid value: {term} in dataset: {self.id} for attribute: {facet}')

    def _parse_file_name(self, fpath):
        """
        Extract data from the file name.

        The file name comes in two different formats. The values are '-'
        delimited.
        Form 1
            <Indicative Date>[<Indicative Time>]-ESACCI
            -<Processing Level>_<CCI Project>-<Data Type>-<Product String>
            [-<Additional Segregator>][-v<GDS version>]-fv<File version>.nc
        Form 2
            ESACCI-<CCI Project>-<Processing Level>-<Data Type>-
            <Product String>[-<Additional Segregator>]-
            <IndicativeDate>[<Indicative Time>]-fv<File version>.nc

        Values extracted from the file name:
            Processing Level
            CCI Project (ecv)
            Data Type
            Product String

        @param ds (str): the full path to the dataset
        @param fpath (str): the path to the file

        @return drs and csv representations of the data

        """

        file_segments = fpath.name.split('-')

        if len(file_segments) < 5:
            logger.error(f'Invalid filename format in dataset: {self.id} for file {fpath.name}')
            return {}

        if file_segments[1] == self.ESACCI:
            return self._get_data_from_filename1(file_segments)

        elif file_segments[0] == self.ESACCI:
            return self._get_data_from_filename2(file_segments)

        # There was an error, unable to extract any tags
        logger.error(f'Invalid filename format in dataset: {self.id} for file {fpath.name}')
        return {}

    def _process_file_attributes(self, file_attributes):

        for global_attr in constants.ALLOWED_GLOBAL_ATTRS:
            # Get the file attribute for the given global attr
            attr = file_attributes.get(global_attr)

            # If the global attribute does not exist for this file,
            # Check defaults
            # continue
            if not attr:

                # Check user defaults for a value in this field
                if self.dataset_defaults.get(global_attr):
                    attr = self.dataset_defaults.get(global_attr)
                else:
                    continue

            # Get merged mapping fields
            attr = self.dataset_json_mappings.get_merged_attribute(self.id, attr)

            # Split based on separator
            if global_attr is constants.PLATFORM and '<' in attr:
                bits = attr.split(', ')

            elif isinstance(attr, list):
                bits = attr

            else:
                # Can separate based on ; or ,
                if isinstance(attr, str):
                    bits = re.split(r'[;,]{1}', attr)
                else:
                    logger.error(f'Could not process attribute from {global_attr} in {self.id}. Got {attr}, expected string or list')

            # Deal with multiplatforms
            if global_attr is constants.PLATFORM:
                bits = self._split_multiplatforms(bits)

            # Replace input attributes with output from scanning process
            file_attributes[global_attr] = bits

        return file_attributes

    def _scan_file(self, filename, file_tags):
        """
        Scan the file and extract tags from the metadata
        :param filename:
        :return:
        """
        labels = {}
        proc_level = file_tags.get(constants.PROCESSING_LEVEL)

        # File specific parser
        handler = HandlerFactory.get_handler(filename.suffix)

        if handler:
            labels = handler(filename).extract_facet_labels(proc_level)

        return labels

    @staticmethod
    def _split_multiplatforms(segments):
        """
        Take a string like ERS-<1,2> and return
        ['ERS-1','ERS-2']

        :param segment: String
        :return: list of components
        """
        split_segments = []
        pattern = re.compile(r'(.*-)<(.*)>.*')

        for segment in segments:

            m = re.match(pattern, segment)
            if m:
                term = m.group(1)
                values = m.group(2).split(',')

                split_segments.extend([f'{term}{val}' for val in values])

            else:
                split_segments.append(segment)

        return split_segments

    def _update_dataset_uris(self, tags):
        """
        Update the set containing all the URIs extracted from the dataset

        :param tags: (dict) URI tags
        """

        for facet, values in tags.items():

            if facet in self.dataset_uris:
                self.dataset_uris[facet].update(values)
            else:
                self.dataset_uris[facet] = set(values)

    def _update_drs_filelist(self, tags, file):
        """
        Update the drs filelists
        :param tags: URIs
        :param drs_files: dictionary to store the state
        :param file: The file to add to the dataset
        """
        # Convert file from pathlib to posix string
        file = file.as_posix()

        labels = self._facets.process_bag(tags)
        drs_labels = self.get_drs_labels(labels)
        ds_id = self.generate_ds_id(drs_labels, file)

        # Create a value where the DRS cannot be created
        if not ds_id:
            ds_id = f'UNKNOWN_DRS - {self.id}'

        if ds_id in self.file_map:
            self.file_map[ds_id].append(file)
        else:
            self.file_map[ds_id] = [file]
