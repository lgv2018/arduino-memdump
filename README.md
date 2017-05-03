# arduino-memdump
dump arduino memory using avrdude and perform analysis on it

## Introduction

This is a Python 3 script that uses avrdude to dump the memory of an Arduino. It can also disassemble the flash memory to assembly code, but `avr-objdump` must be installed for this to work. Currently its analysis capabilities are limited and it has only been tested with an Arduino Uno. This is somewhat of a toy project, so don't expect to be doing anything amazing with this any time soon.

## Documentation

Run `python3 arduino-memdump.py -h` to view the help message.

### Required arguments

`-m/--mcu` is a required argument that is passed directly to avrdude. It describes the type of the microcontroller connected to the programmer. For example, an Arduino Uno has a type of `m328p`.

`-p/--port` is a required argument that describes the port that the Arduino is connected to. For example, when an Arduino Uno is connected to a computer using the USB cable on `/dev/ttyUSB0`, you would run the script specifying `-p /dev/ttyUSB0`.

`--prog` is also passed directly to avrdude; it is the type of programmer used to program the board. Currently only `arduino` has been tested, and this option defaults to that as well.

`-d/--dir` specifies where the memory should be dumped to. If unspecified, the script dumps it to the current working directory.

`--asm` specifies the file that the disassembled flash memory should be written to. If this argument is not specified, it defaults to `disas.s`.

## Example
![Example of running arduino-memdump.py](docs/images/capture.gif?raw=true)
