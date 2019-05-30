import dataiku
from dataiku.customrecipe import *

from functools import partial
from fuzzywuzzy import fuzz, process
import pandas as pd
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

values_dataset_name = get_input_names_for_role('values_dataset')[0]
values_dataset = dataiku.Dataset(values_dataset_name)

output_dataset_name = get_output_names_for_role('output_dataset')[0]
output_dataset = dataiku.Dataset(output_dataset_name)

# Read recipe inputs
data_df = input_dataset.get_dataframe()
values_df = values_dataset.get_dataframe()

# Reading ui parameters
parameters = get_recipe_config()

# Mandatory params
target_col_name = parameters["target_col"]
nb_choices = int(parameters["nb_choices"])
thresh = parameters["thresh"]
ratio_type = parameters["ratio_type"]
ratios = parameters["ratios"]

# Optional params : either values from a list or from a column
values = parameters.get("values", [])
values_colname = parameters.get("values_colname", '')

if values:
    values = values.split(',')

if values_colname:
    values_series = values_df[values_colname]
    if not values_series.empty:
        values += values_series.tolist()

if nb_choices > len(values):
    raise ValueError("Bigger number of choices than count of provided values.")

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
        # This happens in case of cyrilic chars, smileys...
        return filter(lambda x: x in printable, text)


# Actuel use of fuzzywuzzy
def get_choices(text, choices, number_of_choices=1):
    """ Returns a list of tuples with (choice, score) """
    return process.extract(clear_text(text), choices, limit=number_of_choices, scorer=ratio_fct)


choice_key = "choice_%d"
choice_ratio_key = choice_key + "_ratio"


def get_choices_serie(text, choices, base_res_dict, number_of_choices=1, return_ratios=False):
    """ Returns a series with an entry for each choice (an another for ratios if expected)"""

    res_dict = base_res_dict.copy()

    # As long as we get viable choices (above the thresh) we keep filling the dict
    for i, res in enumerate(get_choices(text=text, choices=choices, number_of_choices=number_of_choices)):
        pass_thresh_cond = res[1] > thresh
        if pass_thresh_cond:
            res_dict[choice_key % i] = res[0]

            if return_ratios:
                res_dict[choice_ratio_key % i] = res[1]
        else:
            break

    return pd.Series(res_dict)


# Preparing the values and the base dict used for the line by line result
values = list(set([clear_text(val) for val in values]))
pre_filled_dict = {choice_key % i: '' for i in range(nb_choices)}
if ratios:
    pre_filled_dict.update({choice_ratio_key % i: '' for i in range(nb_choices)})

# Preparing the function used on each line
get_choices_serie_vals = partial(get_choices_serie,
                                 choices=values,
                                 base_res_dict=pre_filled_dict,
                                 number_of_choices=nb_choices,
                                 return_ratios=ratios)

data = data_df[target_col_name].astype(str).fillna('')
result_df = data_df.merge(data.apply(get_choices_serie_vals), left_index=True, right_index=True)

# Write recipe outputs
output_dataset.write_with_schema(result_df)
