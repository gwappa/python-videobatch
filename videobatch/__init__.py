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

### imsave is deprecated as of scipy 1.1.0
from imageio import imread as _imread
from imageio import imwrite as _imsave

try:
    ucls = unicode # test if name 'unicode' exists
except NameError:
    unicode = str

with _warnings.catch_warnings(record=True):
    _warnings.filterwarnings("ignore", message="avprobe", category=UserWarning)
    import skvideo.io as _vio

OUTPUT_SPECS = {"-c:v": "libx264", "-preset": "slow", "-crf": "26"}

PROFILE_TIME = False

VERSION_STR = "1.0.0"

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

def set_profile_time(val):
    global PROFILE_TIME
    PROFILE_TIME = val

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
    if (parent != d) and (len(parent) > 0): # is parent not the drive root?
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
    """this is the superclass of every batch functions. DO NOT USE THIS AS A COMMAND!

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
    
    (parameters)
    <- 'type': one of ("max", "mean", "avg", "scale", "magenta_scale"). 'max' by default.
    <- 'outdir': the directory where the output file(s) will go. defaults to the current directory.
    """
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

class ColorMask(object):
    """a representation of a mask for Pixylation."""
    onset = -1
    offset = -1
    color = None

    def __init__(self, onset, offset):
        self.onset = onset
        self.offset = offset
        self.color = (_np.array(_hsv((self.onset + self.offset)/720)[:-1], dtype=float)*255).round().astype(int)

    def __repr__(self):
        return "ColorMask({0},{1})".format(self.onset, self.offset)

    def apply(self, hues):
        return _np.logical_and(hues >= self.onset, hues < self.offset)

class ROI(object):
    """a base representation of a ROI for Pixylation."""
    xpos = _np.array((), dtype=int)
    ypos = _np.array((), dtype=int)

    def __new__(cls, specs):
        if isinstance(specs, (str, unicode)): # TODO: or path-like??
            roi = super(ROI,cls).__new__(MaskROI)
            return roi
        else: # assume dict
            roi = super(ROI,cls).__new__(RectangularROI)
            return roi

    def __init__(self):
        pass

    def is_empty(self):
        return self.xpos.size == 0

    def crop(self, frame):
        """returns cropped pixels as a (N,3) array"""
        return frame[self.ypos,self.xpos]

    def mark(self, frame, mask, value):
        """marks the `mask`-ed pixels within this ROI in the `frame` to `value`"""
        frame[self.ypos[mask], self.xpos[mask]] = value

class RectangularROI(ROI):
    """a representation of a rectangular ROI for Pixylation."""
    x = 0
    y = 0
    w = 1
    h = 1

    def __init__(self, specs):
        super().__init__()
        self.x = specs.get('x',0)
        self.y = specs.get('y',0)
        self.w = specs.get('w',1)
        self.h = specs.get('h',1)
        xvals = _np.arange(self.x, self.x + self.w)
        yvals = _np.arange(self.y, self.y + self.h)
        xvals, yvals = _np.meshgrid(xvals, yvals, indexing='xy')
        self.xpos  = xvals.flatten()
        self.ypos  = yvals.flatten()
        print(self.xpos)

    def __repr__(self):
        return "RectangularROI(dict(x={0},y={1},w={2},h={3}))".format(self.x, self.y, self.w, self.h)

class MaskROI(ROI):
    """a representation of a Mask-based ROI specification
    loadable from a B/W image file."""
    path = None

    def __init__(self, specs):
        super().__init__()
        self.path = specs
        mask = _imread(specs).astype(bool)
        self.ypos, self.xpos = _np.where(mask)

    def __repr__(self):
        return "MaskROI('{}')".format(self.path)

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


def frame_as_HL(frame):
    """returns the hue and lightness values for a (M,N,3) frame"""
    return _Htable[frame[:,:,0],frame[:,:,1],frame[:,:,2]], _Ltable[frame[:,:,0], frame[:,:,1], frame[:,:,2]]

def vector_as_HL(vec):
    """returns the hue and lightness values for a (N,3) vector of values"""
    return _Htable[vec[:,0],vec[:,1],vec[:,2]], _Ltable[vec[:,0],vec[:,1],vec[:,2]]

def _mask_entries(maskname):
    return "{0}_CM_X,{0}_CM_Y".format(maskname)

