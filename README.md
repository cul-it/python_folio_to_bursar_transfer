# Overview

This repository contains a set of Python tools to assist with the migration from the FOLIO OKAPI platform to the FOLIO Eureka platform. Many of the scripts need to be run in the order presented below as they build upon each other. I purposely did not combine them into a single function to allow for the review of data at each step.

# Installation

Copy .env.example over to .env and populate with your local settings.

```bash
source .venv/bin/activate
pip install \-r requirements.txt
```

# Setup
Before this script can be installed and ran remotely the data sets need be generated. 

# Running  


# Filters

Filters are defined in the .env file are have been implemented to allow for end users to check multiple aspects of the data returned.

## Filter format

```yaml
FILTER_1 = {"name"FineType", "error_message"Wrong Fee Fine Type", "load"FeeFineTypes.json", "flatten true, "filter_field"feeFineId", "filter_operator"IN_FILE", "filter_value""}
FILTER_2 = {"name"PatronType", "error_message"Wrong Patron Type", "load"PatronTypeUUID.json", "flatten true, "filter_field"patron.patronGroup", "filter_operator"IN_FILE", "filter_value""}
```

Each filter line must have a unique and consecutive numbers. The filters will be ran in numerical order.

## Fields

## name 
- Display name of the filter; used in some reports

## error_message 
- Error message to be added to the Export log

## load 
- (options) false | name of the JSON file to be imported

## flatten 
- (options) True | False 
- Should the JSON file be flattened. This will extract the UUID field from the array and place it in a new array. this is used to match based on the In function, or with files containing match patterns.

## filter_field 
- The field in the charges record that should be compared

## filter_operator 
- (options) EQUALS | NOT_EQUAL | ONE_OF | NULL_OR_ONE_OF | LONGER_THAN | SHORTER_THAN | IN_FILE
- operator to compare the field value to

## filter_value 
- The value to compare to the field. 
- To use a environmental variable use the following format: `ENV|<<ENVIRONMENTAL_VARIABLE_NAME>>` for example `ENV|TRANS_ACCOUNT_NAME`. This will try to match the value in the `TRANS_ACCOUNT_NAME` environmental variable to the field value.

# Reformatting

Reformatters are defined in the .env file are have been implemented to allow for end users manipulate the data that was returned by the FOLIO system.

## Reformatter format

```yaml
REFORMAT_1 = {"filter_field"patron.externalSystemId", "type"LEFT_STRIP", "search_for"0", "replace_with"", "new_field"patron.externalSystemId"}
REFORMAT_2 = {"filter_field"title", "search_for",", "type"REPLACE", "replace_with" ", "new_field"cleanTitle"}
```

Each reformat line must have a unique and consecutive numbers. The reformatters will be ran in numerical order.

## Fields

## filter_field
- The field that holds record that should be reformated     

## type
 - (options) LEFT_STRIP | RIGHT_STRIP | REPLACE
    - RIGHT_STRIP will remove the characters from the right side of the string as defined by the search_for field. 
    - LEFT_STRIP will remove the characters from the left side of the string as defined by the search_for field. 
    - REPLACE will replace the search_for string with the replace_with string.

## search_for
 - What value should be searched for and or what charter should be stripped from the left or right.

## replace_with
 - Used with REPLACE type. What the value should be replaced with.

 ## new_field
 - The field name where the changes are to be added to. This can be the same value as the filter_field

# Merge Fields

## Merge Fields format

```yaml
MERGE_1 = {"merge_type"FIELD", "loadfalse, "filter_fieldfalse, "new_field"fee_owner_id", "field_1"ownerId", "field_2"feeFineId", "field_deliminator"|", "field_transform"NONE"}
MERGE_2 = {"merge_type"FILE", "load"AccountMapping.json", "filter_field"fee_owner_id", "new_field"owner_data", "field_transform"NONE"}
```

Each merge line must have a unique and consecutive numbers. The merges will be ran in numerical order.

## Fields
### merge_type 
- (options) FIELD | FILE
    - FIELD this will combine two fields values into a single field separated byt he given deliminator. 
    - FILE This will use the defined field to match against the key in a separate JSON file and write that 'value" field contents of that file to the billing array..
- What type of merge should be done. 

## load 
- false
- name of the JSON file to be imported

## filter_field 
- false 
- Name of field that should be matched to the key in the JSON file.

## new_field 
- The field name where the changes are to be added to. This can be the same value as the filter_field

## field_1 
-  First field when combine 2 current data fields

## field_2 
-  Second field when combine 2 current data fields

## field_deliminator 
-  The deliminator to use when combining filed_1 and field_2

## field_transform 
-  NONE | COUNT |



# Contributing  

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. Please also fork as needed.
 
# .env File  

# License 

[MIT](https://choosealicense.com/licenses/mit/)