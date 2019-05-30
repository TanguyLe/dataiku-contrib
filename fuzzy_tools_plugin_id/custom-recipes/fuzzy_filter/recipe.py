import dataiku
from dataiku.customrecipe import *

from functools import partial
from fuzzywuzzy import fuzz
import string
from unidecode import unidecode

""" This recipes does the following :
1) Loads the datasets & the parameters
2) Prepares the functions to be used on the data
3) Apply get_choices_serie_vals over the whole dataframe line by line
4) Returns the result by merging the resulting dataframe to the original one
"""

# Fetching dataiku datasets
input_dataset_name = get_input_names_for_role('input_dataset')[0]
input_dataset = dataiku.Dataset(input_dataset_name)

output_dataset_name = get_output_names_for_role('output_dataset')[0]
output_dataset = dataiku.Dataset(output_dataset_name)

# Read recipe inputs
data_df = input_dataset.get_dataframe()

# Read ui parameters
parameters = get_recipe_config()
target_col_name = parameters["target_col"]
value = parameters["value"]
thresh = parameters["thresh"]
ratio_type = parameters["ratio_type"]
action = parameters["action"]

# fetching the scorer to use from the fuzzywuzzy module
ratio_fct = getattr(fuzz, ratio_type)

# Python 2 fun
printable = set(string.printable)


def clear_text(text):
    """ Tries to remove accents but keep the underlying letter using unidecode. 
        If it fails, just removes the non-ascii chars """
    try:
        return unidecode(text)
    except UnicodeDecodeError:
        return filter(lambda x: x in printable, text)


# Actuel use of fuzzywuzzy
def get_fuzz_ratio(text, val):
    return ratio_fct(val, clear_text(text))


get_fuzz_ratio_val = partial(get_fuzz_ratio, val=value)

# Compute the condition
data = data_df[target_col_name].astype(str).fillna('')
ratios = data.apply(get_fuzz_ratio_val)
above_thresh = ratios >= thresh

# Use the condition to keep or remove rows
if action == "keep":
    result_df = data_df.loc[above_thresh, :]
else:
    result_df = data_df.loc[~above_thresh, :]

# Write recipe outputs
output_dataset.write_with_schema(result_df)
