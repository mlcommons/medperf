# Hello World Script
#
# This script is unrelated to the MLCube interface. It could be run
# independently without issues. It provides the actual implementation
# of the app.
import os
import csv
import argparse

def hello_world(greetings, names, uppercase=False):
    """Generates a combination of greetings and names

    Args:
        greetings (List[str]): list of greetings
        names (List[str]): list of names
        uppercase (bool): Wether to uppercase the whole greeting

    Returns:
        List[str]: combinations of greetings and names
    """
    full_greetings = []
    
    for greeting in greetings:
        for name, last_name in names:
            full_greeting = f"{greeting}, {name} {last_name}"
            if uppercase:
                full_greeting = full_greeting.upper()
            full_greetings.append(full_greeting)

    return full_greetings


if __name__ == '__main__':
    parser = argparse.ArgumentParser("MedPerf Model Hello World Example")
    parser.add_argument('--names', dest="names", type=str, help="directory containing names")
    parser.add_argument('--uppercase', dest="uppercase", type=bool, help="wether to return uppercase greetings")
    parser.add_argument('--greetings', dest="greetings", type=str, help="directory containing greetings")
    parser.add_argument('--out', dest="out", type=str, help="path to store resulting greetings")

    args = parser.parse_args()

    names = []
    greetings = []

    with open(args.names, "r") as f:
        reader = csv.reader(f)
        next(reader) # skip header
        for row in reader:
            names.append(row)

    with open(args.greetings, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            greetings.append(row[0]) 

    full_greetings = hello_world(greetings, names, args.uppercase)

    out_file = os.path.join(args.out, "predictions.csv")
    with open(out_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "greeting"])
        for idx, full_greeting in enumerate(full_greetings):
            writer.writerow([idx, full_greeting])
