================
Basic tutorials
================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

First pass
----------

For the beginning, just run the following command in your terminal emulator::

  videobatch

This will not convert any videos.
Instead, this will generate a lengthy usage information like this::

  [usage]
      python videobatch.py <path/to/config-file.json>
  
  [base parameters]
  the JSON file must consist of a dictionary that contains the following keys and values:
        'command': (required) the command to run. see below for details.
        'sources': (required) list or pattern(s) of file names to perform conversion.
      'sourcedir': (optional) the directory where the program searches for the video. defaults to the current directory.
  
  the command-specific parameters can be found below.

  (the output continues...)

In principle, :py:mod:`videobatch` says:

+ It requires a JSON-format file as its sole argument; this must contain enough information
  for the program to perform conversion.
+ You need to specify the **conversion command** in the JSON file.
+ There are other **basic** and **command-specific parameters** that you have to fill in the JSON file.

So why not prepare this file?


Running the "projection" command
---------------------------------

Let's start from the ``projection`` command. 

Editing a JSON file
^^^^^^^^^^^^^^^^^^^^

Prepare a new (raw) text file called :file:`config.json`, and open it with a text editor.
There, fill in the followings::

  {
    "sources": ["<path to your video file>"],
    "command": "projection",
    "type": "max"
  }

The whole content is wrapped by a pair of curly brackets {}.
By doing so, we can define a **dictionary** in a JSON-format document.
A dictionary, in programmers' terminology, is just like a data record in an Excel file
where you can store and retrieve a certain **value** based on a **key** (just like a column
in a table).
You can see that a pair of keys and values are placed inside curly brackets as
``<key>:<value>``, separated by commas.
Using key–value pairs, we can store specific properties of this configuration file
related to their names (such as "command", "type" etc).


Parameter specification
^^^^^^^^^^^^^^^^^^^^^^^^

Now it is about the actual keys that are used in :file:`config.json`.
As we saw in the previous section, there are several parameters we need to specify:

+ "command": the conversion command. write "projection" here.
+ "sources": the list of videos that you want to convert. you can specify
  any of your favorite videos.
+ "sourcedir": the usage info says that it "defaults to the current directory", meaning
  that you don't have to specify if you don't mind. Let's leave here unspecified for the time being.

In addition, :guilabel:`[commands]` section of the usage info tells us about what parameter you can specify
for the "projection" command::

  projection: creates a t-projection image file.
              (parameters)
              <- 'type': one of ("max", "mean", "avg", "scale", "magenta_scale"). 'max' by default.
              <- 'outdir': the directory where the output file(s) will go. defaults to the current directory.

In essence, by using the "type" parameter, you can specify the mode of projection (e.g. maximal projection, minimal,
average, standard-deviation...).
Although there is a default value for the "type" parameter, let's fill it in for your later experiment of
changing the parameter.

It says that there is the default value for "outdir", so let's leave this out as well.

Check carefully
^^^^^^^^^^^^^^^^

Before running :py:mod:`videobatch`, check that you wrote the contents *exactly* as in the preceding section, and save it.

.. note::

  JSON format is relatively strict about formatting things.
  There are several rules to obey:

  + every string must be wrapped by double-quotation marks, such as in ``"command"``.
  + a comma must reside between key–value pairs **and no commas after the last pair**.

.. note::
  Particularly in Windows, each back-slash ``\`` in the path must be doubled as ``\\``
  (e.g. write ``"C:\\Users\\gwappa"`` for indicating ``C:\Users\gwappa``)

  in JSON (and in Python), a back-slash has a special role in string (sometimes called as the
  "**escape character**") to represent control characters (e.g. newline ``\n``, or backspace ``\b``).
  In order to represent the ``\`` itself, you therefore must use it twice ``\\`` so that JSON
  does not recognize it in combination with the following character.

Run
^^^^

After checking, it is time to run :py:mod:`videobatch`::

  videobatch config.json

You will notice that the projection image file will be generated in the same directory as :file:`config.json`
(if not, check the file carefully or ask me).


Running the 'pixylation' command
---------------------------------

"Pixylation" is a term that I coined to describe what it does: it detects pixels of the specified color range,
and returns the center position of the set of matched pixels.

Principles behind 'Pixylation'
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each color can be represented as "hue", "saturation" and "lightness" (or HSL altogether), where

