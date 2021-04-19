# encoding: utf-8
"""

"""
__author__ = 'Richard Smith'
__date__ = '07 Feb 2020'
__copyright__ = 'Copyright 2018 United Kingdom Research and Innovation'
__license__ = 'BSD - see LICENSE file in top-level package directory'
__contact__ = 'richard.d.smith@stfc.ac.uk'

from json_tagger import DatasetJSONMappings
from cci_tagger.dataset.dataset import Dataset
from cci_tagger.facets import Facets

PATH = '/Users/vdn73631/Documents/dev/CCI_KE_PROJECT/cci-tagger/cci_tagger/tests/ocean_colour/ESACCI-OC-L3S-CHLOR_A-MERGED-5D_DAILY_4km_GEO_PML_OCx-20000101-fv4.0.nc'
PATH = '/Users/vdn73631/Documents/dev/CCI_KE_PROJECT/cci-tagger/cci_tagger/tests/cloud/200707-ESACCI-L3C_CLOUD-CLD_PRODUCTS-AVHRR_METOPA-fv2.0.nc'
# PATH = '/Users/vdn73631/Documents/dev/CCI_KE_PROJECT/cci-tagger/cci_tagger/tests/sst/19960202120000-ESACCI-L4_GHRSST-SSTdepth-OSTIA-GLOB_CDR2.1-v02.0-fv01.0.nc'
PATH = '/Users/vdn73631/Documents/dev/CCI_KE_PROJECT/cci-tagger/cci_tagger/tests/biomass/ESACCI-BIOMASS-L4-AGB-MERGED-100m-2017-fv1.0.nc'

# GET JSON FILES
mappings = DatasetJSONMappings(['/Users/vdn73631/Documents/dev/CCI_KE_PROJECT/cci-tagger/cci_tagger/tests/test_json_files/biomass.json'])
facets = Facets()

dataset_id = mappings.get_dataset(PATH)

dataset = Dataset(dataset_id, mappings, facets)

uris = dataset.get_file_tags(filepath=PATH)

tags = facets.process_bag(uris)

drs_facets = dataset.get_drs_labels(tags)

drs = dataset.generate_ds_id(drs_facets, PATH)

print(uris)

print(tags)

print(drs_facets)

print(drs)

