#!c:\merperf-cassiano\cli\.venv_37\scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'medperf','console_scripts','medperf'
__requires__ = 'medperf'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('medperf', 'console_scripts', 'medperf')()
    )