* Hue represents the balance of elementary colors (red, green, blue).
* Saturation specifies how vivid the color is.
* Lightness indicates how bright the color is.

The HSL method of color representation is as universal as the RGB or the CMYK methods are, in a sense
that it can represent any color that shows up on your display.

We use the hue values in particular, because it is less affected by the lighting conditions than using,
for example, the RGB values.

Actually, this method is most commonly used in the camera called 'Pixy' (and this is where the term 'Pixylation'
comes from); it identifies objects by a blob of colors in the specific hue range.
It is because of their success in tracking objects fast (60 FPS) and robustly that we opted the hue-based
tracking method.

Configuration parameters
^^^^^^^^^^^^^^^^^^^^^^^^^

When you check the description for the 'pixylation' command, you will find a number of options::

  pixylation: runs 'Pixylator' with multiple masks/ROIs, and saves mask/result files.
              (parameters)
              <- 'mode': the method for converting matched pixels into a position. only has the "CM" mode for the moment.
              <- 'colors': a dictionary where keys represent the names of colors and the values represent their color ranges.
                           a color range is specified as [<from-hue>, <to-hue>].
              <- 'ROIs': a dictionary where keys represent the names of ROIs and the values represent their regions.
                         a rectangular region can be specified as a dictionary {"x":..., "y":..., "w":..., "h":...}.
                         a free-shape region can be specified as a path to a B/W image (white pixels will be taken).
              <- 'maskdir': the directory where the mask file(s) will go. defaults to the current directory.
              <- 'resultdir': the directory where the result file(s) will go. defaults to the current directory.

Just to summarize a little bit more, the parameters are about ROIs (i.e. where to pick up pixels from),
color range to pick up, and the output.
For the output, we have 'masks' and 'results'.

* A mask file is a movie file. It displays the set of pixels that are identified as having "within-range" colors.
  The pixels are shown in the color that is the representative of that color range.
* A result file is a CSV (a sort of spreadsheet, but in a text format) file. It contains the positions of the 
  pixel set that you specified.

Although there are several different ways (e.g. centroid) to define "the position of a set of pixels", but the
only method we use for the time being is by computing "the center of mass".
It averages the positions of all the matched pixels weighted by their brightness.
By doing so, it becomes more robust to the apparent changes in the shape (by lighting conditions) and spontaneous
out-of-place noises.

Writing a configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Having that said, let's write a config file::

  {
    "sources": ["<path to your video file>"],
    "command": "pixylation",
    "mode": "CM",
    "colors": {
        "Green": [90,225],
        "Magenta": [260,360] 
    },
    "ROIs": {
        "object": {
            "x": 318,
            "y": 49,
            "w": 286,
            "h": 464 
        } 
    }
  }

First of all, as the command description states, both the "mask" and "result" shall go to the current directory
since we specify neither ``maskdir`` nor ``resultdir``.
If you are to use a number of files as the source, you'd better having dedicated directories to avoid chaos.

The colors can be specified as the array form ``[<from>,<to>]``.
The overall structure of this entry is made of a "dictionary" format, having the key/value being the name of the color
and its range, respectively.
You can add as many colors as you want as long as it satisfies your interests.

Similar goes for the "ROIs" entry: the key represents the name of the ROI, and the value represents 
the specification of the ROI.
You can specify the origin X, origin Y, width and height to identify the rectangular ROI (as is shown).
Note the coordinate system may be different from what you are used to:

* The "origin" of the coordinates (i.e. the point (x=0,y=0))is at the *top-left* corner of the image.
* "X axis" is the horizontal axis of the image.
* "Y axis" is the vertical axis of the image.

.. note::

    To determine the "right" values for color specification and the ROIs, there will require a small set of trials and errors.
    I recommend having a smaller video clip to test the parameters.
    I personally use the `Pixylator plugin in ImageJ <https://github.com/gwappa/Pixylator>`_ for the trial-and-error phase 
    because it provides you with a lot of essential graphical information.


Run
^^^^

After checking, running is the same as the above::

  videobatch config.json

You will notice that the mask and the result files are generate.
Check that the mask file plays the positions of detected pixels as you expect.

.. note::

  Because of the way :py:mod:`videobatch` creates the output video file, it is possible that your video player
  does not recognize the mask movie.
  In such cases, try using `VLC <http://www.videolan.org/>`_; at the time of writing, it opens any videos that
  :py:mod:`videobatch` creates.


