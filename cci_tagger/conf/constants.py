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

# Values that are common across a number of modules
BROADER_PROCESSING_LEVEL = 'broader_processing_level'
DATA_TYPE = 'data_type'
ECV = 'ecv'
FREQUENCY = 'time_coverage_resolution'
INSTITUTION = 'institution'
PLATFORM = 'platform'
PLATFORM_PROGRAMME = 'platform_programme'
PLATFORM_GROUP = 'platform_group'
PROCESSING_LEVEL = 'processing_level'
PRODUCT_STRING = 'product_string'
PRODUCT_VERSION = 'product_version'
SENSOR = 'sensor'

# Level 2 data is mapped to satellite orbit frequency
LEVEL_2_FREQUENCY = 'http://vocab.ceda.ac.uk/collection/cci/freq/freq_sat_orb'

# List of allowed netcdf attributes
ALLOWED_GLOBAL_ATTRS = [FREQUENCY, INSTITUTION, PLATFORM, SENSOR]
SINGLE_VALUE_FACETS = [BROADER_PROCESSING_LEVEL, DATA_TYPE, ECV, PROCESSING_LEVEL, PRODUCT_STRING]

DRS_FACETS = [ECV, FREQUENCY, PROCESSING_LEVEL, DATA_TYPE, SENSOR, PLATFORM, PRODUCT_STRING, PRODUCT_VERSION]
ALL_FACETS = [BROADER_PROCESSING_LEVEL, DATA_TYPE, ECV, FREQUENCY, INSTITUTION, PLATFORM, PLATFORM_PROGRAMME, PLATFORM_GROUP, PROCESSING_LEVEL, PRODUCT_STRING, PRODUCT_VERSION, SENSOR]

# Multilabels
MULTILABELS = {
    FREQUENCY: 'multi-frequency',
    INSTITUTION: 'multi-institution',
    PLATFORM: 'multi-platform',
    SENSOR: 'multi-sensor'
}

EXCLUDE_REALISATION = 'EXCLUDE'