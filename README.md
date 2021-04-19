# CCI Tagger

## Overview

This package provides a command line tool moles_esgf_tag to generate dataset
tags for both MOLES and ESGF.

## Installation

Create a Python virtual environment:
**Must be Python 3**

```bash
python -m venv venv
source venv/bin/activate
```

Install the latest version of the library

```bash
git clone https://github.com/rsmith013/cci-tagger
cd cci-tagger
pip install -r requirements.txt
pip install -e .
```

## Command Line Script

This script is to be used to check what the tagger outputs when fed with the JSON files. This can be used to build the JSON files and
check they are producing what you expect. This script also produces a moles_tags files to attach to this dataset.

### Usage

```
moles_esgf_tag [-h] (-d DATASET | -f FILE | -j JSON_FILE) [--file_count FILE_COUNT] [-v]
```

You can tag an individual dataset, or tag all the datasets listed in a file. By default a check sum will be produces for each file.

Arguments:

    -h, --help            show help message and exit

    -d DATASET, --dataset DATASET
                          the full path to the dataset that is to be tagged. This option is used to tag a single
                          dataset.

    -f FILE, --file FILE  the name of the file containing a list of datasets to process. This option is used for
                          tagging one or more datasets.

    -j, --json_file       Use the JSON file to provide a list of datasets and also provide the mappings
                          which are used by the tagging code. Useful to test datsets and specific mapping files.

    --file_count FILE_COUNT
                          how many .nc files to look at per dataset

    -v, --verbose         increase output verbosity. Add more vs to increase verbosity.


### Output

A number of files are produced as output:
*  __esgf_drs.json__ contains a list of DRS and associated files. Will also list all files which could not generate a DRS
*  __moles_tags.csv__ contains a list of dataset paths and vocabulary URLs
*  __error.log__ contains a log of errors. This is appended to on each run so if you want a clean start, you will need to delete the file.

### Examples

```bash
moles_esgf_tag -d /neodc/esacci/cloud/data/L3C/avhrr_noaa-16 -v
moles_esgf_tag -f datapath --file_count 2 -v
```

## Check tags

This code generates a directory with HTML pages which can be used to interrogate the opensearch elasticsearch indices to check that
the tags which you are expecting are being found. It also highlights files without DRSs

### Usage

```
cci_check_tags [--conf CONF] [--output OUTPUT]
```

Arguments:

        --conf          Specify the configuration file. Defaults to use %(default)s' 
                        DEFAULT: cci_tagger/conf/tag_check.conf
                        
        --output        Directory to place the output files.
                        DEFAULT: html 

### Output

* index.html            The main page listing all ECVs in the index
* ecv/<ecv_name>.html   ECV specific page. Lists all MOLES datasets in the index and displays details about them.

## Breaking Changes

### V2.0.0
- Removed default terms file
- Removed DRS version based on date

