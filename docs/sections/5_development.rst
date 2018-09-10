=========================
Writing your own command
=========================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

You can add your own command relatively simply.
Please follow the instructions below:

General instructions
====================

1. Derive a new class from ``videobatch.AbstractBatch``. This base class implements most of the
   batch-related common tasks.
2. Registration of the command is achieved at runtime, by wrapping the class with the
   :py:meth:`videobatch.command` decorator.
3. Please add a doc-string to the class (refer to the other commands for the format) so that
   it appears on the usage description.

.. py:decoratormethod:: videobatch.command(name)

    registers the decorated class as a command that has the name as specified.

    :param str name: the name of the command. If the same name already exists,
      the one that is loaded later will overide the existing one.
    

Command-specific implementation
===============================

There are several methods that you are suppose to implement:

.. py:method:: __init__(self, *src, **config)

  You have to call ``super(<your class>,self).__init__(*src, **config)``, in
  order to initialize AbstractBatch nicely, and run the batch process properly.
  You can receive any command-specific parameters by having a keyword argument on the
  declaration of :py:meth:`__init__`.

  :param tuple src: list of source files
  :param dict config: keyword arguments that represent the configuration information.

.. py:method:: __start__(self, name)

  This method is called whenever :py:mod:`videobatch` is starting to process a new file.
  Here, you can implement the file-wise initialization code (such as preparing the output file).

  :param str name: the name of the file that is going to be processed.

.. py:method:: __update__(self, i, frame)

  This is the main method for frame-by-frame processing, and is called for each frame to be processed.

  :param int i: the index of the current frame.
  :param numpy.ndarray frame: the 3-D matrix (x, y, rgb) of the image data.

.. py:method:: __done__(self, name, err=False)

  This method is called whenever :py:mod:`videobatch` has done processing a file.

  :param str name: the name of the file that has been processed.
  :param bool err: indicates if an error occurred and the process gets aborted for this file.
    Note that it only contains a boolean value, and printing the exception is done elsewhere. 

On the other hand, :py:class:`AbstractBatch` provides the entry point for batch processes.
You are *not* supposed to change the implementation:

.. py:method:: AbstractBatch.run(self)

    runs a batch process.
    
    All the configuration must have been already done in :py:meth:`__init__`.
    Within :py:meth:`run`, :py:class:`AbstractBatch` calls :py:meth:`__start__`,
    :py:meth:`__update__` and :py:meth:`__done__`.

Typical flow
=============

1. :py:mod:`videobatch` gets loaded.
   The :py:meth:`videobatch.command` decorator adds commands to the registry.
2. When :py:func:`videobatch.run(cfg)` is called, it looks up for the command
   as it is specified in the configuration.
3. It retrieves the command class from the registry, and calls
   :py:meth:`__init__`, and then :py:meth:`AbstractBatch.run`.
4. Inside :py:meth:`run`, the followings will be performed for each file:

   a. :py:meth:`__start__` is called with the file name.
   b. Single frames are retrieved one by one, and :py:meth:`__update__` is
      called each time.
   c. Upon successful completion or abortion of conversion,
      :py:meth:`__done__` is called.
