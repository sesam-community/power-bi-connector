import json
from six import iteritems
import requests
import sys


default_datetime = '1900-01-01'.split()
default_boolean  = 'False'
default_decimal  = '0.0'
default_int      = '0'
default_string   = 'none'

def setup_dataset(Sesam_data_id):
    """ 
    Creates a new dictionary with the standard Power BI setup
    with one dataset and one table 

    Parameters:
        pipe_data: The data from the Sesam pipe

    Returns: 
        A new dictionary for Power BI use
    """

    tables = [Sesam_data_id]
    new_dataset                = {}
    new_dataset['name']        = Sesam_data_id
    new_dataset["defaultMode"] = "Push"
    new_dataset['tables']      = []

    for i, table in enumerate(tables):
        new_dataset['tables'].append({})
        new_dataset['tables'][i]['name']    = table 
        new_dataset['tables'][i]['columns'] = []

    return new_dataset

def find_dataset_id(response, pipe_name):
    for dataset in response.json()['value']:
        if dataset['name'] == pipe_name:
            return dataset['id']
    print("No matching dataset was found")
    sys.exit()

def check_dataset_status(current_datasets, entities, pipe_name):
    update_rows = update_columns = dataset_id = False
    try:
        num_keys_new = len(entities[0].keys())
    except IndexError:
        print("There are no entities in the Sesam data")
        sys.exit()

    try:
        current_datasets.json()['value']
        for dataset in current_datasets.json()['value']:
            if dataset['name'] == pipe_name:
                dataset_id = dataset['id'] 
                num_keys_old = len(current_datasets.json()['value'][0].keys())
                if num_keys_old == num_keys_new:
                    update_rows = True
                    break
                else:
                    update_columns = True
                    break
    except KeyError:
        dataset_id = False

    return update_rows, update_columns, dataset_id

def add_columns(new_dict, entities, schema):
    """
    Fills in the columns in the disctionary from setup_powerBi_json
    with Sesam entities as rows, and values as columns 

    Parameters:
        new_dict: The dictionary created in setup_powerBi_json
        Sesam_data:     The data from Sesam

    Returns:
        A dictionary with the Sesam data attached in Power BI format
    """

    num_tables = len(new_dict['tables'])
    num_columns = len(schema)

    keys = [data['name'] for data in schema]
    for i in range(num_tables):
        for j in range(num_columns):
            try:
                dataType = schema[j]['type'].capitalize()
                if dataType == 'Null':
                    dataType = 'String'

            except IndexError:
                dataType = 'String'
            new_dict['tables'][i]['columns'].append({})                                                       
            new_dict['tables'][i]['columns'][j]['name'] = keys[j]
            if dataType == 'Datetime':
                new_dict['tables'][i]['columns'][j]['dataType'] = 'DateTime'
                new_dict['tables'][i]['columns'][j]['formatString'] = "m/d/yyyy"
                #new_dict['tables'][0]['columns'][col]['summarizeBy'] = "none"
            elif dataType == 'Integer':
                new_dict['tables'][i]['columns'][j]['dataType'] = 'Int64'                
            else:
                new_dict['tables'][i]['columns'][j]['dataType'] = dataType
    return new_dict, keys

def add_rows(entities, populated_dataset, keys):

    rows         = {}
    rows["rows"] = []
    num_rows     = len(entities)
    num_tables   = len(populated_dataset['tables'])

    for i in range(num_tables):
        for j, entity in enumerate(entities):
            rows["rows"].append({})
            for k, key in enumerate(keys):
                dataType = populated_dataset['tables'][i]['columns'][k]['dataType']
                try:
                    value = format_value(entity[key], dataType)
                except KeyError:
                    value = format_value("", dataType)
                rows['rows'][j][key] = value
    return rows

def format_value(value, dataType):

    if dataType == 'Boolean':
        value = str(value).capitalize()
        if value != 'False' and value != 'True':
            value = default_boolean # default is missing value
        value = bool(value)
        return value

    elif dataType == 'DateTime':
        split_value = value.split()

        if len(split_value) == 0:
            split_value = default_datetime

        elif split_value[0][0] == '~':
            return split_value[0][2:]

        elif len(split_value[0]) == 10:
            if not '-' in split_value[0][:4]:
                return split_value[0]
            else:
                split_value = default_datetime 
        else:
            split_value = default_datetime 
        return split_value[0]

    elif dataType == 'Decimal':
        if value == "":
            return default_decimal
        if str(value).split()[0][0] == '~':
            return str(value).split()[0][2:]
        else:
            return str(value)

    elif dataType == 'Int64':
        if  len(str(value).split()) == 0:
            return default_int
        elif value == None:
            return default_int
        else:
            return value
    elif dataType == 'String':
        if len(str(value).split()) == 0:
            return default_string
        else:
            return value

    else:
        return str(value)
