# 
# MIT License
# 
# Copyright (c) 2018 Keisuke Sehara
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from __future__ import print_function, division
import sys as _sys
import os as _os
from glob import glob as _glob
import json as _json
from traceback import print_exc as _print_exc
import warnings as _warnings

import numpy as _np
from matplotlib.cm import hsv as _hsv

### TODO: imsave is deprecated as of scipy 1.1.0
### may need to branch the function to use imageio.imwrite
from scipy.misc import imsave as _imsave

try:
    ucls = unicode # test if name 'unicode' exists
except NameError:
    unicode = str

with _warnings.catch_warnings(record=True):
    _warnings.filterwarnings("ignore", message="avprobe", category=UserWarning)
    import skvideo.io as _vio

H264_OUTPUT = {"-c:v": "libx264", "-preset": "slow", "-crf": "26"}

commands = dict()

def command(name):
    """decorator function: registers given class as a batch command with ``name``."""
    def register(cls):
        """cls: an AbstractBatch subclass"""
        try:
            if not issubclass(cls, AbstractBatch):
                raise ValueError("*** the class registered with a command must be a subclass of AbstractBatch.")
        except NameError:
            # AbstractBatch itself
            pass
        if name in commands.keys():
            print("*** class '{0}' overriding the existing command '{1}'".format(cls.__name__, name))
        commands[name] = cls
        return cls
    return register

def string_is_empty(s):
    return (s is None) or (len(s.strip()) == 0)

def print_status(msg, out=_sys.stderr, end='\n', flush=True):
    out.write(msg)
    out.write(end)
    if flush == True:
        out.flush()

def get_items(d):
    return d.items()

def force_close(fp):
    try:
        fp.close()
    except:
        pass

def ensure_directory(d):
    parent, child = _os.path.split(d)
    if len(parent) > 0:
        ensure_directory(parent)
    d = _os.path.join(parent, child)
    if not _os.path.exists(d):
        _os.mkdir(d)

class Processor(object):
    """an abstraction of a single-file process."""
    proc = None
    path = None
    name = None
    reader = None
    procbycount = 100
    sepbycount = 1000

    def __init__(self, proc, path, procbycount=None, sepbycount=None):
        """proc be an AbstractBatch object; path be a path to the video file."""
        if proc is None:
            raise ValueError("no procedure is specified for Processor")
        elif path is None:
            raise ValueError("no file path is specified for Processor")
        self.proc = proc
        self.path = path
        self.name = _os.path.split(path)[1]
        if procbycount is not None:
            self.procbycount = int(procbycount)
        if sepbycount is not None:
            self.sepbycount = int(sepbycount)

    def __enter__(self):
        self.reader = _vio.FFmpegReader(self.path)
        self.proc.__start__(self.name)
        print_status("processing: {0}".format(self.name), end='', flush=True)
        return self

    def __iter__(self):
        for i, frame in enumerate(self.reader.nextFrame()):
            if (i>0) and (i % (self.sepbycount) == 0):
                print_status(' ', end='', flush=True)
            yield i, frame
            if (i+1) % (self.procbycount) == 0:
                print_status('.', end='', flush=True)
        print_status("done ({0}).".format(i+1), flush=True)

    def __exit__(self, exc, value, trace):
        try:
            self.proc.__done__(self.name, err=(exc is not None))
        except Exception as e:
            print_status("*** {0}".format(e))
            return False
        finally:
            force_close(self.reader)
        return (exc is None)

@command("test")
class AbstractBatch(object):
    """this is the superclass of every batch functions.

    to create a new batch function:
    1) derive from videobatch.AbstractBatch
    2) implement __init__, __start__, __update__ and __done__ as needed
    3) decorate the class with "@videobatch.command("<command-name>")"
    """
    sources = []
    sourcedir = None
    logging = {}

    def __init__(self, *src, **config):
        if len(src) == 0:
            raise ValueError("no source file specified")
        self.sources = src
        self.sourcedir = config.get("sourcedir", None)
        if string_is_empty(self.sourcedir):
            self.sourcedir = _os.getcwd()
        self.logging = config.get("logging", {})

    def _expandsources(self):
        for src in self.sources:
            pattern = _os.path.join(self.sourcedir, src)
            for path in _glob(pattern):
                yield path

    def run(self):
        for path in self._expandsources():
            with Processor(self, path, **(self.logging)) as reader:
                for i, frame in reader:
                    self.__update__(i, frame)

    def __start__(self, name):
        """subclass-specific implementation for movie-wise initialization procedures."""
        print_status("start('{0}')".format(name))

    def __update__(self, i, frame):
        """subclass-specific implementation for frame-wise updates."""
        print_status("update()")

    def __done__(self, name, err=False):
        """subclass-specific implementation for movie-wise finalization procedures."""
        print_status("done('{0}', err={1})".format(name, err))

