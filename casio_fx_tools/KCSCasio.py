"""
KCSCasio.py
"""

from collections import deque
from itertools import islice
import sys
import math
import re
from casio_fx_tools.KCSProtocol import *

class KCSCasioFX502P:
    def __init__(self, rate = 48000, channels = 1, bits = 8,
                 base_freq = 2400, parity = KCS_PARITY_EVEN):
        self.rate      = rate
        self.channels  = channels
        self.bits      = bits
        self.base_freq = base_freq
        self.parity    = parity

        # Generate the text-to-byte lookup tokens
        self.TOKENS_T2B = {self.TOKENS_B2T[b]: b for b in self.TOKENS_B2T}

    def save_bytes(self, fname = None, gain = 1.0):
        """
        Read the binary data of an FX-502P program using KCSProtocol.

        Returns a bytes object of the binary program data.
        """
        raw_bytes = deque()
        with KCSReader(fname, rate = self.rate, channels = self.channels,
                       bits = self.bits, base_freq = self.base_freq,
                       parity = self.parity, gain = gain) as kcs:
            # First wait for the lead-in
            if not kcs.wait_for_lead_in():
                raise Exception("no FX502P lead-in")

            # Next wait for [0x00, 0xb0] indicating program data
            byteseq = kcs.generate_bytes()
            start, sbytes = self._wait_for_start(byteseq)

            # Collect bytes until we encounter a sequence of 0xFF
            # bytes. The FX502P writes a ton of them, but we don't
            # need to count them all.
            sample = deque(maxlen = 8)
            sample.extend(sbytes)
            sample.extend(islice(byteseq, 5))
            endmark = deque([0xff] * 8)
            for byte in byteseq:
                sample.append(byte)
                if sum(sample) == 2040:
                    break
                raw_bytes.append(sample.popleft())

        # Return the program(s) object as bytes data
        return bytes(raw_bytes)

    def load_bytes(self, data, fname = None, volume = 1.0):
        """
        Write the binary data of an FX-502P program using KCSProtocol.
        """
        with KCSWriter(fname, rate = self.rate, channels = self.channels,
                       bits = self.bits, base_freq = self.base_freq,
                       parity = self.parity, volume = volume) as kcs:
            # Create the lead-in
            kcs.write_lead_in()

            # Write the data of the program(s)
            kcs.write_bytes(data)

            # Write the lead-out (a sequence of 0xff bytes)
            kcs.write_bytes([0xff] * 50)

    def bytes2text(self, data):
        # Convert the first two bytes into the BCD encoded header bytes.
        start = "{0:02X}{1:02X}".format(data[1], data[0])

        if start[0] == 'B':
            # The header indicates a program. Emit the proper 'FPnnn' header.
            output = "FP" + start[1:]

            # Decode the remaining bytes as programe text.
            line = []
            for byte in data[2:]:
                # If there is a token for this byte value, use it.
                # Otherwise convert it into a hex number (There are
                # tokens for all 256 possible byte values, but just
                # in case).
                if int(byte) in self.TOKENS_B2T:
                    token = self.TOKENS_B2T[int(byte)]
                else:
                    token = '0x{0:02X}'.format(int(byte))

                # If the token ends in ':' we do a bit of special formatting
                if token[-1] == ':':
                    if len(line) > 0:
                        output += '\n    ' + ' '.join(line)
                        line = []
                    output += '\n'
                    if token[0] == 'P':
                        output += '' + token
                    else:
                        output += '  ' + token
                else:
                    line.append(token)

                # Break up lines so they don't exceed 80 characters
                if len(' '.join(line)) >= 70:
                    output += '\n    ' + ' '.join(line)
                    line = []

            # Emit anything left in the decoded line.
            if len(line) > 0:
                output += '\n    ' + ' '.join(line)

        elif start[0] == 'F':
            # The header indicates memory data. Emit the 'F nnn' header.
            output = "F " + start[1:] + '\n'
            data = data[2:]

            # Decode and add all non-zero registers to the output.
            for mem in self.MEMORY_SEQ:
                num = islice(data, 8)
                data = data[8:]
                outnum = self._bytes2number(num)
                if outnum != '0.0':
                    output = output + mem + ': ' + outnum + '\n'
        else:
            # Didn't recognize what this byte stream means.
            raise Exception("unrecognized FX502P data header '{0}'", start)
            
        return output + '\n'

    def _bcd2digits(self, bcd):
        return "{0:02X}".format(bcd)

    def _bytes2number(self, data):
        # Convert an FX502P number into something readable
        # We first consume the BCD encoded exponent and the binary flags
        exponent = int(self._bcd2digits(next(data)))
        flags = next(data)

        # Next we consume the 6 BCD encoded bytes. Those make up 10 decimal
        # digits in reverse byte order and the first and last nibble ignored.
        # Yes, that is a rather strange storage format. We convert that into
        # float value representing the mantissa.
        digits = ""
        for byte in data:
            digits = self._bcd2digits(byte) + digits
        digits = (digits[1] + '.' + digits[2:])
        val = float(digits)

        # Apply the negative flag
        if flags & 0x08:
            val = -val

        # Add the exponent depending on exponent sign and convert
        # it all to float and back to string to make it most readable.
        if flags & 0x01:
            return str(float(str(val) + 'e' + str(exponent)))
        else:
            return str(float(str(val) + 'e-' + str(100 - exponent)))

    def _line_gen(self, txt):
        # generate lines from a multi-line string
        for line in txt.split('\n'):
            line = line.strip()
            if line == "" or line[0] == '#':
                continue
            yield line

    def text2bytes(self, txt):
        """
        Convert a program text into FX502P bytes
        """
        data = deque()
        es = ""
        e = 0
        l = 0

        # Get a line generator
        lines = self._line_gen(txt)

        # The first line for FX502P data is supposed to be
        # 'FPnnn' for program data and 'F nnn' for memory
        # data where 'nnn' is the 3-digits entered at SAVE.
        header = next(lines)
        m = re.match('^(F[P ])(\d\d\d)$', header)
        if m is None:
            raise Exception("no FX502P header in '{0}'".format(header))

        # Handle Program text
        if m.group(1) == 'FP':
            # Create the binary program header
            data.append(int(m.group(2)[1:], 16))
            data.append(int('B' + m.group(2)[0], 16))

            # Turn the remaining input into tokens and then into bytes
            for line in lines:
                toks = line.split()
                for tok in toks:
                    if tok not in self.TOKENS_T2B:
                        es += "line {0}: unrecognized token '{1}'\n".format(l, tok)
                        e += 1
                    else:
                        data.append(self.TOKENS_T2B[tok])

        # Handle Memory Register text
        elif m.group(1) == 'F ':
            data.append(int(m.group(2)[1:], 16))
            data.append(int('F' + m.group(2)[0], 16))

            # Initialize an array with all registers set to 0.0
            registers = {m: 0.0 for m in self.MEMORY_SEQ}

            for line in lines:
                # Process all the lines and change the register values
                m = re.match('^([^:]*):\s*(.*)', line)
                if m is None:
                    es += "line {0}: invalid format '{1}'\n".format(l, line)
                    e += 1
                    continue

                # Convert the register name and value
                reg = m.group(1)
                try:
                    val = float(m.group(2))
                except Exception as ex:
                    ex += "line {0}:" + str(ex) + '\n'
                    e += 1
                    continue

                # Check that we know this register name
                if reg not in registers:
                    es += "line {0}: unknown register '{1}'\n".format(l, reg)
                    e += 1
                    continue

                # Change the value of the register to what we read
                registers[reg] = val

            # We have the full array of register values now.
            for reg in self.MEMORY_SEQ:
                data.extend(self._float2bytes(registers[reg]))

        else:
            raise Exception("no FX502P header in '{0}'".format(header))

        if e > 0:
            raise Exception(es + "{0} error(s) parsing program text".format(e))
        
        return bytes(data)
        
    def _float2bytes(self, val):
        if val == 0.0:
            return deque([0, 0, 0, 0, 0, 0, 0, 0])

        result = deque()
        flags = 0x00

        # Convert the value into %1.9e format and split it via regexp
        strval = "{0:1.9e}".format(val)
        m = re.match('(-?)(\d)\.(\d*)e([-\+])(\d*)', strval)

        # Set flag if mantissa is negative
        if m.group(1) == '-':
            flags |= 0x08

        # Set flag and add exponent depending on sign of exponent
        if m.group(4) == '+':
            flags |= 0x01
            result.append(int("{0:02d}".format(int(m.group(5))), 16))
        else:
            result.append(int("{0:02d}".format(100 - int(m.group(5))), 16))
        
        # Add the flag byte
        result.append(flags)

        # Add the mantissa digits
        digits = '0' + m.group(2) + m.group(3) + '0'
        for i in [10, 8, 6, 4, 2, 0]:
            result.append(int(digits[i:i + 2], 16))

        return result

    def _wait_for_start(self, byteseq):
        # Wait for a valid FX502P start header. The start header consists
        # of 0xBnnn for a program or 0xFnnn for memory data, but in reverse
        # byte order and BCD encoded. So a program with header number 123
        # will be represented as 0x23, 0xB1.
        sample = deque(maxlen = 2)
        sample.extend(islice(byteseq, 1))

        for byte in byteseq:
            sample.append(byte)
            start = "{0:02X}{1:02X}".format(sample[1], sample[0])
            m = re.match('^[BF]\d\d\d', start)
            if m is not None:
                return start, bytes(sample)
        raise Exception("no valid start sequence found")

    MEMORY_SEQ = [
        'MF', 'M9', 'M8', 'M7', 'M6', 'M5',
        'M4', 'M3', 'M2', 'M1', 'M0',
        'M1F', 'M19', 'M18', 'M17', 'M16', 'M15',
        'M14', 'M13', 'M12', 'M11', 'M10']

    TOKENS_B2T = {
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
    }

