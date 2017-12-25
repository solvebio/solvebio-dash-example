import plotly.graph_objs as go
import flask


CONFIG = dict(
    dataset_id=('solvebio:public:'
                '/TCGA/1.2.0-2015-02-11/SomaticMutationsBest-GRCh37'),
    cancer_type_field='cancer_abbreviation',
    mutation_type_field='variant_classification',
    sample_field='patient_barcode',

    # Hard-code the mutation types in TCGA, since there are some others
    # we don't want to see.
    mutation_types=[
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
    ],
    palette={
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
)


def mutation_frequency_total_population_charts(gene, **kwargs):
    dataset_id = kwargs.get('dataset_id',
                            CONFIG['dataset_id'])
    cancer_type_field = kwargs.get('cancer_type_field',
                                   CONFIG['cancer_type_field'])
    mutation_type_field = kwargs.get('mutation_type_field',
                                     CONFIG['mutation_type_field'])
    mutation_types = kwargs.get('mutation_types',
                                CONFIG['mutation_types'])
    sample_field = kwargs.get('sample_field', CONFIG['sample_field'])
    palette = kwargs.get('palette', CONFIG['palette'])

    fields = [
        {
            'name': 'total_mutations',
            'data_type': 'integer',
            'is_list': False,
            'ordering': 1,
            'expression': """
dataset_count(
     record.dataset,
     entities=[["gene", record.gene]],
     filters=[
       [record.cancer_type_field, record.cancer_type],
       [record.mutation_type_field + "__in", record.mutation_types.split(",")]
     ]
)
            """
        },
        {
            'name': 'samples_with_mutations',
            'data_type': 'float',
            'is_list': False,
            'ordering': 2,
            'expression': """
dataset_field_terms_count(
    record.dataset,
    field=record.sample_field,
    entities=[["gene", record.gene]],
    filters=[
      [record.cancer_type_field, record.cancer_type],
      [record.mutation_type_field + "__in", record.mutation_types.split(",")]
    ]
)
            """
        },
        {
            'name': 'total_samples',
            'data_type': 'float',
            'is_list': False,
            'ordering': 3,
            'expression': """
dataset_field_terms_count(
    record.dataset,
    field=record.sample_field,
    filters=[
      [record.cancer_type_field, record.cancer_type]
    ]
)
            """
        },
        {
            'name': 'mutation_frequencies',
            'data_type': 'object',
            'is_list': True,
            'ordering': 4,
            'expression': """
[
  {
    "frequency": (i["count"] / float(record.total_mutations)) *
                  (float(record.samples_with_mutations) /
                   float(record.total_samples)) * 100.0,
    "type": i["term"]
  }
  for i in dataset_field_top_terms(
    record.dataset,
    record.mutation_type_field,
    limit=100,
    entities=[["gene", record.gene]],
    filters=[
      [record.cancer_type_field, record.cancer_type],
      [record.mutation_type_field + "__in", record.mutation_types.split(",")]
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
            'gene': gene,
            'dataset': dataset_id,
            'mutation_types': ','.join(mutation_types),
            'cancer_type_field': cancer_type_field,
            'mutation_type_field': mutation_type_field,
            'sample_field': sample_field
        })

    # Sort by cancer_type and annotate
    records = sorted(records, key=lambda k: k['cancer_type'])
    records.reverse()
    records = list(flask.g.client.Annotator(fields, include_errors=True)
                   .annotate(records))

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


def mutation_frequency_mutant_population_charts(gene, **kwargs):
    dataset_id = kwargs.get('dataset_id',
                            CONFIG['dataset_id'])
    cancer_type_field = kwargs.get('cancer_type_field',
                                   CONFIG['cancer_type_field'])
    mutation_type_field = kwargs.get('mutation_type_field',
                                     CONFIG['mutation_type_field'])
    mutation_types = kwargs.get('mutation_types',
                                CONFIG['mutation_types'])
    palette = kwargs.get('palette', CONFIG['palette'])

    fields = [
        {
            'name': 'total_mutations',
            'data_type': 'integer',
            'is_list': False,
            'ordering': 1,
            'expression': """
                dataset_count(
                  record.dataset,
                  entities=[["gene", record.gene]],
                  filters=[
                    [record.cancer_type_field, record.cancer_type],
                    [record.mutation_type_field + "__in",
                     record.mutation_types.split(",")]
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
                  entities=[["gene", record.gene]],
                  filters=[
                           [record.cancer_type_field, record.cancer_type],
                           [record.mutation_type_field + "__in",
                            record.mutation_types.split(",")]
                  ]
                )
            ]
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
            'gene': gene,
            'dataset': dataset_id,
            'mutation_types': ','.join(mutation_types),
            'cancer_type_field': cancer_type_field,
            'mutation_type_field': mutation_type_field
        })

    # Sort by cancer_type and annotate
    records = sorted(records, key=lambda k: k['cancer_type'])
    records.reverse()
    records = list(flask.g.client.Annotator(fields, include_errors=True)
                   .annotate(records))

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
            marker=dict(
                color=palette[mt]
            )
        ))

    return charts
