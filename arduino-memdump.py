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

class ArduinoProfile:
    def __init__(self, mcu, port, programmer):
        # name of the microcontroller e.g. Arduino Uno would use "m328p"
        self.mcu = mcu
        # name of the memory types that are supported
        self.memtypes = ['eeprom', 'efuse', 'flash', 'fuse', 'hfuse', 'lfuse',
        'lock', 'signature', 'application', 'apptable', 'boot', 'prodsig',
        'usersig', 'fuse0', 'fuse1', 'fuse2', 'fuse3', 'fuse4', 'fuse5',
        'fuse6', 'fuse7']
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
        subprocess.run(
            ['avrdude', '-p', profile.mcu, '-c', profile.programmer, '-P', profile.port, '-U', '{0}:r:{0}.bin:r'.format(mt)],
            shell=False,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )

def analyze(args, profile):
    dump(args, profile)

    # read the .bin files that were dumped in the current directory
    mems = dict()
    to_remove = []
    for mt in profile.memtypes:
        fname = mt + '.bin'
        try:
            f = open(fname, 'rb')
            mems[mt] = f.read()
            f.flush()
            f.close()
        except OSError as e:
            # remove mt if no file was created for that memtype
            to_remove.append(mt)

    # remove memtypes that have no file associated with them
    for t in to_remove:
        profile.memtypes.remove(t)

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
        print('Wrote assembly to {0}'.format(os.getcwd() + '/' + args.asm))
    else:
        print('Error! avr-objdump not found on your system!')

    # device signature
    if 'signature' in mems.keys():
        hex_sig = '0x' + binascii.hexlify(mems['signature']).decode('ascii')
        print('Device signature: {0}'.format(hex_sig))

    # print fuses
    if 'lfuse' in mems.keys():
    	lfuse_hex = '0x' + binascii.hexlify(mems['lfuse']).decode('ascii')
    	lfuse_bin = bin(int(lfuse_hex, 16))
    	print('fuse low byte: {0} ({1})'.format(lfuse_hex, lfuse_bin))
    if 'efuse' in mems.keys():
    	efuse_hex = '0x' + binascii.hexlify(mems['efuse']).decode('ascii')
    	efuse_bin = bin(int(efuse_hex, 16))
    	print('fuse extended byte: {0} ({1})'.format(efuse_hex, efuse_bin))

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
    parser.add_argument('--asm', default='disas.s',
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

