=========================
Introduction
=========================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

What is videobatch?
====================

:py:mod:`videobatch` is a Python module that enables a frame-by-frame conversion
of videos in batches (i.e. more than one video with single command execution).

Originally, :py:mod:`videobatch` was intended for a Python-equivalent of the
`Pixylator (ImageJ plugin) <https://github.com/gwappa/Pixylator>`_ that
can be executed in batches.
However, as I added different functionality such as projection or profiling,
now the module has evolved as a general toolkit for batch-executing frame-by-frame
commands.

Basic functionality
===================

* :py:mod:`videobatch` is a command-line Python script that works from your terminal emulator.
* :py:mod:`videobatch` takes number of files as input. These input files are processed/output separately.
* a frame-by-frame conversion is applied to each of the video files.

