# encoding: utf-8
"""
This script creates a set of HTML pages to make it easy to scan through
the results from the tagging process and check that the right tags have made it through.
"""
__author__ = 'Richard Smith'
__date__ = '03 Mar 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

from elasticsearch import Elasticsearch
from configparser import ConfigParser
import argparse
import os
from elasticsearch.helpers import scan
from jinja2 import Environment, PackageLoader
from pathlib import Path
from tqdm import tqdm


class Dataset:
    FIELDS = [
        'collection_id',
        'parent_identifier',
        'title',
        'path',
        'start_date',
        'end_date',
        'bbox',
        'institute',
        'productVersion',
        'productString',
        'processingLevel',
        'dataType',
        'ecv',
        'sensor',
        'platform',
        'frequency',
        'aggregations',
        'drsId',

    ]

    def __init__(self, result, conf):
        source = result['_source']

        host = conf.get('elasticsearch', 'host')
        self.files_index = conf.get('elasticsearch', 'files_index')
        self.es = Elasticsearch([host], verify_certs=False)
        self.opensearch_fields = {}
        self.total_files = 0
        self.files_without_drs = 0

        for field in self.FIELDS:
            value = source.get(field)
            self.opensearch_fields[field] = value

        self._get_file_stats()

    def as_dict(self):
        return {
            'opensearch_fields': self.opensearch_fields,
            'total_files': self.total_files,
            'files_without_drs': self.files_without_drs
        }

    def _get_file_stats(self):
        base_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "projects.opensearch.datasetId.keyword": self.opensearch_fields['collection_id']
                            }
                        }
                    ]
                }
            }
        }

        self.total_files = self.es.count(index=self.files_index, body=base_query)['count']

        query = base_query.copy()
        query['query']['bool']['must_not'] = [{
            "exists": {
                "field": "projects.opensearch.drsId"
            }
        }]

        self.files_without_drs = self.es.count(index=self.files_index, body=query)['count']


def main():
    # Load arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--conf',
        help='Specify the configuration file. Defaults to use %(default)s',
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../conf/tag_check.conf')
    )
    parser.add_argument(
        '--output',
        help='Directory to place the output files',
        default='html'
    )

    args = parser.parse_args()

    # Load conf
    conf = ConfigParser()
    conf.read(args.conf)

    host = conf.get('elasticsearch', 'host')
    collections_index = conf.get('elasticsearch', 'collection_index')
    files_index = conf.get('elasticsearch', 'files_index')

    # Load template environment
    env = Environment(loader=PackageLoader("cci_tagger", "templates"))
    env.trim_blocks = True
    env.lstrip_blocks = True

    # Setup elasticsearch connection
    es = Elasticsearch([host], verify_certs=False)

    # Get list of all ECVs
    query = {
        "query": {
            "bool": {
                "must_not": [
                    {
                        "term": {
                            "ecv.keyword": 'cci'
                        }
                    }
                ]
            }
        },
        "aggs": {
            "ecvs": {
                "terms": {
                    "field": "ecv.keyword",
                    "size": 100
                }
            }
        },
        "size": 0
    }

    results = es.search(body=query, index=collections_index)['aggregations']['ecvs']['buckets']

    ecvs = [bucket['key'] for bucket in results]

    # Get datasets from each ecv
    for ecv in tqdm(ecvs, desc="Generating HTML pages"):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "ecv.keyword": ecv
                            }
                        }
                    ],
                    "must_not": [
                        {
                            "term": {
                                "collection_id.keyword": "cci"
                            }
                        }
                    ]
                }
            }
        }

        datasets = scan(es, query=query, index=collections_index)
        datasets = list(datasets)

        # Get list of drs ids
        drs_ids = []
        for result in datasets:
            drs_ids.extend(result['_source'].get('drsId',[]))

        # Generate page
        datasets = [Dataset(result, conf).as_dict() for result in datasets]

        template = env.get_template('ecv.html')

        output_dir = os.path.join(args.output, 'ecvs')

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        with open(os.path.join(output_dir, f'{ecv}.html'), 'w') as writer:
            writer.write(template.render({
                'title': ecv,
                'datasets': datasets,
                'drs_ids': drs_ids,
                'FILES_INDEX': files_index,
                'HOST': host
            }))

    # Make index page
    template = env.get_template('index.html')

    with open(os.path.join(args.output, 'index.html'), 'w') as writer:
        writer.write(template.render({
            'ecvs': ecvs,
        }))


if __name__ == '__main__':
    main()
