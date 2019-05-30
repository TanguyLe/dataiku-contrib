# Fuzzy Tools Plugin
Fuzzy Tools is a small dataiku DSS plugin wrapping the python package 
fuzzywuzzy via two recipes.
## Fuzzy Filter
Fuzzy filter allows you to filter a dataset by removing or keeping rows 
that match a defined value above a certain confidence threshold.
For that, you can use the four fuzzywuzzy scorers :
- Simple Ratio : Just the matching between the two strings using Levenshtein distance.
- Partial Ratio : Looks for your value within the string, can reach 100% if it is contained in it. (Not affected by extra content)
- Token Sort Ratio : Not affected by the sorting order of the words.
- Token Set Ratio : Not affected by the sorting order of the words and extra content.


For instance you could :
- Keep all rows where the departement is close enough to "sales" 
("sales management", "sales engineering", "1.Sales", "saless", "saales"...)
- Remove rows that contain something that looks like a curse word :)
- Detect text which contains a particular citation
- Detect text which has been copy-pasted with minor changes

etc..

## Fuzzy Choice
The idea with the Fuzzy Choice recipe is very close.
It uses one input dataset and some values 
(provided from a defined list, or a dataset column), and 
creates n (parameter) new columns containing the n best matches 
from the values provided with a column of the original dataset.

For instance, let's say the choices are ["hello", "hi", "bye"], 
the number of choices is 2 and the
input data is a column with ["hel", "hii", "h", "hello you", "bye bye"].
The output dataset will have two new columns 
called "choice_0" and "choice_1" with values
["hello", "hi", "hi", "hello", "bye"] and 
["hi", "hello", "bye", "bye", "hi"].

Disclaimer : this example output may not be 100% accurate :)

Options are:
- Using any of the four fuzzywuzzy filters
- Using values from both a defined list and a dataset
- Changing the number of choices kept
- Changing the confidence threshold
- Picking the ratio type
- Extracting the ratio values in columns named "choice_ratio_x"


