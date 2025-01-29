# Anaphylaxis

## Steps

* Follow the steps described in [Sentinel Scalable NLP repo](https://github.com/kpwhri/Sentinel-Scalable-NLP?tab=readme-ov-file#prediction-modeling-quick-start):
  * Create the Anaphylaxis Cohort using [SAS code](https://github.com/kpwhri/Sentinel-Scalable-NLP/High-Sensitivity-Filter/Programs)
  * Process the corpus output by `04_Clinical_Text_for_NLP.sas` with `mml_utils` using [configuration files](https://github.com/kpwhri/Sentinel-Scalable-NLP/Prediction-Modeling/Anaphylaxis/NLP/configs)
    * A step-by-step guide is provided in the [`mml_utils` documentation](https://github.com/kpwhri/mml_utils/tree/master/examples/phenorm)
  * Run PheNorm using the [R code](https://github.com/kpwhri/Sentinel-Scalable-NLP/Prediction-Modeling/)
    * If you are only applying the model, consider using the [Phenorm Predict repository](https://github.com/kpwhri/phenorm_predict) which contains only the necessary scripts to run an existing model. (You will still need to build the model from the Sentinel Scalable NLP repo)

### `phenorm_predict`

The [`phenorm_predict` repo](https://github.com/kpwhri/phenorm_predict) will provide 3 runnable R scripts to apply the model to your cohort:
* `install_packages.R`: get the prerequisite packages installed
* `process_data.R`: reshape the dataset
* `get_predicted_probabilities.R`: get a CSV with predicted probabilities

### Model Interpretation

To get the appropriate interpretation, you will need a particular model along with a selected cutoff (if unsure, default to 0.5 as cutoff).

The predicted probabilities dataset should have following variables:
* `Obs_ID`: observation/event id (e.g., studyid + index)
* `pred_prob_SILVER_ANA_DX_N_ENCS`
* `pred_prob_SILVER_ANA_MENTIONS_N`
* `pred_prob_SILVER_ANA_CUI_NOTES_N`
* `pred_prob_SILVER_ANA_EPI_MENTIONS_N`
* `pred_prob_Aggregate`

If you do not otherwise have a model/cutoff, use:
* `pred_prob_Aggregate` model
* with cutoff of 
  * `>= 0.5`: `Feature_Status = A`
  * `< 0.5`: `Feature_Status = U`

```python 

import pandas as pd
from datetime import date

cui = 'C0002792'  # https://uts.nlm.nih.gov/uts/umls/concept/C0002792
df = pd.read_csv('predicted_probabilities.csv')  # output of `get_predicted_probabilities.R` (step 3)

# peek at a histogram
df['pred_prob_Aggregate'].hist(bins=50).figure.savefig('model_hist.png')

# apply the model for a simple yes/no 
cutoff = 0.5
df['Feature_Status'] = df['pred_prob_Aggregate'].apply(lambda x: 'A' if x >= cutoff else 'U')

# keep only anaphylaxis cases, reduce to only 2 columns/variables
df = df[df['result'] == 1][['Obs_ID']]

# map to FE table output
df['Confidence'] = 'N'
df['FE_CodeType'] = 'UC'  # UMLS CUI
df['Feature'] = cui
pipeline_id = int(str(hash(f'UC-{cui}-{date.today().year}'))[-8:])  # create unique pipeline id based on current year
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
    'name': 'phenorm-anaphylaxis',
    'run_date': date.today().strftime('%Y-%m-%d'),
    'description': f'Phenorm Anaphylaxis pipeline with cutoff of >= {cutoff}',
    'source': 'https://github.com/kpwhri/Sentinel-Scalable-NLP',
}])
pipeline_df.to_csv('fe_pipeline_table.csv', index=False)
```