@command("projection")
class Projection(AbstractBatch):
    """creates a t-projection image file.
    
    'type' is one of ("max", "mean", "avg", "scale", "magenta_scale"). 'max' by default."""
    outdir = None
    projtype = None
    _buffer = None
    _outname = None

    def __init__(self, *src, sourcedir=None, **config):
        super(Projection, self).__init__(*src, sourcedir=sourcedir)
        self.outdir = config.get("outdir", None)
        if string_is_empty(self.outdir):
            self.outdir = _os.getcwd()
        self.projtype = config.get("type", None)
        if string_is_empty(self.projtype):
            self.projtype = "max"

    def __start__(self, name):
        self._outname = "{0}.png".format(_os.path.splitext(name)[0])
        if self.projtype == "magenta_scale":
            self._blue  = None
            self._green = None
            self._red   = None
        else:
            self._buffer = None

    def __update__(self, i, frame):
        # TODO: check if it is the color image
        if self._buffer is None:
            if self.projtype in ("max",):
                self._buffer = frame.copy()
            elif self.projtype in ("mean", "avg", "scale"):
                self._buffer = frame.astype(float)
            elif self.projtype == "magenta_scale":
                self._buffer = frame.copy()
                self._blue   = frame[:,:,2].copy()
                self._green  = frame[:,:,1].astype(float).copy()
                self._red    = frame[:,:,0].astype(float).copy()
        else:
            if self.projtype in ("mean", "avg", "scale"):
                self._buffer += frame.astype(float)
                self._nframe  = i
            elif self.projtype == "magenta_scale":
                self._red   += frame[:,:,0]
                self._green += frame[:,:,1]
                self._blue   = _np.nanmax([frame[:,:,2], self._blue], axis=0)
            else:
                self._buffer = _np.nanmax([frame, self._buffer], axis=0)

    def __done__(self, name, err=False):
        ensure_directory(self.outdir)
        path = _os.path.join(self.outdir, self._outname)
        if self.projtype in ("mean", "avg"):
            self._buffer = (self._buffer/(self._nframe + 1)).astype(_np.uint8) 
        elif self.projtype == "scale":
            self._buffer /= (self._buffer.max((0,1), keepdims=True))/255
            self._buffer  = self._buffer.astype(_np.uint8)
        elif self.projtype == "magenta_scale":
            self._red   /= self._red.max()
            self._green /= self._green.max() 
            self._buffer = _np.stack([(self._red*255).astype(_np.uint8), (self._green*255).astype(_np.uint8), self._blue], axis=-1)
            self._red    = None
            self._green  = None
            self._blue   = None
        _imsave(path, self._buffer)
        self._buffer = None
        print_status("-> {0}".format(path), flush=True)

class Mask(object):
    """a representation of a mask for Pixylation."""
    onset = -1
    offset = -1
    _color = None
    def __init__(self, onset, offset):
        self.onset = onset
        self.offset = offset

    def __repr__(self):
        return "Mask({0},{1})".format(self.onset, self.offset)

    def apply(self, hues):
        return _np.logical_and(hues >= self.onset, hues < self.offset)

    def as_color(self):
        """returns its representative color"""
        if self._color is None:
            self._color = (_np.array(_hsv((self.onset + self.offset)/720)[:-1], dtype=float)*255).round().astype(int)
        return self._color

class ROI(object):
    """a representation of a ROI for Pixylation."""
    x = 0
    y = 0
    w = 1
    h = 1
    def __init__(self, x=0, y=0, w=1, h=1):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def __repr__(self):
        return "ROI(x={0},y={1},w={2},h={3})".format(self.x, self.y, self.w, self.h)

    def is_empty(self):
        return ((self.w) * (self.h) <= 1)

    def apply(self, values):
        values[:self.y,:] = False
        values[(self.y+self.h):,:] = False
        values[:,:self.x] = False
        values[:,(self.x+self.w):] = False
        return values

