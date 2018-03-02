# cpyvke
Curses PYthon Variable and Kernel Explorer

![A Basic Client](https://github.com/ipselium/cpyvke/blob/master/docs/array.png)


cpyvke is **still in development** : A lot of bugs are still there !

Note that this version only works with Python 3.x.
The Python 2.7 version is no longer maintened !

- - -

## kd5 : the daemon to communicate with IPython kernels

*Communication with ipython kernels.*

* Stream variable list each time a change occurs in the kernel
* Listen to request from the client

- - -

## cpyvke : the Curses interface

*Variable explorer and kernel manager.*

* Explore variables in IPython kernels
* Manage IPython kernels

- - -

## Requirement

* Ipython >= 5.1
* jupyter_client >= 4.4
* numpy (tested with 1.13.0)
* matplotlib (tested with 1.5.1)
* 256 colors terminal is preferred, but cpyvke also works with 8 colors terminals.
* Tested with **python 3.5 only**

- - -

## Configuration

A configuration file *cpyvke.conf* is created in `$HOME/.cpyvke/` at first startup. Appearance of the client can be customize (colors, font).

### Colors

The available colors are...

* black
* red
* green
* yellow
* blue
* magenta
* cyan
* white

### Fonts

cpyvke can also display powerline fonts. You can find them here :
https://github.com/powerline/fonts.

Add the following section in `$HOME/.cpyvke/cpyvke.conf`:

`[font]`

`powerline-font = True`


- - -

## Installation

`git clone https://github.com/ipselium/cpyvke.git`

`python3 setup.py install`

- - -

## Quick Start

### kd5 : The Daemon

*Usage: kd5 {start|stop|restart|list} [INTEGER]*

* start : start daemon. If no [INTEGER] is provided, a new ipython kernel is created. [INTEGER] is the id of the connection file.
* stop : stop daemon
* restart : restart daemon
* list : list available ipython kernels

### cpyvke : The client

*Usage: cpyvke [-h] [-L] [-D] [integer]*

* positional arguments:
	* [integer] : Start up with existing kernel. INTEGER is the id of the connection file.

* optional arguments:
	* [-h], [--help] : show this help message and exit
	* [-D], [--debug] : Debug mode
	* [-L], [--list] : List all kernels

* bindings:
	* **h** : help
	* **s** : sort by name/type
	* **l** : limit display to all variable matching the given keyword
	* **u** : undo limit
	* **c** : kernel manager
	* **/** : Search for variable
	* **q** : previous menu -- quit

### Setup workspace

* You can directly launch `cpyvke`. It will create a new kernel, start the daemon and launch the client
* cpyvke-launch-ipython automatically launch the current ipython console
* You can also manually open an existing ipython instance like this :
	`ipython console --existing kernel-xxxxx.json`
where xxxxx is the id of the kernel

### Note

If you just want to test cpyvke without installing. In cpyvke/ directory :

* launch kd5 first : `python3 -m cpyvke.kd5 start`
* then launch cpyvke : `python3 -m cpyvke.cpyvke`
* and launch ipython in another console : `python3 -m cpyvke.launch`


## Known Bugs and TODO list

*cpyvke* is still in developpement and may present unexpected behavior !

* Issue when shutting down client : whatever user choice, server is killed
* Fix lockfile creation
* cpyvke : crash when "brutal" resize
* cpyvke : Kernel manager (restart dead kernel ?)
* Kernel options (extra_arguments=["--matplotlib='inline'"])
* Compatibility python 3.x : Work still in progress !
