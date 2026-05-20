# Code for custom code recipe code-envs-datasets (imported from a Python recipe)

# To finish creating your custom recipe from your original PySpark recipe, you need to:
#  - Declare the input and output roles in recipe.json
#  - Replace the dataset names by roles access in your code
#  - Declare, if any, the params of your custom recipe in recipe.json
#  - Replace the hardcoded params values by acccess to the configuration map

# See sample code below for how to do that.
# The code of your original recipe is included afterwards for convenience.
# Please also see the "recipe.json" file for more information.

# import the classes for accessing DSS objects from the recipe
import dataiku
# Import the helpers for custom recipes
from dataiku.customrecipe import get_input_names_for_role
from dataiku.customrecipe import get_output_names_for_role
from dataiku.customrecipe import get_recipe_config

# Inputs and outputs are defined by roles. In the recipe's I/O tab, the user can associate one
# or more dataset to each input and output role.
# Roles need to be defined in recipe.json, in the inputRoles and outputRoles fields.

# To  retrieve the datasets of an input role named 'input_A' as an array of dataset names:
input_A_names = get_input_names_for_role('input_A_role')
# The dataset objects themselves can then be created like this:
input_A_datasets = [dataiku.Dataset(name) for name in input_A_names]

# For outputs, the process is the same:
output_A_names = get_output_names_for_role('main_output')
output_A_datasets = [dataiku.Dataset(name) for name in output_A_names]


# The configuration consists of the parameters set up by the user in the recipe Settings tab.

# Parameters must be added to the recipe.json file so that DSS can prompt the user for values in
# the Settings tab of the recipe. The field "params" holds a list of all the params for wich the
# user will be prompted for values.

# The configuration is simply a map of parameters, and retrieving the value of one of them is simply:
my_variable = get_recipe_config()['parameter_name']

# For optional parameters, you should provide a default value in case the parameter is not present:
my_variable = get_recipe_config().get('parameter_name', None)

# Note about typing:
# The configuration of the recipe is passed through a JSON object
# As such, INT parameters of the recipe are received in the get_recipe_config() dict as a Python float.
# If you absolutely require a Python int, use int(get_recipe_config()["my_int_param"])


#############################
# Your original recipe
#############################

# -*- coding: utf-8 -*-
import dataiku
import datetime
import pandas as pd
import re


# Create Dataiku API client
client = dataiku.api_client()

# Create function to extract the base package name
def get_base_package(package):
    base_package = package

    # Handle packages that are referenced with an URL or path
    pattern = r"^(\/|http|git\+http|\-\-find)"
    if re.match(pattern, package):
        base_package = base_package.split('/')[-1]
        if '-' in base_package:
            base_package = base_package.split('-')[0].replace('_', '-')

    # Extract the base package
    # Extract the base package
    pattern = r"^([\w\-\.\[\]]+)"
    base_package = (
        base_package
        .strip()
        .replace('"', '')
        .replace("'", '')
        .replace('#', '')
        .replace('_', '-')
    )

    try:
        base_package = re.match(pattern, base_package).group(1)
    except:
        print(f'Exception when packaged={base_package}')
        base_package = None

    return base_package

# Get list of all code environments
code_envs = client.list_code_envs(as_objects=True)

# Build a list of all the code environments and their associated packages
code_envs_rows = []
for c, code_env in enumerate(code_envs):
    # Get the code environment definition
    definition = code_env.get_definition()

    # Capture details
    row = dict(
        name=None,
        owner=None,
        language=None,
        interpreter=None,
        specified_packages=[],
        actual_packages=[],
        modified=None
    )

    row['name'] = definition.get('envName')

    owner = definition.get('desc').get('owner')
    if owner and owner.startswith('api'):
        owner = 'api'
    row['owner'] = owner

    row['language'] = definition.get('envLang')

    if definition.get('envLang') == 'PYTHON':
        row['interpreter'] = definition.get('desc').get('pythonInterpreter')

    if definition.get('envLang') == 'R':
        row['interpreter'] = definition.get('envLang')

    specified_packages = definition.get('specPackageList')
    if specified_packages and len(specified_packages) > 1:
        specified_packages = list(set(specified_packages.split('\n')))

    specified_packages = [p for p in specified_packages if p]
    specified_packages = list(filter(lambda p: not p.startswith(('--', '#')), specified_packages))
    specified_packages = list(map(lambda p: re.split(r'[;#]', p)[0].strip(), specified_packages))

    row['specified_packages'] = specified_packages

    actual_packages = definition.get('actualPackageList')
    if actual_packages and len(actual_packages) > 1:
        actual_packages = list(set(actual_packages.split('\n')))

    actual_packages = [p for p in actual_packages if p]
    actual_packages = list(filter(lambda p: not p.startswith(('--', '#')), actual_packages))
    actual_packages = list(map(lambda p: re.split(r'[;#]', p)[0].strip(), actual_packages))

    row['actual_packages'] = actual_packages

    modified = int(definition.get('desc').get('creationTag').get('lastModifiedOn'))
    row['modified'] = datetime.datetime.fromtimestamp(modified / 1e3)

    code_envs_rows.append(row)

# Build a list of all specified packages
packages_rows = []
for cer in code_envs_rows:
    for package in cer.get('specified_packages', []):
        row = dict(
            language=cer.get('language', ''),
            package=get_base_package(package)
        )
        packages_rows.append(row)

# Store data in a dataframe
code_envs_df = pd.DataFrame(data=code_envs_rows)
code_envs_df = (
    code_envs_df
    .sort_values(by=['language', 'name'])
    .reset_index(drop=True)
)

packages_df = pd.DataFrame(data=packages_rows)
packages_df = (
    packages_df
    .drop_duplicates()
    .sort_values(by=['language', 'package'])
    .reset_index(drop=True)
)

# Write recipe outputs
code_envs_ds = dataiku.Dataset("code_environments")
code_envs_ds.write_with_schema(code_envs_df)

packages_ds = dataiku.Dataset("packages")
packages_ds.write_with_schema(packages_df)