_Htable = None
_Ltable = None
def _initialize_tables():
    global _Htable, _Ltable
    if _Htable is None:
        print_status("initializing the hue/luma tables...", end='', flush=True)
        _Htable = _np.empty((256, 256, 256), dtype=int)
        _values = _np.arange(256)
        _RGB = _np.empty((256,256,256,3), dtype=int)
        _RGB[:,:,:,0] = _values.reshape((-1,1,1)) # R
        _RGB[:,:,:,1] = _values.reshape((1,-1,1)) # G
        _RGB[:,:,:,2] = _values.reshape((1,1,-1)) # B
        M = _RGB.max(axis=3)
        m = _RGB.min(axis=3)
        D = M - m

        done = (D == 0);
        _Htable[done] = -1
        rng = _np.logical_and(m == _RGB[:,:,:,2], ~done)
        _Htable[rng] = _np.around(60*(1 + (_RGB[rng,1] - _RGB[rng,0])/(D[rng]) )).astype(int)
        done = _np.logical_or(rng, done)
        rng = _np.logical_and(m == _RGB[:,:,:,0], ~done)
        _Htable[rng] = _np.around(60*(3 + (_RGB[rng,2] - _RGB[rng,1])/(D[rng]) )).astype(int)
        done = _np.logical_or(rng, done)
        rng = ~done
        _Htable[rng] = _np.around(60*(5 + (_RGB[rng,0] - _RGB[rng,2])/(D[rng]) )).astype(int)

        _Ltable = (0.212*_RGB[:,:,:,0] + 0.701*_RGB[:,:,:,1] + 0.087*_RGB[:,:,:,2])/255
        print_status("done.", flush=True)


def as_HL(frame):
    """returns the hue and lightness values for a frame"""
    return _Htable[frame[:,:,0],frame[:,:,1],frame[:,:,2]], _Ltable[frame[:,:,0], frame[:,:,1], frame[:,:,2]]

def _mask_entries(maskname):
    return "{0}_CM_X,{0}_CM_Y".format(maskname)

@command("pixylation")
class Pixylation(AbstractBatch):
    """runs 'Pixylator' with multiple masks/ROIs, and saves mask/result files.
    currently CM-mode only"""
    masks = {}
    ROIs  = {}
    mode      = None
    maskdir   = None
    resultdir = None

    _maskfiles = {}
    _masknames = []
    _resultfiles = {}
    _xpos = None
    _ypos = None

    def __init__(self, *src, **config):
        super(Pixylation, self).__init__(*src, **config)
        self.mode = config.get("mode", "CM") # currently CM only
        self.maskdir = config.get("maskdir", None)
        if string_is_empty(self.maskdir):
            self.maskdir = _os.getcwd()
        self.resultdir = config.get("resultdir", None)
        if string_is_empty(self.resultdir):
            self.resultdir = _os.getcwd()

        self.masks = dict([(k, Mask(*v)) for k, v in get_items(config.get("masks", {}))])
        self.ROIs  = dict([(k, ROI(**v)) for k, v in get_items(config.get("ROIs", {}))])
        print("{0}".format(self))
        _initialize_tables()

    def __repr__(self):
        info = ["<< Pixylation >>", "[Masks]"]
        for k, v in self.masks.items():
            info.append("{0}={1}".format(k, v))
        info.append("[ROIs]")
        for k, v in self.ROIs.items():
            info.append("{0}={1}".format(k, v))
        return '\n'.join(info)

    def __start__(self, name):
        self._xpos = None
        self._ypos = None
        self._maskfile = None
        self._resultfiles = {}
        self._masknames = tuple(maskname for maskname in self.masks.keys())
        basename = _os.path.splitext(name)[0]
        ensure_directory(self.maskdir)
        ensure_directory(self.resultdir)

        for roiname, roi in get_items(self.ROIs):
            if roi.is_empty():
                continue
            resultpath = _os.path.join(self.resultdir, "Results_{0}_{1}.csv".format(basename, roiname))
            # TODO: create mask file
            try:
                self._resultfiles[roiname] = open(resultpath, 'w')
                self._resultfiles[roiname].write('Slice,'+','.join(_mask_entries(m) for m in self._masknames))
                self._resultfiles[roiname].write('\n')
            except:
                _print_exc()
                print_status("*** could not open: {0}".format(resultpath))
        if len(self._resultfiles) == 0:
            raise RuntimeError("nothing to output for {0}".format(name))

        maskpath = _os.path.join(self.maskdir, "MASK_{0}.avi".format(basename, roiname))
        try:
            self._maskfile = _vio.FFmpegWriter(maskpath, outputdict=H264_OUTPUT)
        except:
            _print_exc()
            print_status("*** could not open: {0}".format(maskpath))

    def __update__(self, i, frame):
        if self._xpos is None:
            h, w, _ = frame.shape
            x = _np.arange(1, w+1)
            y = _np.arange(1, h+1)
            self._xpos, self._ypos = _np.meshgrid(x, y, indexing='xy')
        H, L = as_HL(frame)
        M = _np.zeros(frame.shape, dtype=int)
        masked = dict((name, value.apply(H)) for name, value in get_items(self.masks))
        for roiname, roi in get_items(self.ROIs):
            values = []
            if roiname not in self._resultfiles.keys():
                continue
            for maskname in self._masknames:
                _match = roi.apply(masked[maskname].copy())
                if _np.count_nonzero(_match) > 0:
                    _weight = L[_match]
                    _x = self._xpos[_match]
                    _y = self._ypos[_match]
                    values.append((_x*_weight).sum()/(_weight.sum()))
                    values.append((_y*_weight).sum()/(_weight.sum()))

                    M[_match,:] = self.masks[maskname].as_color()
                else:
                    values.append(_np.nan)
                    values.append(_np.nan)
            self._resultfiles[roiname].write("{0},".format(i)+','.join("{0:.4f}".format(v) for v in values) + '\n')
        if self._maskfile is not None:
            self._maskfile.writeFrame(M)

    def __done__(self, name, err=False):
        for files in (dict(file=self._maskfile), self._resultfiles):
            for fp in files.values():
                force_close(fp)

