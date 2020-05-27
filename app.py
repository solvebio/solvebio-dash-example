# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import plotly.graph_objs as go
import flask

from solvebio.contrib.dash import SolveBioDash


import solvebio as sb

sb.login(api_host="https://solvebio.api.solvebio.com")

# Initialize the Dash app with SolveBio auth.
app = SolveBioDash(
    __name__,
    title='Example Dash App',
    # client_id='<YOUR CLIENT ID HERE>',
    salt='example-dash-app',
    suppress_callback_exceptions=True)

app.layout = html.Div([
    # Component that manages page routing based on the URL
    dcc.Location(id='url', refresh=False),
    # Div which will contain all page content
    html.Div(id='page-content')
])


def current_user():
    if app.auth:
        user = flask.g.client.User.retrieve()
        return [
            html.Div(children='Logged-in as: {}'.format(user.full_name)),
            html.A('Log out', href='/_dash-logout')
        ]
    else:
        return [
            html.P('(SolveBio Auth not configured)')
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
            html.Button('Go!', id='run-button')
        ]),

        html.Div([
            html.Div([
                html.H3('Mutation Frequencies'),
                dcc.Graph(id='graph-mutation-frequencies'),
            ])
        ])
    ], className="container")


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    # This app only has one page. Learn about multi-page apps:
    # https://plot.ly/dash/urls
    return layout()


@app.callback(
    Output(component_id='graph-mutation-frequencies',
           component_property='figure'),
    [Input(component_id='run-button', component_property='n_clicks')],
    [State(component_id='gene-list', component_property='value')]
)
def mutation_frequencies_total_pop(clicks, genes):
    genes = [g.strip() for g in genes.replace(',', ' ').split()]
    charts = mutation_frequency_total_population_charts(genes[0])

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


def mutation_frequency_total_population_charts(gene, **kwargs):
    dataset_id = 'solvebio:public:/TCGA/1.2.0-2015-02-11/SomaticMutationsBest-GRCh37'
    cancer_type_field = 'cancer_abbreviation'
    mutation_type_field = 'variant_classification'
    sample_field = 'patient_barcode'
    mutation_types = [
        'Missense Mutation',
        'Splice Site',
        'Frame Shift Del',
        'Nonsense Mutation',
        'Frame Shift Ins',
        'In Frame Ins',
        'In Frame Del',
        '5\'UTR',
        '3\'UTR',
        'Nonstop Mutation',
        'UTR'
    ]
    palette = {
        'Missense Mutation': '#57b76e',
        'Nonstop Mutation':  '#a2773c',
        'Splice Site':       '#83b73d',
        'Frame Shift Del':   '#697dcc',
        'Nonsense Mutation': '#d1a33d',
        'Frame Shift Ins':   '#bd70a7',
        'In Frame Ins':      '#68833d',
        'In Frame Del':      '#cb4370',
        '5\'UTR':            '#4cb5af',
        '3\'UTR':            '#cc5231',
        'UTR':               '#cf7568',
        'No Mutation':       '#dddddd'
    }

    fields = [
        {
            'name': 'total_mutations',
            'data_type': 'integer',
            'is_list': False,
            'ordering': 1,
            'expression': """
                dataset_count(
                     dataset,
                     entities=[["gene", gene]],
                     filters=[
                       [cancer_type_field, record.cancer_type],
                       [mutation_type_field + "__in", mutation_types.split(",")]
                     ]
                )
            """
        },
        {
            'name': 'samples_with_mutations',
            'data_type': 'float',
            'is_list': False,
            'expression': """
                dataset_field_terms_count(
                    dataset,
                    field=sample_field,
                    entities=[["gene", gene]],
                    filters=[
                      [cancer_type_field, record.cancer_type],
                      [mutation_type_field + "__in", mutation_types.split(",")]
                    ]
                )
            """
        },
        {
            'name': 'total_samples',
            'data_type': 'float',
            'is_list': False,
            'expression': """
                dataset_field_terms_count(
                    dataset,
                    field=sample_field,
                    filters=[
                      [cancer_type_field, record.cancer_type]
                    ]
                )
            """
        },
        {
            'name': 'mutation_frequencies',
            'data_type': 'object',
            'is_list': True,
            'depends_on': ['total_mutations', 'samples_with_mutations', 'total_samples'],
            'expression': """
                [
                  {
                    "frequency": (i["count"] / float(record.total_mutations)) *
                                  (float(record.samples_with_mutations) /
                                   float(record.total_samples)) * 100.0,
                    "type": i["term"]
                  }
                  for i in dataset_field_top_terms(
                    dataset,
                    mutation_type_field,
                    limit=100,
                    entities=[["gene", gene]],
                    filters=[
                      [cancer_type_field, record.cancer_type],
                      [mutation_type_field + "__in", mutation_types.split(",")]
                    ])
                ] + [{
                  "frequency": float(record.total_samples - record.samples_with_mutations) /
                               float(record.total_samples) * 100.0,
                  "type": "No Mutation"
                }]
            """
        }
    ]

    dataset = flask.g.client.Dataset.get_by_full_path(dataset_id)
    facets = dataset.query().facets(**{
        cancer_type_field: {'limit': 1000},
        mutation_type_field: {'limit': 1000}
    })

    records = []
    for f in facets[cancer_type_field]:
        records.append({
            'cancer_type': f[0],
            'count': f[1],
        })

    # Sort by cancer_type and annotate
    records = sorted(records, key=lambda k: k['cancer_type'])
    records.reverse()
    data = {
        'gene': gene,
        'dataset': dataset_id,
        'mutation_types': ','.join(mutation_types),
        'cancer_type_field': cancer_type_field,
        'mutation_type_field': mutation_type_field,
        'sample_field': sample_field
    }
    ann = flask.g.client.Annotator(fields, include_errors=True, data=data)
    records = list(ann.annotate(records))

    # One Bar chart for each mutation type
    charts = []
    for mt in ['No Mutation'] + mutation_types:
        # For each mutation type, get the frequency per-cancer-type.
        # {name: mutation-type, data: [value-per-cancer-type]}

        data = []
        for r in records:
            f = [f for f in r['mutation_frequencies'] if f['type'] == mt]
            if f:
                data.append(f[0]['frequency'])
            else:
                data.append(0)

        charts.append(go.Bar(
            y=[r['cancer_type'] for r in records],
            x=data,
            name=mt,
            orientation='h',
            textposition='auto',
            # Only show hover tooltips if there is visible data
            hoverinfo=['all' if d else 'none' for d in data],
            marker=dict(
                color=palette[mt]
            )
        ))

    return charts


if __name__ == '__main__':
    app.run_server(debug=True)