@command("pixylation")
class Pixylation(AbstractBatch):
    """runs 'Pixylator' with multiple masks/ROIs, and saves mask/result files.
    
    (parameters)
    <- 'mode': the method for converting matched pixels into a position. only has the "CM" mode for the moment.
    <- 'colors': a dictionary where keys represent the names of colors and the values represent their color ranges.
                 a color range is specified as [<from-hue>, <to-hue>].
    <- 'ROIs': a dictionary where keys represent the names of ROIs and the values represent their regions.
               a rectangular region can be specified as a dictionary {"x":..., "y":..., "w":..., "h":...}.
               a free-shape region can be specified as a path to a B/W image (white pixels will be taken).
    <- 'maskdir': the directory where the mask file(s) will go. defaults to the current directory.
    <- 'resultdir': the directory where the result file(s) will go. defaults to the current directory.
    """

    masks = {}
    ROIs  = {}
    mode      = None
    maskdir   = None
    resultdir = None

    _maskfiles = {}
    _masknames = []
    _resultfiles = {}

    def __init__(self, *src, **config):
        super(Pixylation, self).__init__(*src, **config)
        self.mode = config.get("mode", "CM") # currently CM only
        self.maskdir = config.get("maskdir", None)
        if string_is_empty(self.maskdir):
            self.maskdir = _os.getcwd()
        self.resultdir = config.get("resultdir", None)
        if string_is_empty(self.resultdir):
            self.resultdir = _os.getcwd()

        self.masks = dict([(k, ColorMask(*v)) for k, v in get_items(config.get("colors", {}))])
        self.ROIs  = dict([(k, ROI(v)) for k, v in get_items(config.get("ROIs", {}))])
        print("{0}".format(self))
        if len(self.masks) == 0:
            raise RuntimeError("No color masks found in the configuration; make sure that you have the 'colors' field in it.")
        if len(self.ROIs) == 0:
            raise RuntimeError("No ROI settings found in the configuration; make sure that you have the 'ROIs' field in it.")
        _initialize_tables()

    def __repr__(self):
        info = ["<< Pixylation >>", "[Colors]"]
        for k, v in self.masks.items():
            info.append("{0}={1}".format(k, v))
        info.append("[ROIs]")
        for k, v in self.ROIs.items():
            info.append("{0}={1}".format(k, v))
        return '\n'.join(info)

    def __start__(self, name):
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

        # maskpath = _os.path.join(self.maskdir, "MASK_{0}.avi".format(basename, roiname))
        maskpath = _os.path.join(self.maskdir, "MASK_{0}.mp4".format(basename, roiname))
        try:
            self._maskfile = _vio.FFmpegWriter(maskpath, outputdict=OUTPUT_SPECS)
        except:
            _print_exc()
            print_status("*** could not open: {0}".format(maskpath))

    def __update__(self, i, frame):
        M = _np.zeros(frame.shape, dtype=int)
        for roiname, roi in get_items(self.ROIs):
            if roiname not in self._resultfiles.keys():
                continue
            values = [] # placeholder for positions for each of the masks

            # prepare clipped xpos, ypos, H, L that corresponds to the ROI
            roi_H, roi_L = vector_as_HL(roi.crop(frame))
            
            # check for color masks
            for maskname, colormask in get_items(self.masks):
                roi_match = colormask.apply(roi_H)
                if _np.count_nonzero(roi_match) > 0:
                    match_weight = roi_L[roi_match]
                    match_x = roi.xpos[roi_match]
                    match_y = roi.ypos[roi_match]
                    xrepr = (match_x*match_weight).sum()/(match_weight.sum())
                    yrepr = (match_y*match_weight).sum()/(match_weight.sum())
                    values.append(xrepr+1)
                    values.append(yrepr+1)
                    roi.mark(M,roi_match,colormask.color)
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

from collections import OrderedDict

def get_value(roi, frame):
    """add-on method for getting the value of ROI in the frame"""
    return frame[(roi.x):(roi.x + roi.w), (roi.y):(roi.y + roi.h), :].mean()

@command("profile")
class Profile(AbstractBatch):
    """generates a Z-profile of specified ROI(s).
    
    (parameters)
    <- 'ROIs': a dictionary where keys represent the names of ROIs and the values represent their regions.
               a rectangular region can be specified as a dictionary {"x":..., "y":..., "w":..., "h":...}.
               a free-shape region can be specified as a path to a B/W image (white pixels will be taken).
    <- outdir: the directory where the result file(s) will go. defaults to the current directory.
    """

    ROIs        = OrderedDict()
    resultdir   = None

    def __init__(self, *src, **config):
        self.resultdir = config.get("outdir", None)
        if string_is_empty(self.resultdir):
            self.resultdir = _os.getcwd()
        self.ROIs = dict([(k, ROI(v)) for k, v in get_items(config.get("ROIs", {}))])
        print("{0}".format(self))
        if len(self.ROIS) == 0:
            raise RuntimeError("No ROI settings found in the configuration; make sure that you have the 'ROIs' field in it.")

    def __repr__(self):
        info = ["<< Profile >>"]
        for k, v in self.ROIs.items():
            info.append("{0}={1}".format(k,v))
        return "\n".join(info)

    def __start__(self, name):
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
    print()
    print("[base parameters]")
    print("the JSON file must consist of a dictionary that contains the following keys and values: ")
    
    for param, desc in (("command", "(required) the command to run. see below for details."),
                        ("sources", "(required) list or pattern(s) of file names to perform conversion."),
                        ("sourcedir", "(optional) the directory where the program searches for the video. defaults to the current directory."),
                        ):
        print("{0:>15}: {1}".format("'{}'".format(param), desc))
    print()
    print("[commands]")
    for key, val in get_items(commands):
        desc = "{0:>15}: {1}".format(key, val.__doc__)
        lines = desc.split("\n")
        print(lines[0])
        for line in lines[2:]:
            print(" "*13+line)

def run(config):
    if isinstance(config, (str, unicode)):
        with open(config, 'r') as fp:
            config = _json.load(fp)
            run(config)
            return
    cmd = config.get("command", None)
    src = config.get("sources", [])
    if isinstance(src, (str, unicode)):
        src = [src,]
    if cmd is None:
        raise ValueError("specify the command in the config file, using the 'command' key.")
    proc = commands[cmd](*src, **config)
    if PROFILE_TIME == True:
        import time
        print(">> timing starting")
        start = time.perf_counter()
    proc.run()
    if PROFILE_TIME == True:
        print(">> timing stopping")
        stop  = time.perf_counter()
        print("elapsed {:.3f} seconds".format(stop - start))

