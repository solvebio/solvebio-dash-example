# -*- coding: utf-8 -*-
from dash_solvebio_auth.solvebio_dash import SolveBioDash

from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import flask
import os

from charts import variants
from charts import cnv
from charts import expression

# Initialize the Dash app with SolveBio auth.
app = SolveBioDash(__name__, title='Example Dash App')

# Dash CSS
app.css.append_css({
    "external_url": "//codepen.io/chriddyp/pen/bWLwgP.css"
})

# Loading screen CSS
app.css.append_css({
    "external_url": "//codepen.io/chriddyp/pen/brPBPO.css"
})


def current_user():
    user = flask.g.client.User.retrieve()
    return [
        html.Div(children='Logged-in as: {}'.format(user.full_name))
    ]


def layout():
    return html.Div(children=[
        html.Div(children=[
            html.H1(children='Example Dash App'),
            html.P(children=current_user()),
        ]),

        # Gene list selector
        html.Div(children=[
            html.Div(children=[
                html.Label(children='Gene'),
                dcc.Input(id='gene-list', value='EGFR', type='text')
            ]),
            html.Button('Run Analysis', id='run-button')
        ]),

        html.Div([
            html.Div([
                html.H3('Mutation Frequencies'),
                dcc.Graph(id='graph-mutation-frequencies-total-pop'),
                dcc.Graph(id='graph-mutation-frequencies-mutant-pop')
            ]),

            html.Div([
                html.H3('Gene Expression'),
                dcc.Graph(id='graph-gene-expression')
            ]),

            html.Div([
                html.H3('Copy Number Frequencies'),
                dcc.Graph(id='graph-copy-number-frequencies')
            ])
        ])
    ], className="container")


@app.callback(
    Output(component_id='graph-mutation-frequencies-total-pop',
           component_property='figure'),
    [Input(component_id='run-button', component_property='n_clicks')],
    [State(component_id='gene-list', component_property='value')]
)
def _mutation_frequencies_total_pop(*args):
    if not all(args):
        return []

    clicks, genes = args
    genes = [g.strip() for g in genes.replace(',', ' ').split()]
    charts = variants.mutation_frequency_total_population_charts(genes[0])

    return go.Figure(
        data=charts,
        layout=go.Layout(
            title='Proportion of mutation types (total pop.): {}'
            .format(genes[0]),
            barmode='stack',
            height=600,
            xaxis=dict(
                title='Percentage Frequency'
            ),
            yaxis=dict(
                title='Cancer Type'
            )
        )
    )


@app.callback(
    Output(component_id='graph-mutation-frequencies-mutant-pop',
           component_property='figure'),
    [Input(component_id='run-button', component_property='n_clicks')],
    [State(component_id='gene-list', component_property='value')]
)
def _mutation_frequencies_mutant_pop(*args):
    if not all(args):
        return []

    clicks, genes = args
    genes = [g.strip() for g in genes.replace(',', ' ').split()]
    charts = variants.mutation_frequency_mutant_population_charts(genes[0])

    return go.Figure(
        data=charts,
        layout=go.Layout(
            title='Proportion of mutation types (mutant pop.): {}'
            .format(genes[0]),
            barmode='stack',
            height=600,
            xaxis=dict(
                title='Percentage Frequency'
            ),
            yaxis=dict(
                title='Cancer Type'
            )
        )
    )


@app.callback(
    Output(component_id='graph-gene-expression',
           component_property='figure'),
    [Input(component_id='run-button', component_property='n_clicks')],
    [State(component_id='gene-list', component_property='value')]
)
def _gene_expression(*args):
    if not all(args):
        return []

    clicks, genes = args
    genes = [g.strip() for g in genes.replace(',', ' ').split()]
    charts = expression.gene_expression_charts(genes[0])

    return go.Figure(
        data=charts,
        layout=go.Layout(
            title='mRNA Gene Expression by Cancer Type: {}'.format(genes[0]),
            height=1000,
            xaxis=dict(
                title='Cancer Type (Project Code)'
            ),
            yaxis=dict(
                title='Gene Expression'
            )
        )
    )


@app.callback(
    Output(component_id='graph-copy-number-frequencies',
           component_property='figure'),
    [Input(component_id='run-button', component_property='n_clicks')],
    [State(component_id='gene-list', component_property='value')]
)
def _copy_number_frequencies(*args):
    if not all(args):
        return []

    clicks, genes = args
    genes = [g.strip() for g in genes.replace(',', ' ').split()]
    charts = cnv.copy_number_frequency_charts(hugo_gene=genes[0])

    return go.Figure(
        data=charts,
        layout=go.Layout(
            title='Copy-Number Change (ICGC - Limited Data): {}'
            .format(genes[0]),
            barmode='stack',
            height=1000,
            xaxis=dict(
                title='Frequency of Copy-Number Change'
            ),
            yaxis=dict(
                title='Cancer Type (Project Code)'
            )
        )
    )
