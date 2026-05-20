import dataiku
import datetime
import pandas as pd
import re

from codeenvssearch.helpers import get_base_package

def get_code_envs_as_dataframe()
    client = dataiku.api_client()

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

    # Store code environments data in a dataframe
    code_envs_df = pd.DataFrame(data=code_envs_rows)
    code_envs_df = (
        code_envs_df
        .sort_values(by=['language', 'name'])
        .reset_index(drop=True)
    )

    return code_envs_df

def get_packages_as_dataframe():
    client = dataiku.api_client()

    # Get list of all code environments
    code_envs = client.list_code_envs(as_objects=True)

    # Build a list of all the code environments and their associated packages
    code_envs_rows = []
    for c, code_env in enumerate(code_envs):
        # Get the code environment definition
        definition = code_env.get_definition()

        # Capture details
        row = dict(
            language=None,
            specified_packages=[],
            actual_packages=[]
        )

        row['language'] = definition.get('envLang')

        specified_packages = definition.get('specPackageList')
        if specified_packages and len(specified_packages) > 1:
            specified_packages = list(set(specified_packages.split('\n')))

        specified_packages = [p for p in specified_packages if p]
        specified_packages = list(filter(lambda p: not p.startswith(('--', '#')), specified_packages))
        specified_packages = list(map(lambda p: re.split(r'[;#]', p)[0].strip(), specified_packages))

        row['specified_packages'] = specified_packages

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

    # Store code environments data in a dataframe
    packages_df = pd.DataFrame(data=packages_rows)
    packages_df = (
        packages_df
        .drop_duplicates()
        .sort_values(by=['language', 'package'])
        .reset_index(drop=True)
    )

    return packages_df
