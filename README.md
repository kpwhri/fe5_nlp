# FE5 NLP

Scripts and instructions for deploying the feature engineering solutions for the FE5 project.

## Overview

The five features (and tools/methods):

* [Obesity](#obesitybmi): UMLS-based NLP concept extraction
* [Substance Abuse](#substance-abuse): UMLS-based NLP concept extraction
* [Anaphylaxis](#anaphylaxis): Phenorm
* [History of Suicide Attempt (`suicide_attempt`)](#history-of-suicide-attempt): `konsepy`
* [Smoking Status (`smoking`)](#smoking-status): `konsepy`

## Algorithm Descriptions

The following provides a brief, high-level description of each algorithm. More details can be found via links or
accessing a README file in the relevant folders.

Some notes:

* Any encounter/note that *is* evaluated for a particular feature without results for that feature should be assigned a
  feature status of `'U'` (i.e., Unknown). This is to help with the assigning of a denominator.
* The same CUI can be output by an algorithm to provide other details (e.g., family history).

### Obesity/BMI

Identify obesity using predefined CUIs (or BMI). [details](obesity/README.md)

Steps:

* Use a UMLS-based NLP concept extraction tool (e.g., cTAKES, MetaMap, MetaMapLite)
* Limit based on concepts in [obesity/cuis.txt](obesity/cuis.txt)

#### Output

For those with existing structured data, results are defined as Z-codes to allow greater specificity. For NLP results,
the UMLS CUI `C0028754` is used.

* NLP:

| Variable       | Obesity           | FH: Obesity   |
|----------------|-------------------|---------------|
| Feature        | C0028754          | C0455373      |
| FE_CodeType    | UC                | UC            |
| Feature_Status | A / N / H / X / U | A / N / H / U |
| Confidence     | N                 | N             |

* Structured: [see file](obesity/zcodes.csv)

### Substance Abuse

Identify substance abuse using predefined CUIs. See [details](substance_abuse/README.md).

Steps:

* Use a UMLS-based NLP concept extraction tool (e.g., cTAKES, MetaMap, MetaMapLite)
* Limit based on concepts in [substance_abuse/cuis.txt](substance_abuse/cuis.txt)

#### Output

| Variable       | Substance Abuse   | FH: Substance Abuse |
|----------------|-------------------|---------------------|
| Feature        | C0740858          | C1397159            |
| FE_CodeType    | UC                | UC                  |
| Feature_Status | A / N / H / X / U | A / N / H / U       |
| Confidence     | N                 | N                   |

### Anaphylaxis

Using Phenorm to identify anaphylaxis cases. If a model has not been trained at your particular site, use the aggregate model with a cutoff of >= 0.5. For more details, including Phenorm post-processing to the FE table,
see [README](anaphylaxis/README.md).

The original work for this algorithm is at
the [Sentinel Scalable NLP repo](https://github.com/kpwhri/Sentinel-Scalable-NLP?tab=readme-ov-file#prediction-modeling-quick-start).

#### Output

| Variable       | Anaphylaxis |
|----------------|-------------|
| Feature        | C0002792    |
| FE_CodeType    | UC          |
| Feature_Status | A / U       |
| Confidence     | N           |

### History of Suicide Attempt

The history of suicide attempt/self-harm concept is intended to be summarized at the patient-date level (but
see [konsepy limitation](#konsepy-and-patient-date-level)). This is not strictly true, as the family history of
suicide/self-harm concept could co-occur with a personal history of suicide/self-harm.

Steps:

* Prepare the [prerequisites for `konsepy`](https://github.com/kpwhri/fe5_konsepy?tab=readme-ov-file#prerequisites)
* Run the `suicide_attempt` pipeline:
    *
  `python src/run_concept.py --input-files sample/corpus.csv --outdir out --id-label studyid --concept suicide_attempt`
* Run the post-processing pipeline:
    * `python src/postprocess_hx_attempted_suicide.py --infile out/notes_category_counts.csv`

#### Output

| Variable       | Hx Suicide Attempt |
|----------------|--------------------|
| Feature        | C0455507           |
| FE_CodeType    | UC                 |
| Feature_Status | A / N / X / U      |
| Confidence     | N                  |

### Smoking Status

The smoking status concept is intended to be summarized at the patient-date level (but
see [konsepy limitation](#konsepy-and-patient-date-level)).

Steps:

* Prepare the [prerequisites for `konsepy`](https://github.com/kpwhri/fe5_konsepy?tab=readme-ov-file#prerequisites)
* Run the `smoking` pipeline:
    * `python src/run_concept.py --input-files sample/corpus.csv --outdir out --id-label studyid --concept smoking`
* Run the post-processing pipeline:
    * `python src/postprocess_smoking.py --infile out/notes_category_counts.csv`

#### Output

| Variable       | Smoker        | Never    |
|----------------|---------------|----------|
| Feature        | C0337664      | C0337672 |
| FE_CodeType    | UC            | UC       |
| Feature_Status | A / N / H / U | A / U    |
| Confidence     | N             | N        |

## Footnotes

### `konsepy` and Patient-date Level

Since `konsepy` does not have a note date variable with which to summarize the information, summarization in the
postprocessor occurs at whatever level csv is supplied to `postprocess_*.py`. E.g., supplying
`notes_category_counts.csv` will result in note-level summarization, whereas `mrn_category_counts.csv` will result in
mrn/patient-level summariation.

To get patient-date level summarization, the output file `notes_category_counts.csv` must be grouped at the note date
level. This can be accomplished by the following Python code (intended as pseudo-code):

```python
"""Make `notes_category_counts` into patient-date level summarization."""
import pandas as pd  # pip install pandas

konsepy_output = pd.read_csv('notes_category_counts.csv')  # columns: [mrn, note_id, ...]
metadata = pd.read_csv('metadata.csv')  # columns: [note_id, note_date]

df = pd.merge(konsepy_output, metadata, on='note_id')  # columns: [mrn, note_id, note_date, ...]
del df['note_id']  # remove note_id column: we don't need it

# now, we need to group by (mrn, note_id) and summ all of the concept
result = df.groupby(['mrn', 'note_date']).sum().reset_index()

result.to_csv('notedate_category_counts.csv', index=False)
# now, run `python src/postprocess_*.py --infile out/notedate_category_counts.csv`
```
