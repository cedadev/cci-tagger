import os
import re

from setuptools import find_packages
from setuptools import setup


BASE_NAME = 'cci_tagger'

V_FILE = open(os.path.join(os.path.dirname(__file__),
                           BASE_NAME, '__init__.py'))

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

VERSION = re.compile(r".*__version__ = '(.*?)'",
                     re.S).match(V_FILE.read()).group(1)

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name=BASE_NAME,
    version=VERSION,
    author=u'Antony Wilson',
    author_email='antony.wilson@stfc.ac.uk',
    include_package_data=True,
    packages=find_packages(),
    url='http://stfc.ac.uk/',
    license='BSD licence',
    long_description=README,

    entry_points={
        'console_scripts': [
            'moles_esgf_tag = cci_tagger.scripts:CCITaggerCommandLineClient.main',
            'cci_json_check = cci_tagger.scripts:TestJSONFile.cmd',
            'cci_check_tags = cci_tagger.scripts.check_tags:main',
            'export_facet_json = cci_tagger.scripts.dump_facet_object:main'
        ],
    },

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],

    # Adds dependencies
    install_requires=[
        'SPARQLWrapper',
        'netCDF4',
        'six',
        'verboselogs',

    ],
)
