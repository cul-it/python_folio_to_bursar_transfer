# Overview

This repository contains a set of Python tools to assist with the migration from the FOLIO OKAPI platform to the FOLIO Eureka platform. Many of the scripts need to be run in the order presented below as they build upon each other. I purposely did not combine them into a single function to allow for the review of data at each step.

# Installation

Copy .env.example over to .env and populate with your local settings.

```bash
source .venv/bin/activate
pip install \-r requirements.txt
```

# Configuration

Please see the wiki for .env values and configuration file settings.
The system uses a mix of environment variables and configuration files to manage settings. Secrets are stored in the .env file while job, and processing settings are stored in yaml files located in the `config` directory.

# Data files
Before this script can be installed and ran remotely the data sets need be generated. Theses can be done manually or using the provided utility scripts.

# Running  

```bash
python ./main.py
```

# Testing  

All tests are written using pytest and can be run using the following command:

```bash
pytest
```

Tests are located in the `tests` directory with one test file per class. At the tiem or writing the tests are not complete and are a work in progress.

# Contributing  

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. Please also fork as needed.
 


# License 

[MIT](https://choosealicense.com/licenses/mit/)