### NOT TESTED -->

from collections import OrderedDict

def get_value(roi, frame):
    """add-on method for getting the value of ROI in the frame"""
    return frame[(roi.x):(roi.x + roi.w), (roi.y):(roi.y + roi.h), :].mean()

@command("profile")
class Profile(AbstractBatch):
    """generates a Z-profile of specified ROI(s)."""

    ROIs        = OrderedDict()
    resultdir   = None

    def __init__(self, *src, **config):
        self.resultdir = config.get("resultdir", None)
        if string_is_empty(self.resultdir):
            self.resultdir = _os.getcwd()
        self.ROIs = dict([(k, ROI(**v)) for k, v in get_items(config.get("ROIs", {}))])
        print("{0}".format(self))

    def __repr__(self):
        info = ["<< Profile >>"]
        for k, v in self.ROIs.items():
            info.append("{0}={1}".format(k,v))
        return "\n".join(info)

    def __start__(self, name):
        if len(self.ROIs) == 0:
            raise RuntimeError("nothing to output for {0}".format(name))

        self._resultfile = None
        basename = _os.path.splitext(name)[0]
        ensure_directory(self.resultdir)

        resultpath = _os.path.join(self.resultdir, "Profile_{}.csv".format(basename))
        try:
            self._resultfile = open(resultpath, 'w')
            self._resultfile.write('Slice,'+','.join(self.ROIs.keys()))
            self._resultfile.write('\n')
        except:
            _print_exc()
            raise RuntimeError("could not open: {0}".format(resultpath))

    def __update__(self, i, frame):
        self._resultfile.write("{0},".format(i)+','.join("{0:.4f}".format(v) for v in [get_value(roi, frame) for roi in get_items(self.ROIs)]) + '\n')

    def __done__(self, name, err=False):
        force_close(self._resultfile)

def print_usage():
    print("[usage]")
    print("    python {0} <path/to/config-file.json>".format(*(_sys.argv)))
    print("[commands]")
    for key, val in get_items(commands):
        print("{0:>15}: {1}".format(key, val.__doc__))

def run(config):
    if isinstance(config, (str, unicode)):
        with open(config, 'r') as fp:
            config = _json.load(fp)
            run(config)
            return
    cmd = config.get("command", None)
    src = config.get("sources", [])
    if cmd is None:
        raise ValueError("specify the command in the config file, using the 'command' key.")
    proc = commands[cmd](*src, **config)
    proc.run()

if __name__ == '__main__':
    if len(_sys.argv) == 2:
        run(_sys.argv[1])
    else:
        print_usage()
