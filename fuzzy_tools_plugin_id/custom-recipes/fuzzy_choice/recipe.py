# Code for custom code recipe fuzzy_filter (imported from a Python recipe)

# To finish creating your custom recipe from your original PySpark recipe, you need to:
#  - Declare the input and output roles in recipe.json
#  - Replace the dataset names by roles access in your code
#  - Declare, if any, the params of your custom recipe in recipe.json
#  - Replace the hardcoded params values by acccess to the configuration map

# See sample code below for how to do that.
# The code of your original recipe is included afterwards for convenience.
# Please also see the "recipe.json" file for more information.

# import the classes for accessing DSS objects from the recipe
import dataiku
# Import the helpers for custom recipes
from dataiku.customrecipe import *

# Inputs and outputs are defined by roles. In the recipe's I/O tab, the user can associate one
# or more dataset to each input and output role.
# Roles need to be defined in recipe.json, in the inputRoles and outputRoles fields.

# To  retrieve the datasets of an input role named 'input_A' as an array of dataset names:
input_dataset_name = get_input_names_for_role('input_dataset')[0]
# The dataset objects themselves can then be created like this:
input_dataset = dataiku.Dataset(input_dataset_name)

values_dataset_name = get_input_names_for_role('values_dataset')[0]
values_dataset = dataiku.Dataset(values_dataset_name)

# For outputs, the process is the same:
output_dataset_name = get_output_names_for_role('output_dataset')[0]
output_dataset = dataiku.Dataset(output_dataset_name)


# The configuration consists of the parameters set up by the user in the recipe Settings tab.

# Parameters must be added to the recipe.json file so that DSS can prompt the user for values in
# the Settings tab of the recipe. The field "params" holds a list of all the params for wich the
# user will be prompted for values.

# The configuration is simply a map of parameters, and retrieving the value of one of them is simply:
parameters = get_recipe_config()

# For optional parameters, you should provide a default value in case the parameter is not present:
# my_variable = get_recipe_config().get('parameter_name', None)

# Note about typing:
# The configuration of the recipe is passed through a JSON object
# As such, INT parameters of the recipe are received in the get_recipe_config() dict as a Python float.
# If you absolutely require a Python int, use int(get_recipe_config()["my_int_param"])


#############################
# Your original recipe
#############################

# -*- coding: utf-8 -*-
import pandas as pd
from fuzzywuzzy import fuzz, process
from functools import partial
import string
from unidecode import unidecode

# Read recipe inputs
data_df = input_dataset.get_dataframe()
values_df = values_dataset.get_dataframe()

# Reading ui parameters
target_col_name = parameters["target_col"]
values = parameters["values"].split(',')
values_colname = parameters["values_colname"]
nb_choices = int(parameters["nb_choices"])
thresh = parameters["thresh"]
ratio_type = parameters["ratio_type"]
ratios = parameters["ratios"]

if values_colname:
    values_series = values_df[values_colname]
    if not values_series.empty:
        values += values_series.tolist()

if nb_choices > len(values):
    raise ValueError("More number of choices than provided values.")

# fetching the scorer to use from the fuzzywuzzy module
ratio_fct = getattr(fuzz, ratio_type)

printable = set(string.printable)


def clear_text(text):
    """ Tries to remove accents but keep the underlying letter using unidecode. 
        If it fails, just removes the non-ascii chars """
    try:
        return unidecode(text)
    except UnicodeDecodeError:
        # This happens in case of cyrilic chars, smileys...
        return filter(lambda x: x in printable, text)


def get_choices(text, vals, nb_choices=1):
    """ Returns a list of tuples with (choice, score) """
    return process.extract(clear_text(text), vals, limit=nb_choices, scorer=ratio_fct)


choice_key = "choice_%d"
choice_ratio_key = choice_key + "_ratio"


def get_choices_serie(text, vals, nb_choices=1, ratios=False):
    res_dict = {}
    for i, res in enumerate(get_choices(text=text, vals=vals, nb_choices=nb_choices)):
        pass_thresh = res[1] > thresh
        res_dict[choice_key % i] = res[0] if pass_thresh else ''
        if ratios:
            res_dict[choice_ratio_key % i] = res[1] if pass_thresh else ''

    return pd.Series(res_dict)


values = list(set([clear_text(val) for val in values]))
get_choices_serie_vals = partial(get_choices_serie, vals=values, nb_choices=nb_choices, ratios=ratios)

data = data_df[target_col_name].astype(str).fillna('')
result_df = data_df.merge(data.apply(get_choices_serie_vals), left_index=True, right_index=True)

# Write recipe outputs
output_dataset.write_with_schema(result_df)
