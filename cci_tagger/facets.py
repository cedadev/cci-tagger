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

from cci_tagger.conf.constants import DATA_TYPE, FREQUENCY, INSTITUTION, PLATFORM, \
    SENSOR, ECV, PLATFORM_PROGRAMME, PLATFORM_GROUP, PROCESSING_LEVEL, \
    PRODUCT_STRING, BROADER_PROCESSING_LEVEL, PRODUCT_VERSION
from cci_tagger.conf.settings import SPARQL_HOST_NAME
from cci_tagger.triple_store import TripleStore, Concept
import re


class Facets(object):
    """
    This class is used to store data about the facets, that are obtained from
    the triple store.

    """

    # URL for the vocab server
    VOCAB_URL = f'http://{SPARQL_HOST_NAME}/scheme/cci'

    # All the desired facet endpoints
    FACET_ENDPOINTS = {
        DATA_TYPE: f'{VOCAB_URL}/dataType',
        ECV: f'{VOCAB_URL}/ecv',
        FREQUENCY: f'{VOCAB_URL}/freq',
        PLATFORM: f'{VOCAB_URL}/platform',
        PLATFORM_PROGRAMME: f'{VOCAB_URL}/platformProg',
        PLATFORM_GROUP: f'{VOCAB_URL}/platformGrp',
        PROCESSING_LEVEL: f'{VOCAB_URL}/procLev',
        SENSOR: f'{VOCAB_URL}/sensor',
        INSTITUTION: f'{VOCAB_URL}/org',
        PRODUCT_STRING: f'{VOCAB_URL}/product'
    }

    LABEL_SOURCE = {
        BROADER_PROCESSING_LEVEL: '_get_pref_label',
        DATA_TYPE: '_get_alt_label',
        ECV: '_get_alt_label',
        FREQUENCY: '_get_pref_label',
        INSTITUTION: '_get_pref_label',
        PLATFORM: '_get_platform_label',
        PLATFORM_PROGRAMME: '_get_pref_label',
        PLATFORM_GROUP: '_get_pref_label',
        PROCESSING_LEVEL: '_get_alt_label',
        PRODUCT_STRING: '_get_pref_label',
        PRODUCT_VERSION: None,
        SENSOR: '_get_pref_label'
    }



    def __init__(self, from_json=False):

        # a dict of concept schemes
        self.__facets = {}

        # mapping from platform uri to platform programme label
        self.__platform_programme_mappings = {}

        # mapping from platform uri to platform group label
        self.__programme_group_mappings = {}

        # mapping for process levels
        self.__proc_level_mappings = {}

        # Reversed mapping to allow lookup from uri to tag.
        self.__reversible_facets = {}

        if not from_json:
            for facet, uri in self.FACET_ENDPOINTS.items():
                self._init_concepts(facet, uri)

            self._init_proc_level_mappings()
            self._init_platform_mappings()
            self._reverse_facet_mappings()

    def _init_concepts(self, facet, uri):

        self.__facets[facet] = TripleStore.get_concepts_in_scheme(uri)
        self.__facets[f'{facet}-alt'] = TripleStore.get_alt_concepts_in_scheme(uri)

    def _init_platform_mappings(self):
        """
        Initialise the platform-programme and programme-group mappings.

        Get the hierarchical mappings between programme, platform and group and
        store them locally.

        """
        self.__platform_programme_mappings = {}
        self.__programme_group_mappings = {}

        for platform in self.__facets[PLATFORM].values():
            program_label, program_uri = TripleStore.get_broader(platform)

            # Get the broader terms for each of the uris in the platform list
            self.__platform_programme_mappings[platform.uri] = program_label

            # Get group labels from the broader platform uri
            group_label, _ = TripleStore.get_broader(program_uri)

            if group_label:
                self.__programme_group_mappings[program_uri] = group_label

    def _init_proc_level_mappings(self):
        """
        Initialise the process level mappings.

        Get the hierarchical mappings between process levels and
        store them locally.

        """
        self.__proc_level_mappings = {}
        for proc_level in self.__facets[PROCESSING_LEVEL].values():
            _, proc_level_uri = TripleStore.get_broader(proc_level)

            if proc_level_uri != '':
                self.__proc_level_mappings[proc_level.uri] = proc_level_uri

        self.__facets[BROADER_PROCESSING_LEVEL] = {TripleStore.get_alt_label(uri): uri for uri in
                                                  self.__proc_level_mappings.values()}

    def _reverse_facet_mappings(self):
        """
        Reverse the facet mappings so that it can be given a uri and
        return the required tag.
        :return:
        """

        # Reverse main facets
        for facet in self.__facets:

            reversed = {}

            for k,v in self.__facets[facet].items():
                if isinstance(v, str):
                    reversed[v] = k
                else:
                    reversed[v.uri] = v.tag

            self.__reversible_facets[facet] = reversed

    def get_facet_names(self):
        """
        Get the list of facet names.

        @return  a list of str containing facet names

        """
        facet_names = []
        for key in self.__facets.keys():
            if not key.endswith('-alt'):
                facet_names.append(key)
        return facet_names

    def get_alt_labels(self, facet):
        """
        Get the facet alternative labels and URIs.

        @param facet (str): the name of the facet

        @return a dict where:\n
            key = lower case version of the concepts alternative label\n
            value = uri of the concept

        """
        return self.__facets[f'{facet}-alt']

    def get_labels(self, facet):
        """
        Get the facet labels and URIs.

        @param facet (str): the name of the facet

        @return a dict where:\n
            key = lower case version of the concepts preferred label\n
            value = uri of the concept

        """
        return self.__facets[facet]

    def get_platforms_programme(self, uri):
        """"
        Get the programme label for the given platform URI.

        @param uri (str): the URI of the platform

        @return a str containing the label of the programme that contains the
                platform

        """
        return self.__platform_programme_mappings.get(uri)

    def get_programme_labels(self):
        """
        Get a list of the programme labels, where a programme is a container
        for platforms.

        @return a list of str containing programme labels

        """
        return self.__platform_programme_mappings.values()

    def get_programmes_group(self, uri):
        """"
        Get the group label for the given programme URI.

        @param uri (str): the URI of the programme

        @return a str containing the label of the group that contains the
                programme

        """
        return self.__programme_group_mappings.get(uri)

    def get_group_labels(self):
        """
        Get a list of the group labels, where a group is a container
        for programmes.

        @return a list of str containing group labels

        """
        return self.__programme_group_mappings.values()

    def get_broader_proc_level(self, uri):
        """"
        Get the broader process level URI for the given process level URI.

        @param uri (str): the URI of the process level

        @return a str containing the label of the process level

        """
        return self.__proc_level_mappings.get(uri)

    def get_label_from_uri(self, facet, uri):
        """
        Mappings between facets and label getter
        BROADER_PROCESSING_LEVEL: pref,
        DATA_TYPE: alt,
        ECV: alt,
        FREQUENCY: pref,
        INSTITUTION: pref,
        PLATFORM: pref (made up of PLATFORM_PROGRAMME and PLATFORM_GROUP),
        PLATFORM_PROGRAMME: pref,
        PLATFORM_GROUP: pref,
        PROCESSING_LEVEL: alt,
        PRODUCT_STRING: pref,
        PRODUCT_VERSION: None,
        SENSOR: pref

        :param facet:
        :param uri:
        :return:
        """

        label_routing_string = self.LABEL_SOURCE.get(facet)

        if label_routing_string:

            # Turn string into a callable
            label_routing_func = getattr(self, label_routing_string)

            if label_routing_func:
                return label_routing_func(facet, uri)

        return uri

    def get_pref_label_from_alt_label(self, facet, label):
        """
        Reverse the lookup from alt label to pref label
        :param facet: facet label belongs to
        :param label: label to check
        :return: pref_label
        """

        facet_l = facet.lower()
        term_l = label.lower()

        # Check the term source
        mapping = self.LABEL_SOURCE.get(facet_l)

        if mapping:
            m = re.match('^_get_(?P<label>\w+)_label$', mapping)
            if m:
                source = m.group('label')

                # These sources are alread the pref label
                if source in ('pref', 'product'):
                    return term_l
                else:
                    # Get the URI and then get pref label
                    if term_l in self.get_alt_labels(facet):
                        uri = self.get_alt_labels(facet)[term_l].uri
                        return self._get_pref_label(facet_l, uri)
        return term_l

    def _get_pref_label(self, facet, uri):
        """
        Get the preferred label for the given facet and uri
        :param facet:
        :param uri:
        :return:
        """
        return self.__reversible_facets[facet].get(uri)

    def _get_alt_label(self, facet, uri):
        """
        Get the alt label for the given facet and uri
        :param facet:
        :param uri:
        :return:
        """
        return self.__reversible_facets[f'{facet}-alt'].get(uri)

    def _get_platform_label(self, facet, uri):
        """
        The platform uris are made up of three facets. Try each
        one to see if there is a match
        :param facet: unused
        :param uri:
        :return: label
        """

        for facet in [PLATFORM, PLATFORM_GROUP, PLATFORM_PROGRAMME]:
            label = self.__reversible_facets[facet].get(uri)

            if label:
                return label

        return uri

    def process_bag(self, bag):
        """
        Take a dictionary of facets with uris or strings and turn it into tags
        :param bag: dictionary of facets with lists of uris to convert
        :return: dictionary of facets with the extracted tags
        """
        output = {}

        for facet in bag:
            if isinstance(bag[facet],str):
                uri = bag[facet]

                # Filter out None values
                output[facet] = list(
                    filter(None, [self.get_label_from_uri(facet, uri)])
                )
            else:
                # Filter out None values
                output[facet] = list(
                    filter(None, [self.get_label_from_uri(facet, uri) for uri in bag[facet]])
                )

        return output

    def to_json(self):
        response = {}

        # Get the __facet values
        __facet_dict = {}
        for facet, values in self.__facets.items():
            __facet_dict[facet] = {}
            for label, concept in values.items():
                # Concepts can either be a Concept Object or a string
                if isinstance(concept, str):
                    __facet_dict[facet][label] = concept
                else:
                    __facet_dict[facet][label] = concept.__dict__()

        response['__facets'] = __facet_dict

        # Add the other attributes
        response['__platform_programme_mappings'] = self.__platform_programme_mappings
        response['__programme_group_mappings'] = self.__programme_group_mappings
        response['__proc_level_mappings'] = self.__proc_level_mappings
        response['__reversible_facets'] = self.__reversible_facets

        return response

    @classmethod
    def from_json(cls, data):
        
        # Extract the __facet values
        __facet_dict = {}
        for facet, values in data['__facets'].items():
            __facet_dict[facet] = {}
            for label, concept in values.items():
                # Concepts can either be a Concept Object or a string
                if isinstance(concept, str):
                    __facet_dict[facet][label] = concept
                else:
                    __facet_dict[facet][label] = Concept(**concept)

        obj = cls(from_json=True)

        obj.__facets = __facet_dict

        # Extract the other attributes
        obj.__platform_programme_mappings = data['__platform_programme_mappings']
        obj.__programme_group_mappings = data['__programme_group_mappings']
        obj.__proc_level_mappings = data['__proc_level_mappings']
        obj.__reversible_facets = data['__reversible_facets']

        return obj
