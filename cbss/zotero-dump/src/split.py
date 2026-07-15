import argparse
import json
import os

"""
This script takes an input directory containing JSON files of a data dump from Zotero, chunked
into multiple records. It outputs a set of files to a specified output directory a single JSON
file for each Zotero record, named based on the Zotero record's Item Key
"""

"""
This function takes input and output string parameters, each representing a directory path.
It loads the JSON files found in the input directory, parses the Zotero records (JSON objects)
It then saves them to the output directory as a single file for each Zotero record, based on the
Item Key
"""
def split_records(input: str, output: str):
    # files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    for file in os.listdir(input):
        # Ignore sub-directories
        if not(os.path.isfile(os.path.join(input, file))):
            continue
        data = []
        with open(os.path.join(input, file), mode='r') as in_file:
            data = json.load(in_file)
        for rec in data:
            item_key = rec["key"]
            with open(output+item_key+".json", mode="w+") as out_file:
                json.dump(rec, out_file, indent=2)

if __name__ == "__main__":
    # Get the command line variables via argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Path to the directory containing chunked Zotero records", required=True)
    parser.add_argument("-o", "--output", help="Path to the directory where per-record JSON files should be stored", required=True)
    args = parser.parse_args()

    # create the output directory if it does not exist
    os.makedirs(args.output, exist_ok=True)
    
    # Run the record splitting function
    split_records(args.input, args.output)