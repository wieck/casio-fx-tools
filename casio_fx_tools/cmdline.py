import sys
import argparse
from casio_fx_tools.KCSCasio import *

def fx502p_load():
    # Parse command line
    parser = argparse.ArgumentParser(prog = 'fx502p_load',
        description = 'Load program(s) from text or binary data')
    parser.add_argument('-b', '--binary', action = 'store_true',
                        help = 'input data is binary')
    parser.add_argument('-o', '--output',
                        help = 'write WAV data to file instead of sound card')
    parser.add_argument('input',
                        help = 'program data (text or binary)')
    args = parser.parse_args()

    fx = KCSCasioFX502P()

    # Read the input data either as text or binary data
    if args.binary:
        with open(args.input, 'rb') as f:
            progbin = f.read()
    else:
        with open(args.input, 'r') as f:
            progtxt = f.read()

    # If we read text, convert it into binary program data
    if not args.binary:
        progbin = fx.text2prog(progtxt)

    # Write it to the requested output (default sound card)
    try:
        prog = fx.load_prog(progbin, args.output)
    except KeyboardInterrupt:
        sys.exit(1)

def fx502p_save():
    # Parse command line
    parser = argparse.ArgumentParser(prog = 'fx502p_save',
        description = 'Save program(s) to text or binary file')
    parser.add_argument('-b', '--binary', action = 'store_true',
                        help = 'output will be binary')
    parser.add_argument('-i', '--input',
                        help = 'use WAV file instead of sound card')
    parser.add_argument('output', nargs = '?',
                        help = 'write to file instead of stdout')
    args = parser.parse_args()

    # Get FX-502P binary data (either from file or sound card
    fx = KCSCasioFX502P()
    try:
        prog = fx.save_prog(args.input)
    except KeyboardInterrupt:
        sys.exit(0)

    # Convert FX-502P binary data into requested output (text/binary) to
    # stdout or file.
    if args.binary:
        if args.output is None:
            # Binary data to stdout
            sys.stdout.buffer.write(prog)
        else:
            # Binary data to file
            with open(args.output, 'wb') as out:
                out.write(prog)
    else:
        text = fx.prog2text(prog)
        if args.output is None:
            # Text data to stdout
            sys.stdout.write(text)
        else:
            # Text data to file
            with open(args.output, 'w') as out:
                out.write(text)

