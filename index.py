from __future__ import absolute_import
from __future__ import print_function

from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt

from app import app, layout

app.layout = html.Div([
    # Component that manages page routing based on the URL
    dcc.Location(id='url', refresh=False),
    # Dummy table to load JS/CSS for table
    html.Div(children=[dt.DataTable(id='dummy-table', rows=[{}])],
             style={'display': 'none'}),
    # Div which will contain all page content
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    # This app only has one page. Learn about multi-page apps:
    # https://plot.ly/dash/urls
    return layout()


if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)
