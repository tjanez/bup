#!/bin/sh
"""": # -*-python-*-
bup_python="$(dirname "$0")/bup-python" || exit $?
exec "$bup_python" "$0" ${1+"$@"}
"""
# End preamble.
import sys
from bup import git, vfs, ls
from bup.helpers import *


git.check_repo_or_die()
top = vfs.RefList(None)

# Check out lib/bup/ls.py for the opt spec
ret = ls.do_ls(sys.argv[1:], top, default='/', spec_prefix='bup ')
sys.exit(ret)
