"""
KCSProtocol.py

Classes that handles the Kansas City Standard audio protocol by converting
audio to/from byte data.
"""

from collections import deque
from itertools import islice
import io
import wave
import subprocess

KCS_BASE_FREQ = 2400

KCS_PARITY_EVEN   = 0
KCS_PARITY_ODD    = 1

class KCSReader:
    """
    KCSReader

    Class to decode Kansas City Standard audio into bytes. If a filename
    is provided, the file should be a .WAV and will be used as the audio
    source. Otherwise the sox(1) program is used to read directly from
    the default audio device.
    """
    def __init__(self, fname = None, rate = 48000, channels = 1, bits = 8,
                 base_freq = KCS_BASE_FREQ, parity = None, gain = 1.0):
        self.fname = fname
        self.framerate = rate
        self.sampwidth = bits
        self.nchannels = channels
        self.base_freq = base_freq
        self.parity    = parity
        self.gain      = gain

        if self.fname is None:
            # Reading from the default audio device via sox(1)
            self._open_device(self.framerate, self.sampwidth,
                                  self.nchannels)
        else:
            # Reading from a file via wave module
            self._open_wavefile(self.fname)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if self.fname is None:
            # Terminate the sox subprocess
            self.soxproc.kill()
            self.soxproc.wait()
        else:
            # Close the wave file reader
            self.wavefile.close()

    def _open_wavefile(self, fname):
        self.wavefile = wave.open(fname, 'rb')

        self.framerate = self.wavefile.getframerate()
        self.sampwidth = self.wavefile.getsampwidth()
        self.nchannels = self.wavefile.getnchannels()

        self.scb = self._wave_file_scb(self.wavefile)

    def _open_device(self, framerate = 44100, sampwidth = 1, nchannels = 1):
        cmd = ['rec', '-q', '-r', str(framerate), '-c', str(nchannels),
               '-b', str(sampwidth * 8), '-t', 'raw', '-',
               'gain', str(self.gain)]
        self.soxproc = subprocess.Popen(cmd, stdout = subprocess.PIPE,
                                        text = False)

        self.soxbufrdr = io.BufferedReader(self.soxproc.stdout)

        self.framerate = framerate
        self.sampwidth = sampwidth
        self.nchannels = nchannels

        self.scb = self._sox_rec_scb(self.soxbufrdr)

    def _wave_file_scb(self, wf):
        """
        Sign Change Bit stream for a wave file
        """
        previous = 0
        chunk = int(self.framerate / 10)
        chunk = int(self.framerate * 60)
        while True:
            # Read the file in chunks of 100ms
            frames = wf.readframes(chunk)
            if not frames:
                break

            # Extract the most significant bytes of the leftmost channel
            msbytes = bytearray(frames[self.sampwidth - 1::
                                       self.sampwidth * self.nchannels])
            
            # Emit a stream of sign-change bits
            for byte in msbytes:
                signbit = byte & 0x80
                yield 1 if (signbit ^ previous) else 0
                previous = signbit

    def _sox_rec_scb(self, dev):
        """
        Sign Change Bit stream reading from audio device
        """
        previous = 0
        chunk = int(self.framerate * self.sampwidth * self.nchannels / 10)

        while True:
            # Read the file in chunks of 100ms
            frames = dev.read(chunk)
            if not frames:
                break

            # Extract the most significant bytes of the leftmost channel
            msbytes = bytearray(frames[self.sampwidth - 1::
                                       self.sampwidth * self.nchannels])
            
            # Emit a stram of sign-change bits
            for byte in msbytes:
                signbit = byte & 0x80
                yield 1 if (signbit ^ previous) else 0
                previous = signbit

    def wait_for_lead_in(self):
        """
        Wait for a steady BASE_FREQ tone half a second long
        """
        # Fill a deque buffer with half a second worth of audio frames
        sample = deque(maxlen = int(self.framerate / 2))
        sample.extend(islice(self.scb, int(self.framerate / 2 - 1)))

        # We use a for loop to detect EOF on the scb generator
        for val in self.scb:
            # Check if we have an acceptable tone (doesn't have to be perfect)
            sample.append(val)
            if abs(sum(sample) - self.base_freq) < 100:
                return True
            # Shift 200ms into the end of the buffer to no read every
            # single scb bit.
            sample.extend(islice(self.scb, int(self.framerate / 5 - 1)))

        # Oops
        return False

    def generate_bytes(self):
        """
        Generate a sequence of data bytes by sampling the current
        sign change bit stream
        """
        scb = self.scb
        framerate = self.framerate

        if self.parity is None:
            bitmasks = [0x1,0x2,0x4,0x8,0x10,0x20,0x40,0x80]
        else:
            bitmasks = [0x1,0x2,0x4,0x8,0x10,0x20,0x40,0x80,0]

        # Compute the number of audio frames used to encode a single data bit
        frames_per_bit = int(round(float(framerate) * 8 / self.base_freq))

        # Queue of sampled sign bits
        sample = deque(maxlen = frames_per_bit)     

        # Fill the sample buffer with an initial set of data
        sample.extend(islice(scb, frames_per_bit - 1))
        sign_changes = sum(sample)

        # Look for the start bit
        for val in scb:
            if val:
                sign_changes += 1
            if sample.popleft():
                sign_changes -= 1
            sample.append(val)

            # If a start bit detected, sample the next 8 data bits
            if sample[0] == 1 and sign_changes <= 9:
                byteval = 0
                nbits = 0
                for mask in bitmasks:
                    if sum(islice(scb, frames_per_bit)) >= 12:
                        byteval |= mask
                        nbits += 1
                    if mask == 0:
                        if nbits % 2 != self.parity:
                            raise Exception("parity error")
                # Skip the final two stop bits and refill the sample buffer 
                sample.extend(islice(scb, 2 * frames_per_bit, 3 * frames_per_bit - 1))
                sign_changes = sum(sample)
                yield byteval


