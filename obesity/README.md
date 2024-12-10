# Obesity

Identify obesity using predefined CUIs. Prefer Z-codes to allow for greater specificity if the data allows.

## Steps

* Use a UMLS-based NLP concept extraction tool (e.g., cTAKES, MetaMap, MetaMapLite)
* Limit based on concepts in [cuis.txt](cuis.txt)
* Summarize into `fe_features_table`

## Implementation

### Prerequisites

1. You will need to install one of the UMLS-based NLP concept extraction tools.
    * [Install cTAKES](https://kpwhri.github.io/mml_utils/install_ctakes.html)
    * [Install MetaMapLite](https://kpwhri.github.io/mml_utils/install_metamaplite.html)
    * [Install MetaMap](https://kpwhri.github.io/mml_utils/install_mm.html)
2. We recommend the [`mml_utils` package](https://github.com/kpwhri/mml_utils/) which works well with cTAKES, MetaMap,
   and MetaMapLite. This contains command line tools to complete all of the following steps.
    * Installation requires:
        * Python
        * Install `mml_utils`
            * Download/clone repository: `git clone https://github.com/kpwhri/mml_utils`
            * Install: `cd mml_utils` and `pip install .`
    * Handy `mml_utils` guides/tutorials:
        * [Generic Example](https://github.com/kpwhri/mml_utils/blob/master/examples/complete)
        * [Phenorm Example](https://github.com/kpwhri/mml_utils/tree/master/examples/phenorm)

### Step 1: Prepare notes

Prepare notes into a format amenable to the select UMLS-based NLP extraction tool. Generally, this will be a directory (
or several directories) containing files for each note. The note is usually named as `{note_id}.txt` and contains only
the relevant text.

To do this with `mml_utils` (accepts sas7bdat/csv inputs):

* `mml-sas-to-txt corpus.sas7bdat --id-col note_id --text-col note_text [--n-dir 4] [--outdir OUTDIR]`
* See [more](https://github.com/kpwhri/mml_utils/tree/master/examples/phenorm#dataset-to-text)
* NB: Creating multiple filelists allows running a program like MetaMapLite in parallel.

### Step 2: Run UMLS-based NLP Concept Extraction Tool

Run `MetaMap`, `MetaMapLite`, `cTAKES` on the prepared notes.

To do this with `mml_utils`:

* [MetaMapLite](https://github.com/kpwhri/mml_utils/tree/master/examples/phenorm#metamaplite):
  `mml-run-filelist --filelist filelist.txt --mml-home C:/public_mm_lite --output-format json`
    * Run multiple instances using different filelists
* [MetaMap](https://github.com/kpwhri/mml_utils/tree/master/examples/phenorm#running-metamap)
* [cTAKES](https://kpwhri.github.io/mml_utils/build_umls_for_ctakes.html#run-ctakes-with-new-dictionary):

```commandline
mml-run-ctakes 
C:\inputfiles 
--ctakes-home C:\ctakes\apache-ctakes-4.x.y.z 
--outdir C:\outputxmi 
--umls-key xxx-yyy 
--dictionary C:\ctakes\apache-ctakes-4.x.y.z\resources\org\apache\ctakes\dictionary\lookup\fast\custom_dict.xml
```

### Step 3: Aggregating Output

Output from these systems is written to files which need to be parsed, selected, and summarized. Then, only the relevant
CUIs should be retained.

To do this will `mml_utils`, only the output file type is of importance (see
details [here](https://github.com/kpwhri/mml_utils/tree/master/examples/phenorm#extracting-cuis)):

*
`mml-extract-mml C:\inputdir1 C:\inputdir2 --outdir out --cui-file cuis.txt --output-format mmi|json|xmi [--output-directory C:\outputxmi]`
  * Only include `--output-directory` if it's different than `C:\inputdir` (e.g., metamaplite writes to the same directory)
    * Add the `--cui-file` to limit the processed CUIs to only those that are of interest (e.g., `obesity/cuis.txt`)
    * Add `--exclude-negated` to only look at positively-asserted 

## Step 4: Creating FE Table

Now the output format must be created.

```python
import pandas as pd
from datetime import date  # for generating pipeline id

df = pd.read_csv('out/cuis_by_doc.csv')

# sum all the CUI variables to see which notes have output (they all start with 'C')
cui_columns = [col for col in df.columns if col.startswith('C')]
df['any_cui'] = df[cui_columns].sum()

# limit to only those with at least one cui
df = df[df['any_cui'] > 0][['docid', 'any_cui']]

# map to FE table output
df['Confidence'] = 'N'  # not assessed
df['FE_CodeType'] = '10'  # UMLS CUI
df['Feature'] = 'Z683'  # https://www.icd10data.com/ICD10CM/Codes/Z00-Z99/Z68-Z68/Z68-
  # create unique pipeline id based on current year
pipeline_id = int(str(hash(f'10-Z683-{date.today().year}'))[-8:])
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
  'name': 'metamaplite-obesity',
  'run_date': date.today().strftime('%Y-%m-%d'),
  'description': f'Identifying obesity CUIs with MetaMapLite',
  'source': 'https://github.com/kpwhri/fe5_nlp/obesity',
}])
pipeline_df.to_csv('fe_pipeline_table.csv', index=False)
```
