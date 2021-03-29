from tisane.variable import AbstractVariable, Numeric, Nominal, Ordinal
from tisane.design import Design
from tisane.statistical_model import StatisticalModel
from tisane.smt.synthesizer import Synthesizer
from tisane.helpers import *

from typing import List, Any, Tuple
import subprocess
from subprocess import DEVNULL
import os
import sys

import pandas as pd
import plotly.figure_factory as ff
import plotly.express as px
import dash
import dash_daq as daq
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State, ALL, MATCH
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import webbrowser # For autoamtically opening the browser for the CLI

external_stylesheets = [dbc.themes.BOOTSTRAP]
port = '8081' # FYI: default dash port is 8081
def open_browser():
	webbrowser.open_new("http://localhost:{}".format(port))

__value_to_z3__ = dict() # Global map between vals and z3 facts
        
class InputInterface(object): 
    design: Design 
    statistical_model: StatisticalModel
    app: dash.Dash

    def __init__(self, main_effects: Dict[str, List[AbstractVariable]], interaction_effects: Dict[str, Tuple[AbstractVariable, ...]], design: Design, synthesizer: Synthesizer):
        self.design = design
        self.synthesizer = synthesizer
        
        app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

        ##### Layout main aspects of UI
        main_effects_div = self.layout_main_effects_div(main_effects)
        interaction_effects_div = self.layout_interaction_effects_div(interaction_effects)
        # random_effects_div = self.layout_random_effects_div(random_effects)
        script_download_button = dbc.Button("Generate code snippet and model diagnostics", id='generate_code', color="primary", block=True, disabled=True)

        # Create Dash App
        app.layout = dbc.Container([
                dcc.Store(id='session_store', storage_type='session'),
                dbc.Row([dbc.Col(main_effects_div, width=8)], justify='center'),
                dbc.Row([dbc.Col(interaction_effects_div, width=8)], justify='center'),
                # dbc.Row([dbc.Col(random_effects_card, width=8)], justify='center'),
                # dbc.Row([dbc.Col(family_and_link_card, width=8)], justify='center'),
                dbc.Row([dbc.Col(script_download_button, width=8)], justify='center'),

                # Hidden div for storing intermediate state before updating session
                # store and eventually checking with synthesizer
                html.Div(id='intermediate_store', hidden=True)
            ],
            fluid=True
        )
        
        # TODO: Move outside ctor?
        ##### Add callbacks for interactions
        
        # TODO: Start here - save the values we care about into intermediate storage div; test that first
        @app.callback(
            Output('main_effects_options', 'options'),
            [Input('main_effects_switch', 'value'),
            State('main_effects_options', 'options')],
            # State('main_effects_options', 'options')
        )
        def save_main_effects(switch_value, main_effects_options):
            output = list()
            if switch_value: 
                facts = list()
                for o in main_effects_options: 
                    facts.append(o['value'])
                    output.append({'label': o['label'], 'value': o['value'], 'disabled': True})
                    
                is_sat = self.synthesizer.check_constraints(facts, rule_set='effects', design=self.design)
                if is_sat: 
                    self.synthesizer.update_with_facts(facts, rule_set='effects', design=self.design)
                    return output
                else: 
                    # TODO: Start a modal?
                    raise ValueError(f"Error in saving main effects!")
            else: 
                for o in main_effects_options: 
                    output.append({'label': o['label'], 'value': o['value'], 'disabled': False})
                
                return output
        
        @app.callback(
            Output('two-way_options', 'options'),
            [Input('interaction_effects_switch', 'value'),
            Input('two-way_options', 'value')],
            State('two-way_options', 'options')
        )
        def save_two_way_interaction_effects(switch_value, two_way_values, two_way_options): 
            output = list()
            if switch_value: 
                # Do we have any selected interaction effects to save? 
                if len(two_way_values) > 0: 
                    facts = list()
                    for o in two_way_options: 
                        facts.append(o['value'])
                        output.append({'label': o['label'], 'value': o['value'], 'disabled': True})
                        return output
                    
                    # TODO: Save interaction effects somewhere!
                    # is_sat = self.synthesizer.check_constraints(facts, rule_set='effects', design=self.design)
                    # if is_sat: 
                    #     self.synthesizer.update_with_facts(facts, rule_set='effects', design=self.design)
                    #     return output
                    # else: 
                    #     # TODO: Start a modal?
                    #     raise ValueError(f"Error in saving two-way interaction effects!")
                # No selected interaction effects to save
                else: 
                    for o in two_way_options: 
                        output.append({'label': o['label'], 'value': o['value'], 'disabled': True})
                    return output
            for o in two_way_options: 
                output.append({'label': o['label'], 'value': o['value'], 'disabled': False})
            
            return output
        
        @app.callback(
            Output('n-way_options', 'options'),
            [Input('interaction_effects_switch', 'value'),
            Input('n-way_options', 'value')],
            State('n-way_options', 'options')
        )
        def save_n_way_interaction_effects(switch_value, n_way_values, n_way_options): 
            output = list()
            if switch_value: 
                # Do we have any selected interaction effects to save? 
                if len(n_way_values) > 0: 
                    facts = list()
                    for o in n_way_options: 
                        facts.append(o['value'])
                        output.append({'label': o['label'], 'value': o['value'], 'disabled': True})
                        return output
                    # TODO: Save and verify interaction effect facts somewhere
                    # is_sat = self.synthesizer.check_constraints(facts, rule_set='effects', design=self.design)
                    # if is_sat: 
                    #     self.synthesizer.update_with_facts(facts, rule_set='effects', design=self.design)
                    #     return output
                    # else: 
                    #     # TODO: Start a modal?
                    #     raise ValueError(f"Error in saving n-way interaction effects!")
                # No selected interaction effects to save
                else: 
                    for o in n_way_options: 
                        output.append({'label': o['label'], 'value': o['value'], 'disabled': True})        
                    return output
            for o in n_way_options: 
                output.append({'label': o['label'], 'value': o['value'], 'disabled': False})
                
            return output
        
        @app.callback(
            [Output({'type': 'random_slope', 'index': ALL}, 'options'),
            Output({'type': 'random_intercept', 'index': ALL}, 'options'),
            Output({'type': 'correlated_random_slope_intercept', 'index': ALL}, 'options')],
            [Input('random_effects_switch', 'value'),
            Input({'type': 'random_slope', 'index': ALL}, 'value'),
            Input({'type': 'random_intercept', 'index': ALL}, 'value'),
            Input({'type': 'correlated_random_slope_intercept', 'index': ALL}, 'value')],
            [State({'type': 'random_slope', 'index': ALL}, 'options'),
            State({'type': 'random_intercept', 'index': ALL}, 'options'),
            State({'type': 'correlated_random_slope_intercept', 'index': ALL}, 'options')]
        )
        def save_random_effects(switch_value, random_slope_values, random_intercept_values, correlation_value, random_slope_options, random_intercept_options, correlation_options): 
            slope_output = list()
            intercept_output = list()
            correlation_output = list()
            if switch_value: 
                # Do we have any selected random slopes to save? 
                if len(random_slope_values) > 0: 
                    # TODO: Store (and verify) random slope values
                    pass
                for option in random_slope_options: 
                    o = option[0]
                    slope_output.append([{'label': o['label'], 'value': o['value'], 'disabled': True}])

                # Do we have any selected random intercepts to save? 
                if len(random_intercept_values) > 0: 
                    # TODO: Store (and verify) random slope values
                    pass
                for option in random_intercept_options: 
                    o = option[0]
                    intercept_output.append([{'label': o['label'], 'value': o['value'], 'disabled': True}])    
                
                # Do we have any selected correlations for random effects to save? 
                if correlation_value is not None: 
                    # TODO: Store (and verify) random slope values
                    pass
                for option in correlation_options: 
                    tmp_options = list()
                    o = option[0]
                    tmp_options.append({'label': o['label'], 'value': o['value'], 'disabled': True})
                    o = option[1]
                    tmp_options.append({'label': o['label'], 'value': o['value'], 'disabled': True})
                    correlation_output.append(tmp_options)
                return slope_output, intercept_output, correlation_output
            # else
            for option in random_slope_options: 
                o = option[0]
                slope_output.append([{'label': o['label'], 'value': o['value'], 'disabled': False}])       
            for option in random_intercept_options: 
                o = option[0]
                intercept_output.append([{'label': o['label'], 'value': o['value'], 'disabled': False}]) 
            for option in correlation_options: 
                assert(len(option) == 2)
                tmp_options = list()
                o = option[0]
                tmp_options.append({'label': o['label'], 'value': o['value'], 'disabled': False})
                o = option[1]
                tmp_options.append({'label': o['label'], 'value': o['value'], 'disabled': False})
                correlation_output.append(tmp_options)
            return slope_output, intercept_output, correlation_output

        @app.callback(
            Output('family_link_options', 'options'),
            [Input('family_link_switch', 'value'),
            State('family_link_options', 'options')],
        )
        def save_family_link(switch_value, family_link_options): 
            output = list() 
            if switch_value: 
                facts = list() 
                if family_link_options is not None: 
                    for o in family_link_options: 
                        facts.append(o['value'])
                        output.append({'label': o['label'], 'value': o['value'], 'disabled': True})
                    return output
                else: 
                    return family_link_options
                # check for SAT...
                # is_sat = self.synthesizer.check_constraints(facts, rule_set='effects', design=self.design)
                # if is_sat: 
                #     self.synthesizer.update_with_facts(facts, rule_set='effects', design=self.design)
                #     return output
                # else: 
                #     # TODO: Start a modal?
                #     raise ValueError(f"Error in saving main effects!")
            else: 
                if family_link_options is not None: 
                    for o in family_link_options: 
                        output.append({'label': o['label'], 'value': o['value'], 'disabled': False})

                    return output
                return family_link_options

        @app.callback(
            [Output({'type': 'random_slope', 'index': MATCH}, 'value'),
            Output({'type': 'random_intercept', 'index': MATCH}, 'value'),
            Output({'type': 'correlated_random_slope_intercept', 'index': MATCH}, 'value')],
            [Input({'type': 'random_slope', 'index': MATCH}, 'value'),
            Input({'type': 'random_intercept', 'index': MATCH}, 'value'),
            Input({'type': 'correlated_random_slope_intercept', 'index': MATCH}, 'value')],
            [State({'type': 'random_slope', 'index': MATCH}, 'options'),
            State({'type': 'random_intercept', 'index': MATCH}, 'options'),
            State({'type': 'correlated_random_slope_intercept', 'index': MATCH}, 'options')]
        )
        def sync_correlated_random_effects(slope_value, intercept_value, old_corr_value, slope_options, intercept_options, corr_options): 
            # TODO: Use the cache rather than string comparisons here?
            ctx = dash.callback_context
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            trigger_val = ctx.triggered[0]['value']

            slope_type = '"type":"random_slope"'
            intercept_type = '"type":"random_intercept"'
            correlated_type = '"type":"correlated_random_slope_intercept"'
            
            # Updated the slope selection 
            if slope_type in trigger_id:
                if len(trigger_val) > 0: 
                    if len(intercept_value) > 0: 
                        new_corr_value = corr_options[0]['value']
                        return slope_value, intercept_value, new_corr_value
                    return slope_value, list(), None
                else:
                    return slope_value, intercept_value, None
            elif intercept_type in trigger_id: 
                if len(trigger_val) > 0: 
                    assert(intercept_value is not None)
                    if len(slope_value) > 0: 
                        new_corr_value = corr_options[0]['value']
                        return slope_value, intercept_value, new_corr_value
                    else: 
                        return list(), intercept_value, None
                else: 
                    return slope_value, intercept_value, None
            elif correlated_type in trigger_id:
                new_slope_value = slope_options[0]['value']
                new_intercept_value = intercept_options[0]['value']
                return [new_slope_value], [new_intercept_value], old_corr_value

            # Nothing is selected
            raise PreventUpdate
                
        @app.callback(
            [Output(f"{i}_collapse", "is_open") for i in ['two-way', 'n-way']],
            [Input(f"{i}_toggle", "n_clicks") for i in ['two-way', 'n-way']],
            [State(f"{i}_collapse", "is_open") for i in ['two-way', 'n-way']],
        )
        def toggle_accordion(n1, n2, is_open1, is_open2):
            ctx = dash.callback_context

            if not ctx.triggered:
                return False, False
            else:
                button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "two-way_toggle" and n1:
                return not is_open1, is_open2
            elif button_id == "n-way_toggle" and n2:
                return is_open1, not is_open2
            return False, False

        @app.callback(
            Output('link_choice', 'options'),
            [
                Input('family_link_options', 'value'),
                Input('link_choice', 'options'),
            ],
        )
        def update_link_options(family, old_options): 
            global __value_to_z3__
            
            new_options = list()

            if family is not None: 
                # Get link options
                family_name = str(family)
                assert(family_name in __value_to_z3__.keys())
                family_fact = __value_to_z3__[family_name]
                link_options = self.get_link_options(family_fact)

                for link in link_options: 
                    __value_to_z3__[str(link)] = link
                    new_options.append({'label': str(link), 'value': str(link)})                    

                return new_options
            else: 
                raise PreventUpdate

        @app.callback(
            Output('data_dist', 'figure'),
            [
                Input('family_link_options', 'value'),
                Input('link_choice', 'value')
            ],
            State('data_dist', 'figure')
        )
        def update_chart_family(family, link, old_data): 
            global __value_to_z3__
            
            if family is not None: 
                assert(isinstance(family, str))
                family_fact = __value_to_z3__[family]

                # Get current data 
                (curr_data, curr_label) = self.get_data_dist()

                # Get data for family
                key = f'{family}_data'
                
                # Do we need to generate data?
                if key not in __value_to_z3__.keys(): 
                    family_data = generate_data_dist_from_facts(fact=family_fact, design=self.design)
                    # Store data for family in __value_to_z3__ cache
                    __value_to_z3__[key] = family_data
                # We already have the data generated in our "cache"
                else: 
                    family_data = __value_to_z3__[key]

                if link is not None: 
                    assert(isinstance(link, str))
                    link_fact = __value_to_z3__[link]
                    # Transform the data 
                    transformed_data = transform_data_from_fact(data=family_data, link_fact=link_fact)

                    # Create a new dataframe
                    # Generate figure 
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(x=curr_data, name=f'{self.design.dv.name}',))
                    fig.add_trace(go.Histogram(x=transformed_data, name=f'Simulated {family} distribution, {link} transformation.'))
                    fig.update_layout(barmode='overlay')
                    fig.update_traces(opacity=0.75)
                    fig.update_layout(legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ))

                    return fig
                else: 
                    raise PreventUpdate
            else: 
                raise PreventUpdate

        @app.callback(
            Output('generate_code', 'disabled'),
            [Input('main_effects_switch', 'value'),
            Input('interaction_effects_switch', 'value'),
            Input('random_effects_switch', 'value'),
            Input('family_link_switch', 'value'),]
        )
        def enable_code_generation(me_switch, i_switch, re_switch, fl_switch): 
            # If all the switches are turned on/True
            if me_switch and i_switch and re_switch and fl_switch: 
                return False # disabled: False
            return True # disable: True

        ##### Start and run app on local server
        self.app = app
        open_browser()
        app.run_server(debug=False, threaded=True, port=8081)
        
    def create_switch(self, switch_id: str, form_group_id: str): 
        switch = dbc.FormGroup([
                dbc.Checklist(
                    options=[
                        {"label": "🔐", "value": False}
                    ],
                    value=[],
                    id=switch_id,
                    switch=True,
                    style={'float': 'right'}
                ),
            ],
            id=form_group_id
        )

        return switch
        
    def layout_main_effects_div(self, main_effects: Dict[str, List[AbstractVariable]]): 
        ##### Collect all elements
        # Create main effects title 
        main_title = html.Div([
            html.H3('Main effects'),
            dbc.Alert(
                "TODO: Explanation of main effects", className="mb-0",
                id="main_alert",
                dismissable=True,
                fade=True, 
                is_open=True
            )
        ])
        
        # Get form groups for each set of main effects options
        input_fg, derived_direct_fg, derived_transitive_fg = self.populate_main_effects(main_effects)
        
        # Create main effects switch
        main_switch = self.create_switch(switch_id='main_effects_switch', form_group_id='main_effects_group')
        
        ##### Combine all elements
        # Create div 
        labels = list() 
        fg_combo = list()
        if len(input_fg.children[0].options) > 0: 
            labels.append(dbc.Col(self.create_label_tooltip('Specified', 'End-user has already specified these variables as independent variables.'), width=2))
            fg_combo.append(dbc.Col(input_fg, width=2))
        if len(derived_direct_fg.children[0].options) > 0: 
            labels.append(dbc.Col(self.create_label_tooltip('Derived directly', 'These are indepepdent variables that also cause or are associated with the dependent variable but were not specified.'), width=2))
            fg_combo.append(dbc.Col(derived_direct_fg, width=2))
        if len(derived_transitive_fg.children[0].options) > 0: 
            labels.append(dbc.Col(self.create_label_tooltip('Derived transitively', 'These are independent variables that may underlie independent variables that are already specified.'), width=2))
            fg_combo.append(dbc.Col(derived_transitive_fg, width=2))

        main_effects_div = html.Div([
                main_title,
                dbc.Row(labels),
                dbc.Row(fg_combo),
                main_switch
        ])

        ##### Return div
        return main_effects_div

    def layout_interaction_effects_div(self, interaction_effects): 
        ##### Collect all elements
        # Create interaction effects title 
        interaction_effects_title = html.Div([
            html.H3('Interaction effects'),
            dbc.Alert(
                "TODO: Explanation of interaction effects", className="mb-0",
                id="interaction_alert",
                dismissable=True,
                fade=True, 
                is_open=True
            )
        ])
        
        # Get accordion for the interaction effects (two-way, n-way)
        interaction_effects = self.populate_interaction_effects(interaction_effects)
        
        # Get chart for visualizing interactions
        # two_way_interaction_vis = self.create_two_way_interaction_chart(('HomeWork', 'Race'), self.design.dv, self.design.dataset.dataset)
        # three_way_interaction_vis = self.create_three_way_interaction_chart(('HomeWork', 'Race', 'SES'), self.design.dv, self.design.dataset.dataset)

        # Create interaction effects switch
        interaction_switch = self.create_switch(switch_id='interaction_effects_switch', form_group_id='interaction_effects_group')
        
        
        ##### Combine all elements
        # Create div 

        # interaction_effects_card = dbc.Card(
        #     dbc.CardBody(
        #         [
        #             html.H3("Interaction effects"),
        #             interaction_effects,
        #             interaction_switch
        #         ]
        #     ),
        #     color='light',
        #     outline=True
        # )

        interaction_effects_div = html.Div([
            interaction_effects_title, 
            interaction_effects,
            interaction_switch
        ])

        ##### Return div
        return interaction_effects_div

    def layout_random_effects_div(self, random_effects): 
        random_heading = html.H1(children='Random Effects')
        # random_effects = self.populate_random_effects()
        random_switch = dbc.FormGroup([
                dbc.Checklist(
                    options=[
                        {"label": "🔐", "value": False}
                        # {"label": "Save and lock random effects", "value": False}
                    ],
                    value=[],
                    id='random_effects_switch',
                    switch=True,
                    style={'float': 'right'}
                ),
            ],
            id='random_effects_group'
        )
    
        random_effects_card = dbc.Card(
                dbc.CardBody(
                    [
                        html.H3("Random effects"),
                        # random_effects,
                        random_switch
                    ]
                ),
                color='light',
                outline=True
            )



    def layout_family_link_div(self): 
        family_link_controls = self.make_family_link_options()
        family_link_chart = self.draw_data_dist()
        family_link_switch = dbc.FormGroup([
                dbc.Checklist(
                    options=[
                        {"label": "🔐", "value": False}
                        # {"label": "Save and lock random effects", "value": False}
                    ],
                    value=[],
                    id='family_link_switch',
                    switch=True,
                    style={'float': 'right'}
                ),
            ],
            id='family_link_group'
        )    

        family_and_link_card = dbc.Card(
                dbc.CardBody(
                    [
                        html.H3("Family and link functions"),
                        dbc.Row(
                            [
                                dbc.Col(family_link_chart, md=8),
                                dbc.Col(family_link_controls, md=4),
                            ],
                            align="center",
                        ),
                        family_link_switch
                    ]
                ),
                color='light',
                outline=True
            )
        
    # @param main_effects is a dictionary of pre-generated possible main effects
    def populate_main_effects(self, main_effects: Dict[str, List[AbstractVariable]]): 
        dv = self.design.dv # Might want to get rid of this
        output = list()

        # TODO: We could lay them out in separate divs for query | Tisane recommended | not included.
        # Lay main_effects options out
        input_options = list()
        input_selected = list()
        derived_direct_options = list()
        derived_transitive_options = list()
        for (tag, variables) in main_effects.items(): 
            for v in variables:
                # variable_options.append({'label': str(v.name), 'value': f'{FixedEffect(v.const, dv.const)}'})
                if tag == 'input':
                    input_options.append({'label': str(v.name), 'value': f'{FixedEffect(v.const, dv.const)}'})
                    input_selected.append(f'{FixedEffect(v.const, dv.const)}')
                elif tag == 'derived_direct':
                    derived_direct_options.append({'label': str(v.name), 'value': f'{FixedEffect(v.const, dv.const)}'})
                elif tag == 'derived_transitive':
                    derived_transitive_options.append({'label': str(v.name), 'value': f'{FixedEffect(v.const, dv.const)}'})
                # variable_options.append({'label': str(v.name), 'value': f'{FixedEffect(v.name, dv.name)}'})
        
        input_fg = dbc.FormGroup([
            dbc.Checklist(
                options=input_options,
                value=input_selected,
                id="main_effects_options"
            ),
        ])
        derived_direct_fg = dbc.FormGroup([
            dbc.Checklist(
                options=derived_direct_options, 
                value=[],
                id='derived_direct_options'
            )
        ])
        derived_transitive_fg = dbc.FormGroup([
            dbc.Checklist(
                options=derived_transitive_options, 
                value=[],
                id='derived_transitive_options'
            )
        ])

        return input_fg, derived_direct_fg, derived_transitive_fg

    def populate_interaction_effects(self, interaction_effects: List[Tuple[AbstractVariable, ...]]): 
        vis_charts = list()
        output = list()

        # Build Summary checklist

        # Lay them out
        for (num_interactions, options) in interaction_effects.items(): 
            interaction_options = list()
            for ixn in options:
                ixn_names = [v.name for v in ixn]
                name = '*'.join(ixn_names)
                interaction_options.append({'label': name, 'value': str(name)}) # TODO: Update the value
            
            # output.append(self.make_interaction_card(title=num_interactions, options=interaction_options))
                
                chart = self.make_interaction_vis(title=f'{num_interactions} visualized', interaction=ixn)
                # vis_charts.append(chart)
                vis_charts.append(dbc.Col(chart, className='w-50'))
            
            # summary_card = self.make_interaction_summary_card(title=num_interactions, options=interaction_options)
            # vis_card = self.make_interaction_vis_card(title=num_interactions, vis_cards=vis_charts)
            # output.append(summary_card)
            # output.append(vis_card)
            # output.append(vis_charts)

        # Format vis_chars to so that there are only two per row
        chart_rows = list()
        i = 0 
        while i in range(len(vis_charts)): 
            if i + 1 < len(vis_charts): 
                row = dbc.Row([vis_charts[i], vis_charts[i+1]])
                i+=2
            else: 
                row = dbc.Row([vis_charts[i]])
                i+=1
            chart_rows.append(row)
            
        return html.Div(chart_rows)
    
    def create_two_way_interaction_chart(self, interaction: Tuple[AbstractVariable, AbstractVariable], dv: AbstractVariable, data: pd.DataFrame):
        assert(len(interaction) == 2)
        (x1, x2) = interaction 
        if isinstance(x1, Numeric) and isinstance(x2, Nominal): 
            x = x1
            color_group = x2
        elif isinstance(x1, Numeric) and isinstance(x2, Ordinal): 
            x = x1
            color_group = x2
        elif isinstance(x1, Numeric) and isinstance(x2, Numeric): 
            x1_data = self.design.get_data(x1)
            x2_data = self.design.get_data(x2)
            
            if x1_data.count() <= x2_data.count(): 
                x = x2
                color_group = x1
            else: 
                x = x1
                color_group = x2
        elif isinstance(x1, Nominal) and isinstance(x2, Numeric):
            x = x2
            color_group = x1
        elif isinstance(x1, Nominal) and isinstance(x2, Ordinal): 
            x = x2
            color_group = x1
        elif isinstance(x1, Ordinal) and isinstance(x2, Numeric): 
            x = x1
            color_group = x2
        elif isinstance(x1, Ordinal) and isinstance(x2, Ordinal): 
            x = x1
            color_group = x2
        else: 
            x = x1
            color_group = x2
        
        fig = px.line(data, x=x.name, y=dv.name, color=color_group.name)

        fig_elt = dcc.Graph(id=f'two_way_interaction_chart_{x.name}_{color_group.name}', figure=fig)        
        
        return fig_elt

    def create_three_way_interaction_chart(self, interaction: Tuple[AbstractVariable, AbstractVariable, AbstractVariable], dv: AbstractVariable, data: pd.DataFrame):
        assert(len(interaction) == 3)
        x = interaction[0]
        color_group = interaction[1]
        facet = interaction[2]
        fig = px.line(data, x=x.name, y=dv.name, color=color_group.name, facet_col=facet.name)

        fig_elt = dcc.Graph(id=f'three_way_interaction_chart_{x.name}_{color_group.name}_{facet.name}', figure=fig)        
        
        return fig_elt

    def populate_random_effects(self): 
        # Could be random slope OR random interaction 
        output = list()
        # Get possible main effects from synthesizer
        possible_random_effects = self.synthesizer.generate_random_effects(design=self.design)

        # TODO: We could lay them out in separate divs for query | Tisane recommended | not included.
        # Lay them out
        for (key, facts) in possible_random_effects.items():
            slope = self.make_random_slope_card(variables=key, value=facts[0])
            intercept = self.make_random_intercept_card(variables=key, value=facts[1])
            # TODO: Generate Correlated and Uncorrelated in synthesizer???
            corr_options = dbc.RadioItems(options=[{'label': 'Correlated random slope and intercept', 'value': f'Correlated({slope}, {intercept})'}, {'label': 'Uncorrelated random slope and intercept', 'value': f'Uncorrelated({slope}, {intercept})'}], id={'type': 'correlated_random_slope_intercept', 'index': f'{key}'}, inline=True)
            div = html.Div([
                html.H5(f'{key}'),
                # dbc.Row([dbc.Col(children=[html.H5(f'{key}')], align='start'), corr_options]),
                dbc.Row([dbc.Col(slope, className='w-50'), dbc.Col(intercept, className='w-50')]),
                dbc.Row([dbc.Col(corr_options)], justify='end'),
            ])
            output.append(div)
                # output.append(dbc.Row([dbc.Col(slope, width=4), dbc.Col(intercept, width=4)]))
                # output.append(self.make_random_checklist(label=key, options=facts))
            
            # TODO: correlate should only be an option if both are selected

        # return output
        return html.Div(id='random_effects_div', children=output)
    
    def get_data_dist(self): 
        dv = self.design.dv
        
        data = self.design.get_data(variable=dv)
        
        if data is not None: 
            hist_data = data
            labels = dv.name
        else: 
            raise NotImplementedError
        
        return (hist_data, labels)

    def draw_dist(self, hist_data, label): 
        data = pd.DataFrame(hist_data, columns=[label])

        fig = px.histogram(data, x=label)
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ))

        fig_elt = dcc.Graph(id='data_dist', figure=fig)

        return fig_elt
        
    def draw_data_dist(self): 
        (hist_data, labels) = self.get_data_dist()

        return self.draw_dist(hist_data, labels)

    def populate_data_distributions(self): 
        output = list() 

        (data, labels) = self.get_possible_family_distributions()

        # fig = px.histogram(family_data, x=f"{Value of self.design.dv.name}", y="frequency", color="dist", marginal="rug",
        #                 hover_data=df.columns)

        fig = ff.create_distplot(data, labels, showlegend=False)
        output.append(html.Div([
            html.H3(str(dist)),  
            dcc.Graph(figure=fig)
            ]))

        return html.Div(output)
    
    def get_possible_family_distributions(self): 
        dist_names = self.synthesizer.generate_family_distributions(design=self.design)

        data = list()
        labels = list()
        for dist in dist_names: 
            data.append(generate_data_dist_from_facts(fact=dist, design=self.design))
            labels.append(f'{self.design.dv.name} with {dist}')

        return (data, labels)    

    def get_data_for_family_distribution(self, family_fact: z3.BoolRef): 
        global __value_to_z3__

        key = f'{str(family_fact)}_data'
        if key in __value_to_z3__.keys(): 
            return __value_to_z3__[key]
        else: 
            val = generate_data_dist_from_facts(fact=family_fact, design=self.design)
            __value_to_z3__[key] = val
            return val

    def populate_compound_family_div(self): 

        (curr_data_dist, curr_data_label) = self.get_data_dist()

        (possible_family_dists, possible_family_labels) = self.get_possible_family_distributions()

        # Combine data
        data = curr_data_dist + possible_family_dists
        labels = curr_data_label + possible_family_labels 

        fig = ff.create_distplot(data, labels)
        fig_div = html.Div([
            # html.H3(str(dist)),  
            dcc.Graph(figure=fig)
            ])

        return fig_div

    # TODO: Need to add callbacks to this...
    def populate_link_div(self): 
        output = list()

        # Get Family: Link functions
        dist_link_dict = dict()
        dist_names = self.synthesizer.generate_family_distributions(design=self.design)
        for dist in dist_names: 
            dist_link_dict[dist] = self.get_link_options(dist)

        for family, links in dist_link_dict.items(): 
            options = list() 
            for l in links: 
                default = None # TODO: Start at default (Identity usually)
                options.append({'label': f'{str(l)}', 'value': str(l)})

            # Create HTML div
            output.append(dbc.FormGroup(
                [
                    dbc.Label(f'{str(family)}', 
                        # style={'visibility': 'hidden'}
                    ),
                    dbc.RadioItems(
                        id=f'{str(family)}_link_options',
                        options=options,
                        value=None, # TODO: Start at default (Identity usually)
                        inline=True,
                        # style={'visibility': 'hidden'}
                    ),
                ]
            ))
        return html.Div(output)

    def create_label_tooltip(self, label: str, description: str): 
        name = label.replace(' ', '_')
        tooltip = html.Div(
            [
                html.P(
                    [
                        html.Span(
                            label,
                            id=f'{name}_tooltip_target',
                            style={"textDecoration": "underline", "cursor": "pointer"},
                        )
                    ]
                ),
                dbc.Tooltip(
                    description,
                    target=f'{name}_tooltip_target',
                )
            ]
        )   

        return tooltip

    def create_main_effects_div(self, input_fg, derived_direct_fg, derived_transitive_fg, main_title, main_switch): 
        labels = list() 
        fg_combo = list()
        if len(input_fg.children[0].options) > 0: 
            # TODO: Start here: Add tooltips to all 
            labels.append(dbc.Col(self.create_label_tooltip('Specified', 'End-user has already specified these variables as independent variables.'), width=2))
            fg_combo.append(dbc.Col(input_fg, width=2))
        if len(derived_direct_fg.children[0].options) > 0: 
            labels.append(dbc.Col(self.create_label_tooltip('Derived directly', 'These are indepepdent variables that also cause or are associated with the dependent variable but were not specified.'), width=2))
            fg_combo.append(dbc.Col(derived_direct_fg, width=2))
        if len(derived_transitive_fg.children[0].options) > 0: 
            labels.append(dbc.Col(self.create_label_tooltip('Derived transitively', 'These are independent variables that may underlie independent variables that are already specified.'), width=2))
            fg_combo.append(dbc.Col(derived_transitive_fg, width=2))

        main_effects_div = html.Div([
                main_title,
                dbc.Row(labels),
                dbc.Row(fg_combo),
                main_switch
        ])

        return main_effects_div

    def get_link_options(self, family_fact: z3.BoolRef): 
         
        link_functions = self.synthesizer.generate_link_functions(design=self.design, family_fact=family_fact)

        return link_functions
    
    def make_family_options(self): 
        global __value_to_z3__ 

        options = list()

        dist_names = self.synthesizer.generate_family_distributions(design=self.design)

        for d in dist_names: 
            __value_to_z3__[str(d)] = d
            options.append({'label': str(d), 'value': str(d)})
        
        return options

    def make_family_link_options(self): 
        family_options = self.make_family_options()

        controls = dbc.Card(
            [
                dbc.FormGroup(
                    [
                        dbc.Label('Family'),
                        dcc.Dropdown(
                            id='family_link_options',
                            options=family_options,
                            value=None,
                        ),
                    ]
                ),
                dbc.FormGroup(
                    [
                        dbc.Label('Link function'),
                        dcc.Dropdown(
                            id='link_choice',
                            options=[],
                            value=None,
                        ),
                    ]
                )
            ],
            body=True,
        )

        return controls

    def make_interaction_vis_card(self, title: str, vis_cards: List[dbc.Card]): 
        card = dbc.Card([
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        f"{title}",
                        color="link",
                        id=f"{title}_vis_toggle",
                    )
                )
            ),
            dbc.Collapse(
                vis_cards,
                id=f'{title}_vis_collapse'
            )
        ])
        return card

    def make_interaction_summary_card(self, title: str, options: List): 
        card = dbc.Card([
            dbc.CardHeader(
                html.H2(
                    dbc.Button(
                        f"{title}",
                        color="link",
                        id=f"{title}_toggle",
                    )
                )
            ),
            dbc.Collapse(
                dbc.FormGroup([
                    dbc.Checklist(
                        options=options,
                        value=[],
                        id=f"{title}_options",
                        labelStyle={'disabled': True}
                    ),
                ]),
                id=f'{title}_collapse'
            )
        ])
        return card

    def make_interaction_vis(self, title: str, interaction: Tuple[AbstractVariable, ...]): 
        # Create vis 
        fig = None
        if len(interaction) == 2: 
            fig = self.create_two_way_interaction_chart(interaction, self.design.dv, self.design.dataset.dataset)
        elif len(interaction) == 3: 
            fig = self.create_three_way_interaction_chart(interaction, self.design.dv, self.design.dataset.dataset)
        else: 
            pass
            # fig = None

        # Add it to cards 
        names = [v.name for v in interaction]
        interaction_name = '*'.join(names)
        card = dbc.Card([
            dbc.CardHeader([dbc.Checklist(options=[{'label': f'{interaction_name}', 'value': f'{interaction_name}'}], id={'type': 'interaction_vis', 'index': f'{interaction_name}'}, value=[])]),
            dbc.CardBody([
                fig
            ])
        ])

        return card

    def make_random_slope_card(self, variables: str, value: str):
        var_names = variables.split(',')
        base = var_names[0]
        group = var_names[1]
        card = dbc.Card([
            dbc.CardHeader([dbc.Checklist(options=[{'label': 'Random slope', 'value': f'{value}'}], id={'type': 'random_slope', 'index': f'{variables}'}, value=[])]),
            dbc.CardBody([
                html.P(f'Does each {base} within {group} differ in their impact on the dependent variable?'),
                # dbc.Checklist(options=[{'label': 'Include', 'value': f'{value}'}], id=f'{value}_slope')
            ])
        ])

        return card
    
    def make_random_intercept_card(self, variables: str, value: str):
        var_names = variables.split(',')
        base = var_names[0]
        group = var_names[1]
        card = dbc.Card([
            dbc.CardHeader([dbc.Checklist(options=[{'label': 'Random intercept', 'value': f'{value}'}], id={'type': 'random_intercept', 'index': f'{variables}'}, value=[])]),
            dbc.CardBody([
                html.P(f'Does each {base} within {group} differ on average on the dependent variable?')
            ])
        ])

        return card

    def make_random_checklist(self, label: str, options: List): 
        checklist = dbc.FormGroup([
            dbc.Label(label),
            dbc.Checklist(
                options=[
                    {'label': 'Random slope', 'value': f'{options[0]}'},
                    {'label': 'Random intercept', 'value': f'{options[1]}'},
                    {'label': 'Correlated random slope & intercept', 'value': f'{options[2]}'}
                ],
                value=[],
                labelStyle={'display': 'inline-block'}
            )  
        ])
        return checklist
            # TODO: correlate should only be an option if both are selected

    
    @classmethod
    def ask_inclusion_prompt(cls, subject: str) -> bool: 

        prompt = f'Would you like to include {subject}?'
        choices = f' Y or N: '

        while True: 
            ans = add_inclusion_prompt(prompt=prompt, choices=choices)
            if ans.upper() == 'Y': 
                return ans.upper()
            elif ans.upper() == 'N': 
                return ans.upper()
            else: 
                pass
    
    @classmethod
    def ask_inclusion(cls, subject: str) -> bool: 
    
        ans = cls.ask_inclusion_prompt(subject)

        if ans.upper() == 'Y':
            # TODO: write to a file here 
            return True
        elif ans.upper() == 'N': 
            return False
        else: 
            pass
    
    # TODO: Format the interactions to be more readable
    @classmethod 
    def format_options(cls, options: List) -> List: 
        return options

    @classmethod
    def ask_multiple_choice_prompt(cls, options: List) -> Any: 
        prompt = f'These cannot be true simultaneously.'
        formatted_options = cls.format_options(options)
        choices = f' Pick index (starting at 0) to select option in: {formatted_options}: '
        while True: 
            idx = int(input(prompt + choices))
            # st.write()

            if idx in range(len(options)): 
                # only keep the constraint that is selected. 
                constraint = options[idx] 
                print(f'Ok, going to add {constraint} and remove the others.')
                return idx
            else:
                print(f'Pick a value in range')
                pass
    
    @classmethod
    def resolve_unsat(cls, facts: List, unsat_core: List) -> List: 
        idx = cls.ask_multiple_choice_prompt(options=unsat_core)
    
        return unsat_core[idx]

    # TODO: Format options for specifying family of a distribution
    @classmethod
    def format_family(cls, options: List): 
        return options
    
    @classmethod
    def ask_family_prompt(cls, options: List, dv: AbstractVariable): 
        prompt = f'Which distribution best approximates your dependent variable {dv}?'
        formatted_options = cls.format_options(options)
        choices = f' Pick index (starting at 0) to select option in: {formatted_options}: '

        while True: 
            idx = int(input(prompt + choices))

            if idx in range(len(options)): 
                # only keep the constraint that is selected. 
                constraint = options[idx] 
                print(f'Ok, going to add {constraint} and remove the others.')
                return idx
            else:
                print(f'Pick a value in range')
                pass
    
    @classmethod
    def ask_family(cls, options: List, dv: AbstractVariable): 
        idx = cls.ask_family_prompt(options=options, dv=dv)

        return options[idx]

    @classmethod
    def ask_link_prompt(cls, options: List, dv: AbstractVariable): 
        prompt = f'W'


    @classmethod
    def ask_link(cls, options: List, dv: AbstractVariable): 
        idx = cls.ask_link_prompt(options=options, dv=dv)

        return options[idx]

    # @classmethod
    # def ask_change_default_prompt(cls, subject: str, default: str, options: List): 
    #     prompt = f'The default {subject} is {default}. Would you like to change it to one of {options}?'

    # @classmethod
    # def ask_change_default(cls, subject: str, default: str, options: List): 
    #     idx = cls.ask_change_default_prompt(subject=subject, default=default, options=options)
    #     pass