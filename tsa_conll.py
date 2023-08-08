import json
import os
import argparse
import itertools
from collections import Counter, defaultdict

# Read the json files from norec-fine and create conll-formated text files with the sentiment targets data

def i_set(span_str): 
    """Input: target span string like '28:39',
    Out: set for the indices """
    idx_strings = span_str.split(":")
    targ_min, targ_max = int(idx_strings[0]), int(idx_strings[1])
    return set(range(targ_min, targ_max))


def token_data (text):
    """
    Split by space and add start and end indexes.
    Input: a space-tokenized sentence
    Out: List of dicts, one for each token
    start and end is the character positions within the sentence
    idx is the token index in the sentence
    """
    tokens = [{"token": t} for t in text.split(" ")]
    i = 0 
    for idx, token in enumerate(tokens):
        token["start"] = i
        token["end"] = token["start"] + len(token["token"])
        token["idx"] = idx
        i = token["end"]+1
    return tokens




def get_bio_target(sentence):
    """Input: The sentence dict developed from the json.
    sentence["tsa_spans"] is a dict with the span character indices as text are the key, 
        and the value is an int for polarity
    Out: list of tokens, list of tags"""
    try:
        tsa_spans = sentence["tsa_spans"]
    # will throw exception if the opinion target is None type
    except TypeError:
        return []
    except ValueError:
        return []
    # get the beginning and ending indices
    if len(sentence["text"]) < 1:
        return []
        
    tokens = token_data(sentence["text"])
    tags = ["O"] * len(tokens)
    token_indexed_targets = [] # List of tuples with polarity and indexes

    for tsa_span, polarity in tsa_spans.items():
        tsa_char_set = i_set(tsa_span)
        this_span = [] # token index of tokens in this span
        for token in tokens:
            token_char_set = set(range(token["start"], token["end"]))
            if token_char_set <= tsa_char_set:
                this_span.append(token["idx"])
        token_indexed_targets.append((polarity, this_span))
    
    for polarity, t_indexlist in token_indexed_targets:
        t_indexlist.sort() # List of token indices with given polarity
        for list_index, t_idx in enumerate(t_indexlist):
            if list_index == 0: # First
                tags[t_idx] = "B-targ-"+polarity
            else: 
                tags[t_idx] = "I-targ-"+polarity
    return ( [t["token"] for t in tokens], tags)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--jfolder", "-jf",
        type=str,
        default="norec_fine",
        help="Folder with train, dev and test norec fine json files. Default is 'norec_fine'"
    )
    parser.add_argument(
        "--cfolder", "-cf",
        type=str,
        default="tsa_conll",
        help="Folder for saving converted conll files. Default is 'tsa_conll'"
    )
    parser.add_argument(
        "--intensities", "-i",
        dest="intensities",
        default=False,
        action="store_true",
        help="Add this flag to add intensity to the polarity label"
    )
    args= parser.parse_args()

    json_folder = args.jfolder
    conll_folder = args.cfolder
    return_intensity = args.intensities == True 
    if not os.path.exists(conll_folder):
        os.mkdir(conll_folder)
    splits = ["train", "dev", "test"]

    for split in splits:
        with open(os.path.join(json_folder, split+".json"), encoding = "utf-8") as rf:
            dataset_json = json.load(rf)

        for idx, sent in enumerate(dataset_json.copy()):
            sent_targets = [] # list of dicts, one for each sentiment target in the opinions list.
            for opn in sent["opinions"]:
                for target_elem in opn["Target"][1]: #  example: ['0:8', '28:39', '69:72']
                    idx_strings = target_elem.split(":")
                    targ_min, targ_max = int(idx_strings[0]), int(idx_strings[1])
                    if targ_max > 0: #Both 0 if empty target
                        targ_text = sent["text"][targ_min:targ_max]
                        polarity = opn["Polarity"]
                        intensity = opn["Intensity"]
                        sent_targets.append({"polarity": polarity, "intensity": intensity, "word": targ_text, "start": targ_min, 
                            "end": targ_max, "span": target_elem})
            dataset_json[idx]["targets"]=sent_targets

        # Now each target span is separate not regarding overlap
        #Resolve the textual labels
        intensities = {'Slight':1, 'Standard':2, 'Strong':3}
        polarities = {'Negative':-1, 'Positive':1}

        for idx, sent in enumerate(dataset_json.copy()):
            targets = sent["targets"]
            #remove duplicates
            unique_spans = set([target["span"] for target in targets])
        
            # Check for target subsets and partial overlaps. They are not there in norec-fine.
            # (But there are multiple cases where more than one opinion has the same target.)
            for first, second in itertools.product(unique_spans, unique_spans):
                f, s = i_set(first) , i_set(second)
                if f < s: # True subset
                    print("Subset target!",sent) # None
                if f != s and len(f.intersection(s) )> 0:
                    print("Targets are overlapping!",sent) # None

            resolved = {} # key: str for span, value: int for polarity

            for span_str in unique_spans:
                span_targets =[ t for t in targets if t["span"] == span_str] # List of the targets with that same span
                span_polarity = sum([polarities.get(t["polarity"], 0) *intensities.get(t["intensity"], 0) 
                                        for t in span_targets])
               
                sent_int = min(3, max(span_polarity, -3)) # clip to -3...3 range for each resolved target 
                if sent_int > 0: sent_str = "Positive"
                elif sent_int < 0: sent_str = "Negative"
                else: sent_str = span_targets[-1]["polarity"] # Use last polarity if equally pos and neg
                # Here is where you would change the code if you want to resolve mixed opinions differently. Or if you want to keep intensity in the conll label
                if return_intensity:
                    sent_str = sent_str+ "-"+str(abs(sent_int))
                resolved[span_str] = sent_str
            dataset_json[idx]["tsa_spans"] = resolved


            # Now each target has one polarity, resolved from all polarities towards it.
            # if "Rollo " in sent["text"]: print(sent) 
    
        conll_sents = []
        for sent in dataset_json:
            tokens, tags = get_bio_target(sent)
            # sent['sent_id']+"\n" +  adds sentence id at top of each sentence in the list
            assert "\t" not in sent['sent_id']
            conll_sents.append("#sent_id="+sent['sent_id']+"\n" + "\n".join([to+"\t"+ta for to, ta in zip(tokens, tags)]))
        with open(os.path.join(conll_folder, split+".conll"), "w", encoding="UTF-8") as wf:
            wf.write("\n\n".join(conll_sents))



