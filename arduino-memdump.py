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
                    # not sure whether fuse0 exists or if the integers start
                    # at fuse1, so always check both fuse0 and fuse1
                    if N >= 1:
                        break
                    else:
                        N += 1
                        continue

        # return list of supported memtypes
        return dumpable

def dump(args):
    # save the working directory
    pwd = os.getcwd()

    a = ArduinoProfile(
        mcu='m328p',
        memtypes=['eeprom', 'efuse'],
        port=args.port,
        programmer='arduino'
    )
    print('Checking for supported memtypes...')
    mts = a.find_memtypes()

    # change back to the previous working directory before dumping the memory
    os.chdir(pwd)

    for mt in mts:
        print('dumping {0}...'.format(mt))
        # dump that memtype to a file
        subprocess.run(
            ['avrdude', '-p', a.mcu, '-c', a.programmer, '-P', a.port, '-U', '{0}:r:{0}.bin:r'.format(mt)],
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )

def main():
    # create top level parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # global arguments

    # mode: dump
    parser_dump = subparsers.add_parser('dump', help='dumps the mcu\'s memory to files based on memory type')
    # run the dump function
    parser_dump.set_defaults(function=dump)

    # port that the arduino is connected to via USB
    parser_dump.add_argument('-p', '--port',
            help='the port the Arduino is connected to, e.g. /dev/ttyUSB0',
            required=True)

    # mode: analyze

    args = parser.parse_args()
    # run the function associated with the mode
    args.function(args)

if __name__ == '__main__':
    main()

