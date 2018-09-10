======================
Installing videobatch
======================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Dependency on `ffmpeg`
----------------------

:py:mod:`videobatch` depends on the :command:`ffmpeg`-related commands to
read/write videos.
Please install the necessary commands to your terminal emulator:

1. Install `ffmpeg <https://ffmpeg.org/>`_.

   * make sure that you install all the sub-commands, in particular :command:`ffprobe`.
   * For macs and linux computers, it may be easier installing through a package manager
     such as :command:`apt` or `Homebrew <https://brew.sh/>`_.
2. Make sure that your terminal emulator can find :command:`ffprobe`.
   
   * this is the command that specifies where you can find the ffmpeg programs.

You can check if it is the case by executing the following code from your terminal emulator::

    which ffprobe
    # response example: /usr/local/bin/ffprobe

In some cases, in Windows cmd.exe, for example, use the following instead::

    where ffprobe
    # response example: C:\ffmpeg\bin\ffprobe

In case if your terminal does not recognize the installed :command:`ffprobe`, you need to add its
containing directory to your command search path (typically it is called :envvar:`PATH` and
it is in the environment variables list).

Installation of videobatch
--------------------------

You can install :py:mod:`videobatch` through the :command:`pip` Python package manager.
The following call automatically downloads/upgrades the dependencies::

    pip install git+https://github.com/gwappa/python-videobatch.git

.. note::

    As a matter of fact, :py:mod:`videobatch` is built on top of many great open-source Python libraries, namely:

    + :py:mod:`numpy`
    + :py:mod:`scipy`
    + :py:mod:`matplotlib`
    + :py:mod:`sk-video`

    In most cases you don't have to take care about installing these libraries before downloading
    :py:mod:`videobatch`, as the :command:`pip` library manager taks care of it for you.

    If your :command:`pip` fails to download the libraries, or if you don't have Python at all, then 
    consider downloading `Anaconda <https://www.anaconda.com/distribution/>`_, which is a
    Python distribution that contains most of the useful libraries (including :py:mod:`numpy`,
    :py:mod:`scipy` and :py:mod:`matplotlib`) pre-installed.


