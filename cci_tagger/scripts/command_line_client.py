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

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from datetime import datetime
from cci_tagger.conf.settings import ERROR_FILE, LOG_FORMAT
import json
import sys
import time
import logging
import verboselogs

from cci_tagger.tagger import ProcessDatasets

verboselogs.install()
logger = logging.getLogger()

# Set up ERROR file log handler
fh = logging.FileHandler(ERROR_FILE)
fh.setLevel(logging.ERROR)
LOG_FORMATTER = logging.Formatter(LOG_FORMAT)
fh.setFormatter(LOG_FORMATTER)

logger.addHandler(fh)

def get_logging_level(verbosity):

    map = {
        1: logging.INFO,
        2: verboselogs.VERBOSE,
        3: logging.DEBUG
    }

    if verbosity > max(map):
        verbosity = max(map)

    return map.get(verbosity,logging.ERROR)


def get_datasets_from_file(file_name):
    """
    Get a list of datasets from the given file.

    @param file_name (str): the name of the file containing the list of
            datasets to process

    @return a List(str) of datasets

    """
    datasets = set()
    with open(file_name) as reader:
        for ds in reader.readlines():
            datasets.add(ds.strip())

    return datasets


def read_json_file(file_name):
    """
    Get the contents from the given json file.

    @param file_name (str): the name of the json file

    @return the contents of the json file

    """

    with open(file_name) as json_data:
        data = json.load(json_data)

    return data


class CCITaggerCommandLineClient(object):

    @staticmethod
    def parse_command_line():
        parser = ArgumentParser(
            description='Tag observations. You can tag an individual dataset, '
            'or tag all the datasets'
            '\nlisted in a file.',
            epilog='\n\nA number of files are produced as output:'
            '\n  esgf_drs.json contains a list of DRS and associated files '
            'and check sums'
            '\n  moles_tags.csv contains a list of dataset paths and '
            'vocabulary URLs'
            '\n  error.txt contains a list of errors'
            '\n\nExamples:'
            '\n  moles_esgf_tag -d /neodc/esacci/cloud/data/L3C/avhrr_noaa-16 '
            '-v'
            '\n  moles_esgf_tag -f datapath --file_count 2 -v'
            '\n  moles_esgf_tag -j example.json -v'
            '\n  moles_esgf_tag -s',
            formatter_class=RawDescriptionHelpFormatter)

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '-d', '--dataset',
            help=('the full path to the dataset that is to be tagged. This '
                  'option is used to tag a single dataset.')
        )
        group.add_argument(
            '-f', '--file',
            help=('the name of the file containing a list of datasets to '
                  'process. This option is used for tagging one or more '
                  'datasets.')
        )
        group.add_argument(
            '-j', '--json_file',
            action='append',
            help=('Use the JSON file to provide a list of datasets and also provide the mappings'
                  'which are used by the tagging code. Useful to test datsets and specific mapping files')
        )

        parser.add_argument(
            '--file_count',
            help='how many .nc files to look at per dataset',
            type=int, default=0
        )
        parser.add_argument(
            '-v', '--verbose', action='count',
            help='increase output verbosity',
            default=0
        )

        args = parser.parse_args()
        datasets = None

        # Set logging level
        logger.setLevel(get_logging_level(args.verbose))

        # Set up console logger
        ch = logging.StreamHandler()
        ch.setLevel(logger.level)
        ch.setFormatter(LOG_FORMATTER)

        logger.addHandler(ch)


        start_time = time.strftime("%H:%M:%S")

        # Read datasets from the command line
        if args.dataset is not None:
            datasets = {args.dataset}

        # Read list of datasets from a file
        elif args.file is not None:
            datasets = get_datasets_from_file(args.file)

        # Given a json file, get the datasets from the datasets key
        elif args.json_file is not None:

            datasets = []
            for file in args.json_file:
                json_data = read_json_file(file)

                if json_data.get("datasets"):
                    datasets.extend(json_data["datasets"])

        # Print start time based on verbosity
        if logger.level <= logging.INFO:
            print(f"\n{start_time} STARTED")
            if args.dataset:
                print(f'Processing {args.dataset}')

        return datasets, args

    @classmethod
    def main(cls):
        start_time = datetime.now()

        # Get the command line arguments
        datasets, args = cls.parse_command_line()

        # Quit of there are no datasets
        if not datasets:
            print('You have not provided any datasets')
            sys.exit(0)

        if args.json_file:
            json_file = args.json_file
        else:
            json_file = None

        pds = ProcessDatasets(json_files=json_file)
        pds.process_datasets(datasets, args.file_count)

        if logger.level <= logging.INFO:
            print(f'\n{time.strftime("%H:%M:%S")} FINISHED\n\n')
            end_time = datetime.now()
            time_diff = end_time - start_time
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f'Time taken {hours:02d}:{minutes:02d}:{seconds:02d}')

        exit(0)


if __name__ == "__main__":
    CCITaggerCommandLineClient.main()
