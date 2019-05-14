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
from fuzzywuzzy import fuzz
from functools import partial
import string
from unidecode import unidecode

# Read recipe inputs
data_df = input_dataset.get_dataframe()

target_col_name = parameters["target_col"]
value = parameters["value"]
thresh = parameters["thresh"]
ratio_type = parameters["ratio_type"]
action = parameters["action"]

ratio_fct = getattr(fuzz, ratio_type)

printable = set(string.printable)


def clear_text(text):
    """ Tries to remove accents but keep the underlying letter using unidecode. 
        If it fails, just removes the non-ascii chars """
    try:
        return unidecode(text)
    except UnicodeDecodeError:
        return filter(lambda x: x in printable, text)


def get_fuzz_ratio(text, val):
    return ratio_fct(val, clear_text(text))


get_fuzz_ratio_val = partial(get_fuzz_ratio, val=value)

data = data_df[target_col_name].astype(str).fillna('')
ratios = data.apply(get_fuzz_ratio_val)
above_thresh = ratios >= thresh

if action == "keep":
    result_df = data_df.loc[above_thresh, :]
else:
    result_df = data_df.loc[~above_thresh, :]

# Write recipe outputs
output_dataset.write_with_schema(result_df)
