# -*- coding: utf-8 -*-
import flask
import plotly.graph_objs as go


def copy_number_frequency_charts(hugo_gene):
    if not hugo_gene:
        return []

    dataset_id = ('solvebio:public:'
                  '/ICGC/2.0.0-21/CopyNumberSomaticMutation-GRCh37')
    gene_field = 'gene_affected'  # Ensembl code
    mutation_type_field = 'mutation_type'
    cancer_type_field = 'project_code'

    # Convert HUGO gene to Ensembl
    hgnc = flask.g.client.Dataset.get_by_full_path(
        'solvebio:public:/HGNC/3.1.1-2017-08-28/HGNC')
    gene = None
    for res in hgnc.query().filter(
            gene_symbol=hugo_gene,
            ensembl_gene_id__prefix='ENSG'):
        gene = res.get('ensembl_gene_id')
        break

    if gene is None:
        print('[CNV] Could not convert HUGO gene to Ensembl: {}'
              .format(hugo_gene))
        return []

    dataset = flask.g.client.Dataset.get_by_full_path(dataset_id)
    facets = dataset.query().facets(**{
        mutation_type_field: {'limit': 1000},
        cancer_type_field: {'limit': 1000}
    })
    mutation_types = [m[0] for m in facets[mutation_type_field]]

    records = []
    for f in facets[cancer_type_field]:
        records.append({
            'cancer_type': f[0],
            'count': f[1],
            'gene': gene,
            'dataset': dataset_id,
            'gene_field': gene_field,
            'mutation_types': ','.join(mutation_types),
            'cancer_type_field': cancer_type_field,
            'mutation_type_field': mutation_type_field
        })

    fields = [
        {
            'name': 'total_mutations',
            'data_type': 'integer',
            'is_list': False,
            'ordering': 1,
            'expression': """
                dataset_count(
                  record.dataset,
                  filters=[
                    [record.gene_field, record.gene],
                    [record.cancer_type_field, record.cancer_type]
                ])
            """
        },
        {
            'name': 'mutation_frequencies',
            'data_type': 'object',
            'is_list': True,
            'ordering': 2,
            'expression': """
            [
                {
                    "frequency":
                    i["count"] / float(record.total_mutations) * 100.0,
                    "type": i["term"]
                }
                for i in dataset_field_top_terms(
                  record.dataset,
                  record.mutation_type_field,
                  limit=100,
                  filters=[
                     [record.gene_field, record.gene],
                     [record.cancer_type_field, record.cancer_type]
                  ]
                )
            ]
            """
        }
    ]

    # Sort by cancer_type and annotate
    records = sorted(records, key=lambda k: k['cancer_type'])
    records.reverse()
    records = list(flask.g.client.Annotator(fields).annotate(records))

    # One Bar chart for each mutation type
    charts = []
    for mt in mutation_types:
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
            # marker=dict(
            #     color=palette[mt]
            # )
        ))

    return charts
