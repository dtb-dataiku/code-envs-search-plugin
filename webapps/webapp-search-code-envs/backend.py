from dataiku.customwebapp import *

# Access the parameters that end-users filled in using webapp config
# For example, for a parameter called "input_dataset"
# input_dataset = get_webapp_config()["input_dataset"]

import ast
import datetime
import re

import dataiku
import dash
import dash_bootstrap_components as dbc

from dash import dcc, html, Input, Output, State, ctx

from codeenvssearch.helpers import get_base_package


# CONFIGURATION
webapp_config = get_webapp_config()

CODE_ENVS_DS_NAME = webapp_config.get('code_envs_ds_name')

APP_HEADER = 'Search Code Environments'
APP_SUBHEADER = 'Search for already installed packages'


# HELPERS
def get_code_envs():
    '''Get code environment data.'''
    
    # Get pre-built dataset with code environments data
    code_envs_df = dataiku.Dataset(CODE_ENVS_DS_NAME).get_dataframe()
    code_envs_df['specified_packages'] = code_envs_df['specified_packages'].apply(ast.literal_eval)
    code_envs_df['actual_packages'] = code_envs_df['actual_packages'].apply(ast.literal_eval)
    
    # Get list of all code environments
    return code_envs_df.to_dict('records')

def search_code_envs(packages_query_raw, code_envs):
    '''Build search results content.'''
    
    # Process package query
    packages_query_list = [get_base_package(line.lower()) for line in packages_query_raw.split('\n') if line.split()]
    packages_query_set = set(filter(lambda p: p, packages_query_list))
    n_packages_in_query = len(packages_query_set)
    
    # Find code environments that contain one or more matches
    matched_code_envs = []
    for c in code_envs:
        specified_packages = set(map(lambda p: get_base_package(p), c.get('specified_packages', [])))
        if not packages_query_set.isdisjoint(specified_packages):
            matched_code_envs.append(c)
        
    # Build search content and match scores
    search_content, match_scores, names = [], [], []
    for m in matched_code_envs:
        # Get specified packages in code environment
        specified_packages_full = sorted(m.get('specified_packages', []))
        specified_packages_list = list(map(lambda p: get_base_package(p), specified_packages_full))
        specified_packages = set(map(lambda p: get_base_package(p), specified_packages_full))

        # Compare package query to specified packages
        common_packages = packages_query_set & specified_packages
        missing_packages = packages_query_set - common_packages
        match_score = (len(common_packages) / n_packages_in_query)

        # Get code environment language
        language = str(m.get('interpreter', ''))
        if language in ('nan', ''):
            language = m.get('language', '')

        # Build search content
        # Build title
        title_content = []

        title_content.append(html.P(m['name'], className='fw-bold lh-sm'))
        title_content.append(html.P(f"Match Score: {match_score:.0%},  Language: {language}", className='fst-italic lh-sm'))

        # Build details
        detailed_content = []

        if missing_packages:
            detailed_content.append(html.P('Missing packages:'))
            detailed_content.append(html.Ul([html.Li(p) for p in sorted(missing_packages)]))

        detailed_content.append(html.Br())
        detailed_content.append(html.P('Code environment packages:'))
        
        list_items = []
        for base_package, versioned_package in zip(specified_packages_list, specified_packages_full):
            if base_package in common_packages:
                list_items.append(html.Li(html.Strong(versioned_package)))
            else:
                list_items.append(html.Li(versioned_package))
                
        detailed_content.append(html.Ul(list_items))

        # Make list of dbc.AccordionItems to return
        search_content.append(dbc.AccordionItem(detailed_content, title=html.Div(title_content)))
        match_scores.append(match_score)
        names.append(m['name'])
        
        search_content = [
            x
            for _, _, x in sorted(
                zip(match_scores, names, search_content),
                key=lambda x: (-x[0], x[1])
            )
        ]

    return search_content


# APP
# Build layout
def serve_layout():
    header = html.Header(
        dbc.Container(
            [
                html.H1(APP_HEADER, className='display-5 mb-1'),
                html.P(APP_SUBHEADER, className='lead mb-0')
            ],
            fluid=False
        ),
        className='py-4 bg-light border-bottom sticky-top'
    )
    
    query = dbc.Container(
        [
            dbc.Card(
                [
                    dbc.CardHeader(html.H4('Query', className='mb-0')),
                    dbc.CardBody(
                        [
                            dbc.Label('Find code environments with the following package(s):'),
                            dbc.Textarea(
                                id='search-input',
                                size='sm',
                                placeholder='Enter packages line by line',
                                rows=5,
                                class_name='mb-3'
                            ),
                            dbc.Button(
                                'Search',
                                id='search-button',
                                color='primary',
                                class_name='me-1'
                            ),
                            dbc.Button(
                                'Reset',
                                id='reset-button',
                                color='primary',
                                class_name='me-1'
                            ),
                            dbc.Alert(
                                id='search-alert',
                                is_open=False,
                                dismissable=False,
                                duration=None,
                                class_name='mt-2'
                            )
                        ],
                        class_name='mb-3'
                    )
                ],
                className="mb-4 shadow-sm"
            )
        ],
        fluid=False,
        class_name='py-4'
    )
    
    results = html.Div(
        id='results-div',
        children=[
            dbc.Container(
                [
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H4('Results', className='mb-0')),
                            dbc.CardBody(
                                dbc.Accordion(id='results-list', start_collapsed=True),
                                class_name='mb-3'
                            )
                        ],
                        class_name='mb-4 shadow-sm'
                    )
                ],
                fluid=False,
                class_name='py-4'
            )
        ],
        style={'display': 'none'}
    )
    
    return html.Div([
        header,
        dbc.Row([dbc.Col([query]), dbc.Col([results])])
    ])

# Set stylesheet
app.config.external_stylesheets = [dbc.themes.BOOTSTRAP]

# Serve layout
app.layout = serve_layout

# Search
@app.callback(
    Output('search-alert', 'is_open'),
    Output('search-alert', 'children'),
    Output('search-alert', 'color'),
    Output('search-alert', 'duration'),
    Input('search-button', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    State('search-input', 'value'),
    prevent_initial_call=True
)
def search_alert(search_clicks, reset_clicks, search_input):
    trigger_id = ctx.triggered_id
    
    if trigger_id == 'search-button':
        if not search_input:
            return True, 'Please enter packages; one package per line.', 'warning', None
        
    if trigger_id == 'reset-button':
        return False, None, None, None
    
    return True, 'Searching...', 'success', 5000

@app.callback(
    Output('search-input', 'value'),
    Output('results-list', 'children'),
    Output('results-div', 'style'),
    Input('search-button', 'n_clicks'),
    Input('reset-button', 'n_clicks'),
    State('search-input', 'value'),
    prevent_initial_call=True
)
def update_results(search_clicks, reset_clicks, search_input):
    trigger_id = ctx.triggered_id
    
    if trigger_id == 'reset-button':
        return '', None, {'display': 'none'}
    
    if trigger_id == 'search-button':
        if not search_input:
            return dash.no_update, None, {'display': 'none'}
        
        code_envs = get_code_envs()
        search_content = search_code_envs(search_input, code_envs)
        
        return dash.no_update, search_content, {'display': 'block'}
    
    
    return dash.no_update, dash.no_update, dash.no_update
