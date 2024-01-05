# Targeted Sentiment Analysis on The Norwegian Review Corpus, NoReC<sub>*tsa*</sub>. 
NoReC<sub>*fine*</sub> is a Norwegain dataset annotated for sentiment expression with targets and holder. See the [github repository](https://github.com/ltgoslo/norec_fine) and [paper](https://www.aclweb.org/anthology/2020.lrec-1.618) for details.  
NoReC<sub>*fine*</sub> consists of professional reviews, a subset of the [Norwegian Review Corpus NoReC](https://github.com/ltgoslo/norec). 
## Convert NoReC<sub>*fine*</sub> sentiment targets to CoNLL

Our conversion scipt presented here, converts the NoReC<sub>*fine*</sub> sentiment targets to CoNLL, for training models for Targeted Sentiment Analysis (TSA).  

When doing Targeted Sentiment Analysis, we are interested in what is spoken positively or negatively about in each sentence, and what is the polarity of the sentiment. A sentiment target may have more than one opinion towards it. We count 1732 sentiment targets with more than one opinion towards it, and 402 of these have both positive and negative opinions. An example from the dataset: 

```
{"sent_id": "004702-02-01", "text": "Forviklingskomedie med brodd og bismak .", 
    "opinions": [
        {"Source": [[], []], "Target": [["Forviklingskomedie"], ["0:18"]], 
                "Polar_expression": [["brodd"], ["23:28"]], "Polarity": "Positive", "Intensity": "Strong", "NOT": false, "Source_is_author": true, "Target_is_general": false, "Type": "E"}, 
        {"Source": [[], []], "Target": [["Forviklingskomedie"], ["0:18"]], "Polar_expression": [["bismak"], ["32:38"]], "Polarity": "Negative", "Intensity": "Standard", "NOT": false, "Source_is_author": true, "Target_is_general": false, "Type": "E"}]},
```
The annotations give that *Forviklingskomedie* is a sentiment target with two opinions towards it: "brodd", which is positive with strong intensity, and "bismak" which is negative with standard intensity. Our script resolves these situations to the polarity with the strongest total intensity weight. (In case of a tie, the last opinion polarity wins.) Our example target *"Forviklingskomedie"* is resolved to a positive sentiment target since the  positive expression has the strongest intensity. The TSA CoNLL output for this sentence is therefore as follows:
```
#sent_id=004702-02-01
Forviklingskomedie	B-targ-Positive
med	O
brodd	O
og	O
bismak	O
.	O
```
### The sentence id
The sentence id line starts with a '#' and has no tab in it. The first 6 digits are the document identification. The same document id is used in the [NoReC metadata](https://github.com/ltgoslo/norec/tree/master/data). Here, one may retrieve information about the document genre, author, year and rating of the reviewed entity.


## To run the conversion script:
1. Clone the repo norec_fine
`git clone https://github.com/ltgoslo/norec_fine.git`
2. Run `python tsa_conll.py` with optional arguments for the path to the NoReC<sub>*fine*</sub> folder containing the json files, and for the path for the resulting CoNLL tab-separated files.  
```
usage: tsa_conll.py [-h] [--jfolder JFOLDER] [--cfolder CFOLDER] [--intensities]

optional arguments:
  -h, --help            show this help message and exit
  --jfolder JFOLDER, -jf JFOLDER
                        Folder with train, dev and test norec fine json files. Default is 'norec_fine'
  --cfolder CFOLDER, -cf CFOLDER
                        Folder for saving converted conll files. Default is 'tsa_conll'
  --intensities, -i     Add this flag to add intensity to the polarity label
```

The result of the conversion as per posting this repository, is found in the `tsa_conll`subfolder.

## Conversion from conll to HF Datasets
`conll_to_dataset.ipynb` has a script for converting the conll-formatted TSA datasets into the HF Datasets Arrow-format. The contents of the resulting folders, can be loaded through `datasets.load_from_disk`.
```
from datasets import load_from_disk, DatasetDict, Dataset
load_from_disk(<arrow_folder>)
```
### Sentiment intensity integers
The intensities annotated in NoReC<sub>*fine*</sub> are converted as follows: `{'Slight':1, 'Standard':2, 'Strong':3}`. When multiple sentiment expressions have the same target, the values are added / subtracted. When a target receives equaly strong pos and neg sentiments, the last polarity in the sentence is  assigned. This corresponds with an intuitive understanding of communicating sentiment in Norwegian, that the last sentiment expressed tends to be conclusive. The intensity is in these cases set to 1. Our conversion script does not output any "mixed" polarity classification, but this can be modified in the script.

## Cite this work
If you use the NoReC<sub>*tsa*</sub> dataset in your work, please cite as informed on the [NoReC<sub>*fine*</sub>](https://github.com/ltgoslo/norec_fine#cite) github page.
## Licencing
The licence for this derived version of NoReC<sub>*fine*</sub>, is found on the [NoReC<sub>*fine*</sub>](https://github.com/ltgoslo/norec_fine#cite) github page.
