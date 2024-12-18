# Substance Abuse

Identify substance abuse using predefined CUIs.



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

* `mml-extract-mml C:\inputdir1 C:\inputdir2 --outdir out --cui-file cuis.txt --extract-format mmi|json|xmi [--extract-directory C:\outputxmi]`
  * This works for cTAKES (`xmi`), MetaMap (`mmi` or `json`), and MetaMapLite (`mmi` or `json`) result files
  * Only include `--extract-directory` if it's different than `C:\inputdir` (e.g., metamaplite writes to the same directory)
    * Add the `--cui-file` to limit the processed CUIs to only those that are of interest (e.g., `substance_abuse/cuis.txt`)
    * Add `--exclude-negated` to only look at positively-asserted 

## Step 4: Creating FE Table
Now the output format must be created.

If you have run `mml_utils`, use the included `parse_to_fe_table.py` to create the table as a CSV file. Several variables/columns/fields will need to be added from other sources:

* ProviderID = '.U.'
* EncounterID = '.U.'
* PatID = '.U.'
* Feature_dt = ''
* FeatureID = 'defined at feature table level'
          
Here is some pseudocode to help build the table:

```python

primary_cui = 'C0740858'
family_history_cui = 'C1397159'
label = 'substance_abuse'

results = []
for encounter in encounters:
    # Primary CUI
    if encounter.has('polarity' == 1 and 'conditional' == 'false' and 'subject' == 'patient' and 'historyOf' == 0):
        results.append({'Feature': primary_cui, 'Feature_Status': 'A'})  # Active 
    elif encounter.has('polarity' == -1 and 'conditional' == 'false' and 'subject' == 'patient' and 'historyOf' == 0):
        results.append({'Feature': primary_cui, 'Feature_Status': 'N'})  # Negated
    elif encounter.has('polarity' == 1 and 'conditional' == 'false' and 'subject' == 'patient' and 'historyOf' == 1):
        results.append({'Feature': primary_cui, 'Feature_Status': 'H'})  # Historical 
    elif encounter.has('polarity' == 1 and 'conditional' == 'false' and 'subject' != 'patient' and 'historyOf' == 0):
        results.append({'Feature': primary_cui, 'Feature_Status': 'X'})  # Other Subject
    else:
        results.append({'Feature': primary_cui, 'Feature_Status': 'U'})  # Else: unknown
        
    # Family History CUI
    if encounter.has('polarity' == 1 and 'conditional' == 'false' and 'subject' == 'family_member' and 'historyOf' == 0):
        results.append({'Feature': family_history_cui, 'Feature_Status': 'A'})  # Active 
    elif encounter.has('polarity' == -1 and 'conditional' == 'false' and 'subject' == 'family_member' and 'historyOf' == 0):
        results.append({'Feature': family_history_cui, 'Feature_Status': 'N'})  # Negated
    elif encounter.has('polarity' == 1 and 'conditional' == 'false' and 'subject' == 'family_member' and 'historyOf' == 1):
        results.append({'Feature': family_history_cui, 'Feature_Status': 'H'})  # Historical 
    else:
        results.append({'Feature': family_history_cui, 'Feature_Status': 'U'})  # Else: unknown

# add missing variables
pipeline_id = int(str(hash(f'UC-{label}-{date.today().year}'))[-8:])
for result in results:
    # map to FE table output
    result['Confidence'] = 'N'  # not assessed
    result['FE_CodeType'] = 'UC'  # UMLS CUI
    # create unique pipeline id based on current year
    result['PipelineID'] = pipeline_id

    # TODO: additional variables must come from other sources which lack a pre-defined shape
    # result['ProviderID'] = '.U.'
    # result['EncounterID'] = '.U.'
    # result['PatID'] = '.U.'
    # result['Feature_dt'] = ''
    # result['FeatureID'] = 'defined at feature table level'

# output
pd.DataFrame.from_records(results).to_csv('fe_feature_table.csv', index=False)

pipeline_df = pd.DataFrame.from_records([{
    'id': pipeline_id,
    'name': f'{label}',
    'run_date': date.today().strftime('%Y-%m-%d'),
    'description': f'Identifying {label} CUIs',
    'source': 'https://github.com/kpwhri/fe5_nlp/substance_abuse',
}])
pipeline_df.to_csv('fe_pipeline_table.csv', index=False)
```
