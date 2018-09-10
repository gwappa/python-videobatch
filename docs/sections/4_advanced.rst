=========================
Advanced usages
=========================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Using a free-shape ROI
=======================

As of version 0.10, a free-shape ROI can be used for e.g. Pixylation.

First thing you need to do is to prepare a black-and-white image called a "mask file".
Here are what it has to satisfy:

1. A mask file must be of 8-bit or 16-bit grayscale.
2. The mask file has to have the same dimensions (width/height) as the video file that it is applied.
3. The pixel that are in the ROI must be in white, and otherwise in black.

.. note::

    In fact, all that videobatch does is to call :py:mod:`scipy` to open the image file,
    and then convert the data into a boolean 2D matrix.
    Therefore, the specification is not as strict as shown above in reality;
    if you know what you are doing, it is free to use any other types of images.

Instead of specifying the ROI with a dictionary, you can give a path to your mask file::

    "ROIs": {
        "ROI1": "path/to/your/mask/file.png",
        ...
    }


Running videobatch as a library
================================

Internally, videobatch calls :py:func:`videobatch.run`, with the
dictionary object created from the configuration JSON file.

You can therefore generate the config dictionary programatically (without editing a file),
and call :py:func:`videobatch.run` from within your Python script.

.. py:function:: videobatch.run(cfg)

    runs batch processing.

    :param cfg: the configuration information, either in a dictionary or as a path to the JSON file.
    :type cfg: str or dict

