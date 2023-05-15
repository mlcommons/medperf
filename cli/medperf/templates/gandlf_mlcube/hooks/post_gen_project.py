#!/usr/bin/env python
import os

PROJECT_DIRECTORY = os.path.realpath(os.path.curdir)


if __name__ == "__main__":
    os.makedirs("workspace", exist_ok=True)
