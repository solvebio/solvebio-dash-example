# -*- coding: utf-8 -*-
import flask
import plotly.graph_objs as go
import numpy as np


def gene_expression_charts(gene):
    if not gene:
        return []

    dataset_id = ('solvebio:public:'
                  '/ICGC/1.0.0-17/ExpressionSequencing')
    gene_field = 'gene_id'
    cancer_type_field = 'project_code'
    # count_field = 'normalized_read_count'
    count_field = 'raw_read_count'

    dataset = flask.g.client.Dataset.get_by_full_path(dataset_id)
    facets = dataset.query().facets(**{
        cancer_type_field: {'limit': 1000}
    })

    records = []
    for f in facets[cancer_type_field]:
        records.append({
            'cancer_type': f[0],
            'count': f[1],
            'gene': gene,
            'dataset': dataset_id,
            'gene_field': gene_field,
            'cancer_type_field': cancer_type_field,
            'count_field': count_field
        })

    fields = [
        {
            'name': 'read_counts',
            'data_type': 'double',
            'is_list': True,
            'ordering': 1,
            'expression': """
                dataset_field_values(
                  record.dataset,
                  record.count_field,
                  limit=10000,
                  filters=[
                    [record.gene_field, record.gene],
                    [record.cancer_type_field, record.cancer_type]
                ])
            """
        }
    ]

    # Sort by cancer_type and annotate
    records = list(flask.g.client.Annotator(fields).annotate(records))

    # One chart for each cancer/project type
    charts = []
    for r in records:
        charts.append(go.Box(
            y=[np.log2(c + 1) for c in r['read_counts']],
            name=r['cancer_type'],
            showlegend=False
        ))

    charts = sorted(charts, key=lambda c: np.median(c.y))
    charts.reverse()

    return charts
