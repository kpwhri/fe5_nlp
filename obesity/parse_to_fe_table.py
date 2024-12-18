"""
Generate FE Table for Obesity

Parse the nlp.csv file output by `mml-extract-mml` from cTAKES or MetaMapLite.

Usage:
    python parse_to_fe_table.py [EXTRACT_NLP_CSV_OUTFILE]

Example:
    python parse_to_fe_table.py out/nlp_{date}.csv

Output:
    fe_feature_table.csv -> outline of feature table
    fe_pipeline_table.csv -> locally-maintained information about this pipeline run
"""
import sys
from pathlib import Path

import pandas as pd
from datetime import date  # for generating pipeline id

# see https://uts.nlm.nih.gov/uts/umls/concept/C0028754
PRIMARY_CUI = 'C0028754'  # Obesity

# see https://uts.nlm.nih.gov/uts/umls/concept/C0455373
FAM_HX_CUI = 'C0455373'  # FH: Obesity


def get_ctakes_features(df: pd.DataFrame):
    """Convert cTAKES results to Feature_Status"""

    def evaluate_personal(grp):
        negated = grp['polarity'] < 0
        # cTAKES default is 'historyOf'
        historical = grp['historical'] == 1
        # cTAKES default for 'conditional' is the string 'true' or 'false' which may not evaluate to True/False
        conditional = grp['conditional']
        is_patient = grp['subject'] == 'patient'
        if grp[~negated & ~historical & is_patient & ~conditional].any(axis=1).any():
            return 'A'
        elif grp[negated & ~historical & is_patient & ~conditional].any(axis=1).any():
            return 'N'
        elif grp[~negated & historical & is_patient & ~conditional].any(axis=1).any():
            return 'H'
        elif grp[~negated & ~historical & ~is_patient & ~conditional].any(axis=1).any():
            return 'X'
        else:
            return 'U'

    def evaluate_family(grp):
        negated = grp['polarity'] < 0
        # cTAKES default label is 'historyOf'
        historical = grp['historical'] == 1
        # cTAKES default for 'conditional' is the string 'true' or 'false' which may not evaluate to True/False
        conditional = grp['conditional']
        is_family = grp['subject'] == 'family_member'
        if grp[~negated & ~historical & is_family & ~conditional].any(axis=1).any():
            return 'A'
        elif grp[negated & ~historical & is_family & ~conditional].any(axis=1).any():
            return 'N'
        elif grp[~negated & historical & is_family & ~conditional].any(axis=1).any():
            return 'H'
        else:
            return 'U'

    df = df[['docid', 'polarity', 'historical', 'conditional', 'subject']]
    # patient
    pt_df = df.set_index('docid').groupby(level='docid').apply(evaluate_personal).reset_index(name='Feature_Status')
    # family history
    fhx_df = df.set_index('docid').groupby(level='docid').apply(evaluate_family).reset_index(name='Feature_Status')
    return pt_df, fhx_df


def get_mml_features(df: pd.DataFrame):
    """Convert MetaMapLite results to Feature_Status"""
    def evaluate_personal(grp):
        if grp[(grp['negated'] == 1) | (grp[grp['negated']] == '1')].any(axis=1).any():
            return 'A'
        else:
            return 'U'

    df = df[['docid', 'negated']]
    pt_df = df.set_index('docid').groupby(level='docid').apply(evaluate_personal).reset_index(name='Feature_Status')
    return pt_df


def add_variables(df: pd.DataFrame, cui: str, codetype: str = 'UC'):
    # map to FE table output
    df['Confidence'] = 'N'  # not assessed
    df['FE_CodeType'] = codetype  # 'UC' for UMLS CUI
    df['Feature'] = cui
    # create unique pipeline id based on current year
    pipeline_id = int(str(hash(f'{codetype}-{cui}-{date.today().year}'))[-8:])
    df['PipelineID'] = pipeline_id

    # TODO: additional variables must come from other sources which lack a pre-defined shape
    # df['ProviderID'] = '.U.'
    # df['EncounterID'] = '.U.'
    # df['PatID'] = '.U.'
    # df['Feature_dt'] = ''
    # df['FeatureID'] = 'defined at feature table level'
    return df, pipeline_id


def main(infile: Path):
    """

    :param infile:
    :return:
    """
    df = pd.read_csv(infile)
    if 'polarity' in df.columns:
        pt_df, fhx_df = get_ctakes_features(df)
        label = 'ctakes'
    else:  # assume is metamaplite which only has negated
        pt_df = get_mml_features(df)
        fhx_df = pd.DataFrame(columns=['docid', 'Feature_Status'])  # empty dataset
        label = 'metamaplite'

    pt_df, pt_pipeline_id = add_variables(pt_df, PRIMARY_CUI)
    fhx_df, fhx_pipeline_id = add_variables(fhx_df, FAM_HX_CUI)

    # merge datasdets and output
    result_df = pd.concat((pt_df, fhx_df))
    result_df.to_csv('fe_feature_table.csv', index=False)

    # create information for locally-maintained pipeline
    pipeline_df = pd.DataFrame.from_records([
        {
            'id': pt_pipeline_id,
            'name': f'{label}-substance_abuse',
            'run_date': date.today().strftime('%Y-%m-%d'),
            'description': f'Identifying substance abuse CUIs with {label}',
            'source': 'https://github.com/kpwhri/fe5_nlp/substance_abuse',
        },
        {
            'id': fhx_pipeline_id,
            'name': f'{label}-substance_abuse',
            'run_date': date.today().strftime('%Y-%m-%d'),
            'description': f'Identifying substance abuse CUIs with {label}',
            'source': 'https://github.com/kpwhri/fe5_nlp/substance_abuse',
        },
    ])
    pipeline_df.to_csv('fe_pipeline_table.csv', index=False)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(Path(sys.argv[1]))
    else:
        print('Usage: python parse_to_fe_table.py [EXTRACT_NLP_CSV_OUTFILE]')
