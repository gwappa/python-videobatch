# Python `videobatch` module

This module was intended for a Python-equivalent of
the [Pixylator (ImageJ plugin)](https://github.com/gwappa/Pixylator).
In fact, now that the module becomes a more general toolkit,
you can in principle perform any types of frame-by-frame conversion of videos.

The current version is `1.0`.

Note that I do not provide any test code here! This is just
out of my laziness...
Please poke me in case of any weird behavior of the code!

## Documentation

Rough documentation is [here](https://python-videobatch.readthedocs.io/en/latest/).

## Functionality

+ Can take number of files as input (processed/output separately).
+ Frame-by-frame conversion is applied (see below for commands) to
  each of the video files.

## Commands

+ `projection`: equivalent to ImageJ's "Z-projection" command.
+ `profile`:    equivalent to ImageJ's "Z-profile" command.
+ `pixylation`: equivalent to the "Pixylator" plugin.

## Installation

### python libraries (including `videobatch`)

`videobatch` requires `numpy`, `scipy`, `matplotlib` (weirdly enough)
and `scikit-video`.

They will be automatically installed with `videobatch`
if you use the `pip` command:

```
pip install git+https://github.com/gwappa/python-videobatch.git
```

### FFmpeg

The following `scikit-video` library uses `ffmpeg`-related commands
to read/write videos.
What you need to do before running `videobatch` is:

1. Install [ffmpeg](https://ffmpeg.org/); make sure that you install
sub-commands, particularly `ffprobe`.
   + For Macs and Linux computers, it may be easier that you install
     through a package manager such as `apt` or `Homebrew`.
2. Make sure that your terminal emulator can find `ffprobe`
   by modifying the environment variables, if necessary.

Actually, `ffprobe` is the command that `scikit-video` uses to 
find out the actual `ffmpeg` binary to use.


## Known issues

It looks like my use of `FFmpegWriter` is inappropriate for some
video players (incl. QuickTime Player on the Mac).
If you encounter this problem, try using [VLC](http://www.videolan.org/vlc/).
Note that I don't plan to fix this issue for the time being!

## License

The MIT License

