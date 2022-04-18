import os, pathlib
import shutil
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser("Medperf Data Preparator Example")
    parser.add_argument("--input_dir", dest="input", type=str, help="path containing raw names")
    parser.add_argument("--out", dest="out" , type=str, help="path to store prepared data")

    args = parser.parse_args()

    pathlib.Path.mkdir(args.out, parents=True, exist_ok=True)

    shutil.copytree(args.input, args.out)
