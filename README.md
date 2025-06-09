# casio-fx-tools

**Tools to save and load CASIO FX calculator programs and data using the
[Kansas City Standard](https://en.wikipedia.org/wiki/Kansas_City_standard)
protocol.**

[CASIO](https://en.wikipedia.org/wiki/Casio)
made several programmable pocket calculators with Cassette Tape interfaces
to save and load programs and data using the *Kansas City Standard* or
variations of it.

# Table of Contents
* [Supported Calculators](#supported-calculators)
* [Installation and setup](#installation-and-setup)
* [FX-502P Save Programs to File](#fx-502p-save-programs-to-file)
* [FX-502P Load Programs from File](#fx-502p-load-programs-from-file)
* [FX-502P Program Tokens](#fx-502p-program-tokens)
* [FX-502P Wire Protocol](#fx-502p-wire-protocol)
* [Credits](#credits)

## Supported Calculators

* FX-502P with FA-1 interface (most likely the FX-501P will work too)

## Installation and Requirements

It is recommended to install these tools in a
[Python Virtual Environment](https://docs.python.org/3/library/venv.html).
After creating the venv perform
```
python3 ./setup.py install
```

The [sox(1)](https://sourceforge.net/projects/sox/)
Sound eXchange program needs to be installed. This utility is available
in all major Linux distributions and for Windows.

Like we had to in the old days using real Cassette Tape recorders,
volume levels need to be adjusted. There will be some trial and error
involved in this.

## FX-502P Save Programs to File

The command `fx502p_save` can read a recorded audio file or directly from the
sound card and save the program(s) to a file or stdout. 
```
$ fx502p_save -h
usage: fx502p_save [-h] [-b] [-i INPUT] [-g GAIN] [output]

Save program(s) to text or binary file

positional arguments:
  output                write to file instead of stdout

optional arguments:
  -h, --help            show this help message and exit
  -b, --binary          output will be binary
  -i INPUT, --input INPUT
                        use sound file instead of sound card
  -g GAIN, --gain GAIN  apply gain to the input
```

Without any options or arguments it will read from the sound card and
output a text version of all programs or memory registers to stdout.

```
$ fx502p_save
FP000
P0:
    2 + 2 =
```

Providing an output file name will write to that.
```
$ fx502p_save test1.cas
$ cat test1.cas
FP000
P0:
    2 + 2 =
```

The `--binary` option allows to save raw byte data representing the
program(s).
```
$ fx502p_save -b test1.bin
$ od -tx1 test1.bin
0000000 00 b0 00 0c 5c 0c 5
0000007
```

If the `fx502p_save` program is experiencing *parity errors* it may
be because of low recording levels. The `--gain db` option can be used
to increase the volume.


## FX-502P Load Programs from File

The command `fx502p_load` can read a text or binary file and produce
the equivalent .WAV audio file or send it directly to the sound card.

```
$ fx502p_load -h
usage: fx502p_load [-h] [-b] [-o OUTPUT] [-v VOLUME] input

Load program(s) from text or binary data

positional arguments:
  input                 program data (text or binary)

optional arguments:
  -h, --help            show this help message and exit
  -b, --binary          input data is binary
  -o OUTPUT, --output OUTPUT
                        write WAV data to file instead of sound card
  -v VOLUME, --volume VOLUME
                        when writing to sound card adjust volume```
```

If the input file is a text file it should be in a similar format as
the example given in the `fx502p_save` above using the tokens listed
below.


## FX-502P Program Tokens

The text representation of a CASIO FX-502P program is tokens
for each byte of the program's binary data. Each *step* in the
calculator's memory is represented by one byte, no matter how
many keys had to be pressed to create that *step*. Note that some
byte values are impossible to input on the calculator. For example
the actual keystroke values for **BST** and **FST** exist, but
obviously cannot appear in a real program. So please be careful
when feeding your calculator random binary data.

There is no formatting required. Any amount of whitespace between
tokens will work. A `#` sign at the start of a line can be used to
add comments.

The list of interpreted tokens in `KCSCasio.py` is
```
        0x00:   'P0:',
        0x01:   'P1:',
        0x02:   'P2:',
        0x03:   'P3:',
        0x04:   'P4:',
        0x05:   'P5:',
        0x06:   'P6:',
        0x07:   'P7:',
        0x08:   'P8:',
        0x09:   'P9:',
        0x0a:   '0',
        0x0b:   '1',
        0x0c:   '2',
        0x0d:   '3',
        0x0e:   '.',
        0x0f:   'EXP',

        0x10:   'RND0',
        0x11:   'RND1',
        0x12:   'RND2',
        0x13:   'RND3',
        0x14:   'RND4',
        0x15:   'RND5',
        0x16:   'RND6',
        0x17:   'RND7',
        0x18:   'RND8',
        0x19:   'RND9',
        0x1a:   '4',
        0x1b:   '5',
        0x1c:   '6',
        0x1d:   '7',
        0x1e:   '8',
        0x1f:   '9',

        0x20:   'LBL0:',
        0x21:   'LBL1:',
        0x22:   'LBL2:',
        0x23:   'LBL3:',
        0x24:   'LBL4:',
        0x25:   'LBL5:',
        0x26:   'LBL6:',
        0x27:   'LBL7:',
        0x28:   'LBL8:',
        0x29:   'LBL9:',
        0x2a:   'HLT',
        0x2b:   '??2b??',
        0x2c:   '??2c??',
        0x2d:   '??2d??',
        0x2e:   '??2e??',
        0x2f:   '??2f??',

        0x30:   'GOTO0',
        0x31:   'GOTO1',
        0x32:   'GOTO2',
        0x33:   'GOTO3',
        0x34:   'GOTO4',
        0x35:   'GOTO5',
        0x36:   'GOTO6',
        0x37:   'GOTO7',
        0x38:   'GOTO8',
        0x39:   'GOTO9',
        0x3a:   '??3a??',
        0x3b:   '??3b??',
        0x3c:   'ENG',
        0x3d:   'ooo',
        0x3e:   'log',
        0x3f:   'ln',

        0x40:   'GSB-P0',
        0x41:   'GSB-P1',
        0x42:   'GSB-P2',
        0x43:   'GSB-P3',
        0x44:   'GSB-P4',
        0x45:   'GSB-P5',
        0x46:   'GSB-P6',
        0x47:   'GSB-P7',
        0x48:   'GSB-P8',
        0x49:   'GSB-P9',
        0x4a:   '+/-',
        0x4b:   '(',
        0x4c:   ')',
        0x4d:   'sin',
        0x4e:   'cos',
        0x4f:   'tan',

        0x50:   'X<->M0',
        0x51:   'X<->M1',
        0x52:   'X<->M2',
        0x53:   'X<->M3',
        0x54:   'X<->M4',
        0x55:   'X<->M5',
        0x56:   'X<->M6',
        0x57:   'X<->M7',
        0x58:   'X<->M8',
        0x59:   'X<->M9',
        0x5a:   '*',
        0x5b:   '/',
        0x5c:   '+',
        0x5d:   '-',
        0x5e:   '=',
        0x5f:   'EXE',

        0x60:   'Min0',
        0x61:   'Min1',
        0x62:   'Min2',
        0x63:   'Min3',
        0x64:   'Min4',
        0x65:   'Min5',
        0x66:   'Min6',
        0x67:   'Min7',
        0x68:   'Min8',
        0x69:   'Min9',
        0x6a:   '??6a??',
        0x6b:   'DSZ',
        0x6c:   'X=0',
        0x6d:   'X=F',
        0x6e:   'RAN#',
        0x6f:   'PI',

        0x70:   'MR0',
        0x71:   'MR1',
        0x72:   'MR2',
        0x73:   'MR3',
        0x74:   'MR4',
        0x75:   'MR5',
        0x76:   'MR6',
        0x77:   'MR7',
        0x78:   'MR8',
        0x79:   'MR9',
        0x7a:   'ISZ',
        0x7b:   'X>=0',
        0x7c:   'X>=F',
        0x7d:   'mean(x)',
        0x7e:   'stddev',
        0x7f:   'stddev-1',

        0x80:   'M-0',
        0x81:   'M-1',
        0x82:   'M-2',
        0x83:   'M-3',
        0x84:   'M-4',
        0x85:   'M-5',
        0x86:   'M-6',
        0x87:   'M-7',
        0x88:   'M-8',
        0x89:   'M-9',
        0x8a:   'PAUSE',
        0x8b:   'IND',
        0x8c:   'SAVE',
        0x8d:   'LOAD',
        0x8e:   'MAC',
        0x8f:   'SAC',

        0x90:   'M+0',
        0x91:   'M+1',
        0x92:   'M+2',
        0x93:   'M+3',
        0x94:   'M+4',
        0x95:   'M+5',
        0x96:   'M+6',
        0x97:   'M+7',
        0x98:   'M+8',
        0x99:   'M+9',
        0x9a:   'DEL',
        0x9b:   '??9b??',
        0x9c:   'ENG<-',
        0x9d:   'ooo<-',
        0x9e:   '10^X',
        0x9f:   'e^X',

        0xa0:   'X<->M10',
        0xa1:   'X<->M11',
        0xa2:   'X<->M12',
        0xa3:   'X<->M13',
        0xa4:   'X<->M14',
        0xa5:   'X<->M15',
        0xa6:   'X<->M16',
        0xa7:   'X<->M17',
        0xa8:   'X<->M18',
        0xa9:   'X<->M19',
        0xaa:   'ABS',
        0xab:   'INT',
        0xac:   'FRAC',
        0xad:   'asin',
        0xae:   'acos',
        0xaf:   'atan',

        0xb0:   'Min10',
        0xb1:   'Min11',
        0xb2:   'Min12',
        0xb3:   'Min13',
        0xb4:   'Min14',
        0xb5:   'Min15',
        0xb6:   'Min16',
        0xb7:   'Min17',
        0xb8:   'Min18',
        0xb9:   'Min19',
        0xba:   'X^Y',
        0xbb:   'X^(1/Y)',
        0xbc:   'R->P',
        0xbd:   'P->R',
        0xbe:   '%',
        0xbf:   '??bf??',

        0xc0:   'MR10',
        0xc1:   'MR11',
        0xc2:   'MR12',
        0xc3:   'MR13',
        0xc4:   'MR14',
        0xc5:   'MR15',
        0xc6:   'MR16',
        0xc7:   'MR17',
        0xc8:   'MR18',
        0xc9:   'MR19',
        0xca:   '??ca??',
        0xcb:   'X<->Y',
        0xcc:   'sqrt',
        0xcd:   'X^2',
        0xce:   '1/X',
        0xcf:   'X!',

        0xd0:   'M-10',
        0xd1:   'M-11',
        0xd2:   'M-12',
        0xd3:   'M-13',
        0xd4:   'M-14',
        0xd5:   'M-15',
        0xd6:   'M-16',
        0xd7:   'M-17',
        0xd8:   'M-18',
        0xd9:   'M-19',
        0xda:   'DEG',
        0xdb:   'RAD',
        0xdc:   'GRA',
        0xdd:   'hyp-sin',
        0xde:   'hyp-cos',
        0xdf:   'hyp-tan',

        0xe0:   'M+10',
        0xe1:   'M+11',
        0xe2:   'M+12',
        0xe3:   'M+13',
        0xe4:   'M+14',
        0xe5:   'M+15',
        0xe6:   'M+16',
        0xe7:   'M+17',
        0xe8:   'M+18',
        0xe9:   'M+19',
        0xea:   '??ea??',
        0xeb:   '??eb??',
        0xec:   '??ec??',
        0xed:   'hyp-asin',
        0xee:   'hyp-acos',
        0xef:   'hyp-atan',

        0xf0:   'X<->MF',
        0xf1:   'MinF',
        0xf2:   'MRF',
        0xf3:   'M-F',
        0xf4:   'M+F',
        0xf5:   'X<->M1F',
        0xf6:   'Min1F',
        0xf7:   'MR1F',
        0xf8:   'M-1F',
        0xf9:   'M+1F',
        0xfa:   'AC',
        0xfb:   'NOP',
        0xfc:   '??fc??',
        0xfd:   '??fd??',
        0xfe:   '??fe??',
        0xff:   'EOF',
```


## FX-502P Example Programs

### CASIO Program Library Chapter 2 - Electricity

* [Electricity-1](examples/casio_program_library/electricity-1/electricity-1.md) Delta-Y Conversion

### Other Programs

* [Annuities](examples/annuities.md): A set of programs that calculate annuities like mortgage loans.


## FX-502P Wire Protocol

The FX-502P with the FA-1 adaptor uses a variant of the
[Kansas City Standard](https://en.wikipedia.org/wiki/Kansas_City_standard)
Cassette Tape protocol. The base frequency is 2400Hz. A `ONE` bit is
encoded as 8 cycles of 2400Hz. A `ZERO` bit is encoded as 4 cycles of
1200HZ. Each byte is encoded as a `ZERO` start bit, 8 `DATA` bits, an
`EVEN-PARITY` bit and two `ONE` stop bits.

A complete program is encoded as a lead-in of 2400Hz (about 3 seconds),
a `[0x00, 0xB0]` byte sequence, the tokens for each program (starting
with `P0:..P9`) and finally a series of `0xFF` bytes signaling EOF.


## Credits

Some of the code, specifically the decoding of audio, has been
heavily influenced (AKA copied) from the
[py-kcs](https://www.dabeaz.com/py-kcs/)
project by 
[David Beazley](http://www.dabeaz.com). Thank you Sir.
