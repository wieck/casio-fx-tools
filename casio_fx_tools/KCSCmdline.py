import sys
import argparse
from casio_fx_tools.KCSCasio import *
from casio_fx_tools.KCSProtocol import *

def fx502p_load():
    # Parse command line
    parser = argparse.ArgumentParser(prog = 'fx502p_load',
        description = 'Load program(s) from text or binary data')
    parser.add_argument('-b', '--binary', action = 'store_true',
                        help = 'input data is binary')
    parser.add_argument('-o', '--output',
                        help = 'write WAV data to file instead of sound card')
    parser.add_argument('-v', '--volume',
                        help = 'when writing to sound card adjust volume',
                        type = float, default = 1.0)
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
        progbin = fx.text2bytes(progtxt)

    # Write it to the requested output (default sound card)
    try:
        prog = fx.load_bytes(progbin, args.output, volume = args.volume)
    except KeyboardInterrupt:
        sys.exit(1)
    except KCSException as ex:
        print("Error:", str(ex), file = sys.stderr)
        sys.exit(1)

def fx502p_save():
    # Parse command line
    parser = argparse.ArgumentParser(prog = 'fx502p_save',
        description = 'Save program(s) to text or binary file')
    parser.add_argument('-b', '--binary', action = 'store_true',
                        help = 'output will be binary')
    parser.add_argument('-i', '--input',
                        help = 'use sound file instead of sound card')
    parser.add_argument('-g', '--gain',
                        help = 'apply gain to the input',
                        type = float, default = 1.0)
    parser.add_argument('output', nargs = '?',
                        help = 'write to file instead of stdout')
    args = parser.parse_args()

    # Get FX-502P binary data (either from file or sound card
    fx = KCSCasioFX502P()
    try:
        data = fx.save_bytes(args.input, gain = args.gain)
    except KeyboardInterrupt:
        sys.exit(1)
    except KCSException as ex:
        print("Error:", str(ex), file = sys.stderr)
        sys.exit(1)

    # Convert FX-502P binary data into requested output (text/binary) to
    # stdout or file.
    if args.binary:
        if args.output is None:
            # Binary data to stdout
            sys.stdout.buffer.write(data)
        else:
            # Binary data to file
            with open(args.output, 'wb') as out:
                out.write(data)
    else:
        text = fx.bytes2text(data)

        if args.output is None:
            # Text data to stdout
            sys.stdout.write(text)
        else:
            # Text data to file
            with open(args.output, 'w') as out:
                out.write(text)

def kcs_analyze():
    # Parse command line
    parser = argparse.ArgumentParser(prog = 'fx502p_save',
        description = 'Save program(s) to text or binary file')
    parser.add_argument('-i', '--input',
                        help = 'use WAV file instead of sound card')
    parser.add_argument('-g', '--gain',
                        help = 'when reading from sound card add gain',
                        type = float, default = 1.0)
    parser.add_argument('-p', '--parity',
                        help = 'use {even|odd} parity')
    parser.add_argument('-r', '--framerate',
                        help = 'sampling rate (default 48000Hz)',
                        type = int, default = 48000)
    parser.add_argument('-f', '--basefreq',
                        help = 'base frequence (default 2400Hz)',
                        type = int, default = 2400)
    args = parser.parse_args()

    if args.parity is None:
        parity = None
    elif args.parity == 'even':
        parity = KCS_PARITY_EVEN
    elif args.parity == 'odd':
        parity = KCS_PARITY_ODD
    else:
        print("unknown parity '{0}'".format(args.parity), file = sys.stderr)
        sys.exit(2)

    try:
        with KCSReader(args.input, rate = args.framerate,
                       base_freq = args.basefreq, parity = parity,
                       gain = args.gain) as kcs:
            if not kcs.wait_for_lead_in():
                print("no lead-in detected", file = sys.stderr)
                sys.exit(1)
            for byte in kcs.generate_bytes():
                print("0x{0:02X} ".format(byte), end = "")
                sys.stdout.flush()
    except KeyboardInterrupt:
        print("")
        sys.exit(1)
    except KCSException as ex:
        print("")
        print("Error:", str(ex), file = sys.stderr)
        sys.exit(1)
