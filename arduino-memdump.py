#!/usr/bin/python3

import argparse, os, random, string, subprocess, sys, tempfile

# list of possible memory types supported by avrdude
memtypes = ['eeprom', 'efuse', 'flash', 'fuse', 'hfuse', 'lfuse', 'lock',
        'signature', 'application', 'apptable', 'boot', 'prodsig', 'usersig']

class ArduinoProfile:
    def __init__(self, mcu, memtypes, port, programmer):
        # name of the microcontroller e.g. Arduino Uno would use "m328p"
        self.mcu = mcu
        # name of the memory types the user wants to dump
        self.memtypes = memtypes
        # the port that the arduino is connected to, e.g. /dev/ttyUSB0
        self.port = port
        # the programmer used to program the arduino, e.g. arduino, stk500v2
        self.programmer = programmer

    def find_memtypes(self):
        '''Use avrdude to try to dump the memory of all memory types supported
        by the MCU'''

        # avrdude needs to dump memory to a file, so create a temporary
        # directory
        dumpable = memtypes
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)

            # run avrdude for each memtype
            for mt in memtypes:
                try:
                    subprocess.run(
                        ['avrdude', '-p', self.mcu, '-c', self.programmer, \
                            '-P', self.port, '-U', \
                            '{0}:r:{0}.bin:r'.format(mt) \
                        ],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.STDOUT
                    )
                except subprocess.CalledProcessError:
                    dumpable.remove(mt)

            # also run avrdude for fuseN memtypes, i.e. 'fuse' followed by
            # an integer, but stop once one is found to not be supported
            N = 0
            while True:
                try:
                    mt = 'fuse{0}'.format(N)
                    ret = subprocess.run(
                        ['avrdude', '-p', self.mcu, '-c', self.programmer, \
                            '-P', self.port, '-U', \
                            '{0}:r:{0}.bin:r'.format(mt) \
                        ],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.STDOUT
                    )

                    # if no errors, add the memtype to the list of dumpables
                    if ret.check_returncode() == 0:
                        dumpable.append(mt)
                    N += 1
                except subprocess.CalledProcessError:
                    break

        # return list of supported memtypes
        return dumpable

def main():
    # create top level parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # option: strings
    parser_strings = subparsers.add_parser('strings', help='find ASCII strings')

    # option: dump

    args = parser.parse_args()

if __name__ == '__main__':
    # main()
    a = ArduinoProfile(
            mcu='m328p',
            memtypes=['eeprom', 'efuse'],
            port='/dev/ttyUSB0',
            programmer='arduino'
    )
    mts = a.find_memtypes()
    for mt in mts:
        print('{0} is supported'.format(mt))

