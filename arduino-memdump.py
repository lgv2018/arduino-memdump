#!/usr/bin/python3

import argparse
import binascii
import os
import random
import shutil
import string
import struct
import subprocess
import sys
import tempfile

# list of possible memory types supported by avrdude
memtypes = ['eeprom', 'efuse', 'flash', 'fuse', 'hfuse', 'lfuse', 'lock',
        'signature', 'application', 'apptable', 'boot', 'prodsig', 'usersig']

class ArduinoProfile:
    def __init__(self, mcu, port, programmer):
        # name of the microcontroller e.g. Arduino Uno would use "m328p"
        self.mcu = mcu
        # name of the memory types that are supported
        self.memtypes = memtypes
        # the port that the arduino is connected to, e.g. /dev/ttyUSB0
        self.port = port
        # the programmer used to program the arduino, e.g. arduino, stk500v2
        self.programmer = programmer

def dump(args, profile):
    os.chdir(args.dir)
    print('Dumping supported memtypes using avrdude...')

    if shutil.which('avrdude') == None:
        print('Error! avrdude not found on your system!')
        sys.exit(1)

    for mt in profile.memtypes:
        # dump that memtype to a file
        try:
            subprocess.run(
                ['avrdude', '-p', profile.mcu, '-c', profile.programmer, '-P', profile.port, '-U', '{0}:r:{0}.bin:r'.format(mt)],
                shell=False,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError:
            profile.memtypes.remove(mt)

    # also run avrdude for fuseN memtypes, i.e. 'fuse' followed by
    # an integer, but stop once one is found to not be supported
    N = 0
    while True:
        try:
            mt = 'fuse{0}'.format(N)
            ret = subprocess.run(
                ['avrdude', '-p', profile.mcu, '-c', profile.programmer, \
                    '-P', profile.port, '-U', \
                    '{0}:r:{0}.bin:r'.format(mt) \
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT
            )

            # if no errors, add the memtype to the list of dumpables
            if ret.check_returncode() == 0:
                profile.memtypes.append(mt)
            N += 1
        except subprocess.CalledProcessError:
            # not sure whether fuse0 exists or if the integers start
            # at fuse1, so always check both fuse0 and fuse1
            if N >= 1:
                break
            else:
                N += 1
                continue

def analyze(args, profile):
    dump(args, profile)

    # read the .bin files that were dumped in the current directory
    mems = dict()
    for mt in profile.memtypes:
        fname = mt + '.bin'
        try:
            f = open(fname, 'rb')
            mems[mt] = f.read()
            f.flush()
            f.close()
        except OSError as e:
            # sometimes the avrdude subprocess doesn't raise a
            # CalledProcessError even when the memtype doesn't exist, so
            # remove it if no file was created for that memtype
            profile.memtypes.remove(mt)

    # show successfully dumped memtypes
    mts = ''
    for mt in profile.memtypes:
        mts += mt + ', '
    print('Successfully dumped {0}\n'.format(mts[:-2]))

    # print useful information about the memory dumped

    # see if avr-objdump exists
    print('Using avr-objdump to disassemble flash memory...')
    if shutil.which('avr-objdump') != None:
        # try to disassemble the flash memory using avr-objdump
        out = subprocess.check_output(
            ['avr-objdump', '-b', 'binary', '-m', 'avr', '-D', 'flash.bin'])
        f = open(args.asm, 'wb')
        f.write(out)
    else:
        print('Error! avr-objdump not found on your system!')

    # device signature
    if 'signature' in mems.keys():
        hex_sig = binascii.hexlify(mems['signature'])
        print('Device signature: {0}'.format(hex_sig))

    # analyze fuses

def main():
    # create top level parser
    parser = argparse.ArgumentParser()

    # required arg: the type of the microcontroller e.g. 'm328p' for an uno
    parser.add_argument('-m', '--mcu', required=True,
            help='the type of microcontroller; see avrdude\'s man page for examples')
    # port that the arduino is connected to via USB
    parser.add_argument('-p', '--port', required=True,
            help='the port the Arduino is connected to, e.g. /dev/ttyUSB0')
    # programmer used to program the board
    parser.add_argument('--prog', default='arduino',
            help='the programmer used to program the board; currently only \'arduino\' is tested, and defaults to that as well')
    # directory to dump the memory into (must exist)
    parser.add_argument('-d', '--dir', default='./',
            help='the directory to dump the memory into (must exist); defaults to the current working directory')
    # dump the code to this file
    parser.add_argument('--asm', default='./disas.s',
            help='the file to dump the disassembled flash memory to')

    # parse arguments
    args = parser.parse_args()
    profile = ArduinoProfile(
        mcu=args.mcu,
        port=args.port,
        programmer=args.prog
    )

    analyze(args, profile)

if __name__ == '__main__':
    main()

