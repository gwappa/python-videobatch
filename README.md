# Python `videobatch` module

This module was intended for a Python-equivalent of
the [Pixylator (ImageJ plugin)](https://github.com/gwappa/Pixylator).
In fact, now the module is generalized to be used as a toolkit
to perform any types of conversion of videos frame-by-frame.

The current version is `0.9.1`.

Note that I do not provide any test code here! This is just
out of my laziness...
Please poke me in case of any weird behavior of the code!

## Functionality

+ Can take number of files as input (processed/output separately).
+ Frame-by-frame conversion is applied (see below for commands) to
  each of the video files.

## Commands

+ `projection`: equivalent to ImageJ's "Z-projection" command.
+ `pixylation`: equivalent to the "Pixylator" plugin.

## Installation

```
pip install git+https://github.com/gwappa/python-videobatch.git
```

## License

The MIT License

