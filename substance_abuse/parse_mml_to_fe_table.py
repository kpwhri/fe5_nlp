"""
Parse the mml.csv file output by `mml-extract-mml`.

Usage:
    python parse_mml_to_fe_table.py [EXTRACT_MML_CSV_OUTFILE]

Example:
    python parse_mml_to_fe_table.py out/mml_{date}.csv
"""
import sys
from pathlib import Path

import pandas as pd
from datetime import date  # for generating pipeline id


def is_negated(val):
    """Parse the negated column value"""
    return val == '1' or val == 1


def main(infile: Path, include_negated=False):
    """

    :param infile:
    :param include_negated: include negated as a separate feature
    :return:
    """
    df = pd.read_csv(infile)
    df = df[['docid', 'cui', 'negated']]
    df['cui'] = df.apply(lambda x: -1 if x['negated'] == '1' or x['negated'] == 1 else 1, axis=1)
    df = df.groupby('docid')['cui'].sum().reset_index()

    # map to FE table output
    df['Confidence'] = 'N'  # not assessed
    df['FE_CodeType'] = 'UC'  # UMLS CUI
    df.loc[:, 'Feature_Status'] = 'A'  # affirmed
    df.loc[df['cui'] < 0, 'Feature_Status'] = 'N'  # negated
    df['Feature'] = 'C0740858'  # https://uts.nlm.nih.gov/uts/umls/concept/C0740858
    # create unique pipeline id based on current year
    pipeline_id = int(str(hash(f'UC-C0740858-{date.today().year}'))[-8:])
    df['PipelineID'] = pipeline_id

    # TODO: additional variables must come from other sources which lack a pre-defined shape
    # df['ProviderID'] = '.U.'
    # df['EncounterID'] = '.U.'
    # df['PatID'] = '.U.'
    # df['Feature_dt'] = ''
    # df['FeatureID'] = 'defined at feature table level'

    # output
    df.to_csv('fe_feature_table.csv', index=False)

    pipeline_df = pd.DataFrame.from_records([{
        'id': pipeline_id,
        'name': 'metamaplite-substance_abuse',
        'run_date': date.today().strftime('%Y-%m-%d'),
        'description': f'Identifying substance abuse CUIs with MetaMapLite',
        'source': 'https://github.com/kpwhri/fe5_nlp/substance_abuse',
    }])
    pipeline_df.to_csv('fe_pipeline_table.csv', index=False)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(Path(sys.argv[1]))
    else:
        print('Usage: python parse_mml_to_fe_table.py [EXTRACT_MML_CSV_OUTFILE]')

