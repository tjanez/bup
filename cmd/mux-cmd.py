#!/bin/sh
"""": # -*-python-*-
bup_python="$(dirname "$0")/bup-python" || exit $?
exec "$bup_python" "$0" ${1+"$@"}
"""
# End preamble.
import os, sys, subprocess, struct
from bup import options
from bup.helpers import *

# Give the subcommand exclusive access to stdin.
orig_stdin = os.dup(0)
devnull = os.open('/dev/null', os.O_RDONLY)
os.dup2(devnull, 0)
os.close(devnull)

optspec = """
bup mux command [arguments...]
--
"""
o = options.Options(optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])
if len(extra) < 1:
    o.fatal('command is required')

subcmd = extra

debug2('bup mux: starting %r\n' % (extra,))

outr, outw = os.pipe()
errr, errw = os.pipe()
def close_fds():
    os.close(outr)
    os.close(errr)

p = subprocess.Popen(subcmd, stdin=orig_stdin, stdout=outw, stderr=errw,
                     preexec_fn=close_fds)
os.close(outw)
os.close(errw)
sys.stdout.write('BUPMUX')
sys.stdout.flush()
mux(p, sys.stdout.fileno(), outr, errr)
os.close(outr)
os.close(errr)
prv = p.wait()

if prv:
    debug1('%s exited with code %d\n' % (extra[0], prv))

debug1('bup mux: done\n')

sys.exit(prv)
