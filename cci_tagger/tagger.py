'''
BSD Licence
Copyright (c) 2016, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
        this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
        this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.
    * Neither the name of the Science & Technology Facilities Council (STFC)
        nor the names of its contributors may be used to endorse or promote
        products derived from this software without specific prior written
        permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''

import json

from cci_tagger.conf.constants import ALLOWED_GLOBAL_ATTRS, SINGLE_VALUE_FACETS
from cci_tagger.facets import Facets
from cci_tagger.conf.settings import ESGF_DRS_FILE, MOLES_TAGS_FILE
from json_tagger import DatasetJSONMappings
from cci_tagger.dataset.dataset import Dataset
from cci_tagger.utils import TaggedDataset
import logging
import verboselogs
import json

verboselogs.install()


class ProcessDatasets(object):
    """
    This class provides the process_datasets method to process datasets,
    extract data from file names and from within net cdf files. It then
    produces files for input into MOLES and ESGF.

    Some data are extracted from the file name.

    The file name comes in two different formats. The values are '-'
    delimited.
    Format 1
        <Indicative Date>[<Indicative Time>]-ESACCI
        -<Processing Level>_<CCI Project>-<Data Type>-<Product String>
        [-<Additional Segregator>][-v<GDS version>]-fv<File version>.nc
    Format 2
        ESACCI-<CCI Project>-<Processing Level>-<Data Type>-
        <Product String>[-<Additional Segregator>]-
        <IndicativeDate>[<Indicative Time>]-fv<File version>.nc

    Values extracted from the file name:
        Processing Level
        CCI Project (ecv)
        Data Type
        Product String

    Other data are extracted from the net cdf file attributes.
        time frequency
        sensor id
        platform id
        product version
        institute

    The DRS is made up of:
        project (hard coded "esacci")
        cci_project
        time frequency
        processing level
        data type
        sensor id
        platform id
        product string
        product version
        realization
        version (current date)

    Realization is used to distinguish between DRS that would otherwise be
    identical. When determining the realisation a file of mappings of dataset
    names to DRS is consulted. If the data set already exists in the list then
    the existing realisation value is reused.

    """
    ESACCI = 'ESACCI'
    DRS_ESACCI = 'esacci'

    # an instance of the facets class
    __facets = None

    __moles_facets = SINGLE_VALUE_FACETS + ALLOWED_GLOBAL_ATTRS

    def __init__(self, suppress_file_output=False,
                 json_files=None, facet_json=None, **kwargs):
        """
        Initialise the ProcessDatasets class.

        @param suppress_file_output (boolean): Whether or not to write out moles tags
        @param json_files (iterable): collection of JSON files to load
        @param facet_json (string): filepath to JSON file which contains a dump of the facet object
                to save time when loading the tagger

        """
        self.logger = logging.getLogger(__name__)
        self.__suppress_fo = suppress_file_output

        if facet_json:
            with open(facet_json, 'r') as reader:
                self.__facets = Facets.from_json(json.load(reader))
                print(self.__facets)
        else:
            self.__facets = Facets()

        self.__file_drs = None
        self.__file_csv = None
        self._open_files()
        self.__not_found_messages = set()
        self.__error_messages = set()
        self.__dataset_json_values = DatasetJSONMappings(json_files)

    def _check_property_value(self, value, labels, facet, defaults_source):
        if value not in labels:
            print ('ERROR "{value}" in {file} is not a valid value for '
                   '{facet}. Should be one of {labels}.'.
                   format(value=value, file=defaults_source,
                          facet=facet, labels=', '.join(sorted(labels))))
            exit(1)
        return True

    def get_dataset(self, dspath):
        """
        Return a dataset object for the requested path
        :param dspath: Path to the dataset
        :return: Dataset
        """

        dataset_id = self.__dataset_json_values.get_dataset(dspath)
        return Dataset(dataset_id, self.__dataset_json_values, self.__facets)

    def process_datasets(self, datasets, max_file_count=0):
        """
        Loop through the datasets pulling out data from file names and from
        within net cdf files.

        @param datasets (List(str)): a list of dataset names, these are the
        full paths to the datasets
        @param max_file_count (int): how many .nc files to look at per dataset.
                If the value is less than 1 then all datasets will be
                processed.

        """

        ds_len = len(datasets)
        self.logger.info(f'Processing a maximum of {max_file_count if max_file_count > 0 else "unlimited"} files for each of {ds_len} datasets')

        # A sanity check to let you see what files are being included in each dataset
        dataset_file_mapping = {}
        terms_not_found = set()

        for dspath in sorted(datasets):

            dataset = self.get_dataset(dspath)

            dataset_uris, ds_file_map = dataset.process_dataset(max_file_count)

            self._write_moles_tags(dataset.id, dataset_uris)

            dataset_file_mapping.update(ds_file_map)

            terms_not_found.update(dataset.not_found_messages)

        self._write_json(dataset_file_mapping)

        if len(terms_not_found) > 0:
            print("\nSUMMARY OF TERMS NOT IN THE VOCAB:\n")
            for message in sorted(terms_not_found):
                print(message)

        self._close_files()

    def get_file_tags(self, fpath):
        """
        Extracts the facet labels from the tags
        USED BY THE FACET SCANNER FOR THE CCI PROJECT
        :param fpath: Path the file to scan
        :return: drs identifier (string), facet labels (dict)
        """

        # Get the dataset
        dataset = self.get_dataset(fpath)

        # Get the URIs for the datset
        uris = dataset.get_file_tags(filepath=fpath)

        # Turn uris into human readable tags
        tags = self.__facets.process_bag(uris)

        # Get DRS labels
        drs_facets = dataset.get_drs_labels(tags)

        # Generate DRS id
        drs = dataset.generate_ds_id(drs_facets, fpath)

        return TaggedDataset(drs, tags, uris)

    def _write_moles_tags(self, ds, uris):
        """

        :param ds: Dataset (will be a file path)
        :param uris: Dictionary of extracted tags as URIS to the vocab service
        """

        for facet in self.__moles_facets:
            tags = uris.get(facet)
            if tags:
                self._write_moles_tags_out(ds, tags)

    def _write_moles_tags_out(self, ds, uris):

        if self.__suppress_fo:
            return
        else:
            for uri in uris:
                self.__file_csv.write(f'{ds},{uri}\n')

    def _write_json(self, drs):
        if self.__suppress_fo:
            return

        self.__file_drs.write(
            json.dumps(drs, sort_keys=True, indent=4, separators=(',', ': ')))

    def _open_files(self, ):
        # Do not open files if suppress output is true
        if self.__suppress_fo:
            return

        self.__file_csv = open(MOLES_TAGS_FILE, 'w')

        self.__file_drs = open(ESGF_DRS_FILE, 'w')

    def _close_files(self, ):
        if self.__suppress_fo:
            return

        self.__file_csv.close()

        self.__file_drs.close()


if __name__ == '__main__':
    import sys
    filename = sys.argv[1]
    pds = ProcessDatasets()
    tds = pds.get_file_tags(fpath=filename)
    print(tds)