class KCSWriter:
    """
    KCSWriter

    Class to encode bytes into Kansas City Standard audio. If a filename
    is provided, the file will be a .WAV and will be used as the audio
    target. Otherwise the sox(1) program is used to write directly to
    the default audio device.
    """
    def __init__(self, fname = None, rate = 48000, channels = 1, bits = 8,
                 base_freq = KCS_BASE_FREQ, parity = None, volume = 1.0):
        self.fname = fname
        self.framerate = rate
        self.sampwidth = bits
        self.nchannels = channels
        self.base_freq = base_freq
        self.parity    = parity
        self.volume    = volume

        # create square wave patterns for zero and one bits. fphw is the
        # number of frames per half wave. 
        fphw = int(rate / base_freq / 2)
        self.zero = ([0xff] * fphw * 2 + [0x00] * fphw * 2) * 4
        self.one  = ([0xff] * fphw + [0x00] * fphw) * 8

        # Open the audio output
        if fname is None:
            self._open_device()
        else:
            self._open_wavefile(fname)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        if self.fname is None:
            # Terminate the sox subprocess
            self.soxproc.stdin.close()
            self.soxproc.wait()
        else:
            # Close the wave file reader
            self.wavefile.close()

    def _open_wavefile(self, fname):
        self.wavefile = wave.open(fname, 'wb')

        self.wavefile.setframerate(self.framerate)
        self.wavefile.setsampwidth(int(self.sampwidth / 8))
        self.wavefile.setnchannels(self.nchannels)

        self._write = self.wavefile.writeframes

    def _open_device(self):
        # Launch sox's play(1) command to write to the sound card
        # By default we use 48000 Hz mono 8-bit unsigned PCM
        cmd = ['play', '-q', '-r', str(self.framerate), '-e', 'unsigned',
               '-c', str(self.nchannels), '-b', str(self.sampwidth),
               '-t', 'raw', '-v', str(self.volume), '-']
        self.soxproc = subprocess.Popen(cmd, stdin = subprocess.PIPE,
                                        text = False)

        # Create a BufferedWriter over stdin to write binary data
        self._write = io.BufferedWriter(self.soxproc.stdin).write

    def write_lead_in(self, secs = 3.0):
        # The KCS lead-in is a continuous tone of the base frequency
        # for the specified length. We can easily generate that by
        # using one bits.
        numwaves = int(self.framerate / len(self.one) * secs)
        self._write(bytes(self.one * numwaves))   

    def write_bytes(self, data):
        if self.parity is None:
            bitmasks = [0x1,0x2,0x4,0x8,0x10,0x20,0x40,0x80]
        else:
            bitmasks = [0x1,0x2,0x4,0x8,0x10,0x20,0x40,0x80,0]

        # Generate audio data one byte at a time
        frames = deque()
        for byte in data:
            # Generate the start bit
            frames.extend(self.zero)
            
            nbits = 0
            for mask in bitmasks:
                if mask != 0:
                    # Add the data bits and count the ones
                    if byte & mask:
                        frames.extend(self.one)
                        nbits += 1
                    else:
                        frames.extend(self.zero)
                else:
                    # Add a parity bit
                    if nbits % 2 != self.parity:
                        frames.extend(self.one)
                    else:
                        frames.extend(self.zero)
            # Add two stop bits
            frames.extend(self.one)
            frames.extend(self.one)

            # Write the audio data out and reset the frames buffer
            self._write(bytes(frames))
            frames.clear()
