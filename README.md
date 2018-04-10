- - -

# cpyvke
Curses PYthon Variable and Kernel Explorer

![A Basic Client](https://github.com/ipselium/cpyvke/blob/master/docs/pydev.png)


cpyvke is a variable explorer and a kernel manager written in Python 3 ncurses
for iPython kernels (Python 2.x or 3.x).
cpyvke supports inspection of numpy ndarray among others types, and provides a set of
tools to visualize and plot data.

Be aware that cpyvke is **still in development** : A lot of bugs are definitely there !

Note that this version only works with Python 3.x. The Python 2.7 version is no
longer maintened !

- - -

## cpyvke : the Curses interface

*Variable explorer and kernel manager.*

* Explore variables in IPython kernels
* Manage IPython kernels

- - -

## kd5 : the daemon to communicate with IPython kernels

*Communication with ipython kernels.*

* Stream variable list each time a change occurs in the kernel
* Listen to request from the client

- - -

## Requirement

* 256 colors terminal is preferred, but cpyvke also works with 8 colors terminals.
* python3-tk : install it with your package manager
* Tested with **python 3.5 only**

- - -

## Dependencies

* Ipython >= 5.1
* ipykernel (tested with 4.6.1)
* jupyter_client >= 4.4
* psutil (tested with 3.4.2)
* numpy (tested with 1.13.0)
* matplotlib (tested with 1.5.1)

- - -

## Installation

`git clone https://github.com/ipselium/cpyvke.git`

`python3 setup.py install`

- - -

## Quick Start

To start working, just launch `cpyvke` in a console. It will create a new kernel, start the daemon and launch the client :

`cpyvke`

You can also launch `cpyvke-launch-ipython` to open the current kernel :

`cpyvke-launch-ipython`

You can now work in this Ipython console and cpyvke will display all changes in the associated kernel :

`In [1] : run my_program.py`


## Tips

You can also use : https://github.com/ipselium/vim-cpyvke

**vim-cpyvke** provides tools to evaluate blocks of code or full scripts
directly from vim. The duo **cpyvke/vim-cpyvke** paired with a vim plugin such
as **python-mode** (www.github.com/klen/python-mode) can provide a complete
development environment for Python in console.

- - -

## Manuals

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
	* **ENTER** : Validate/Item menu
	* **q|ESC** : Previous menu/quit'
	* **s** : sort by name/type
	* **l** : limit display to all variable matching the given keyword
	* **u** : undo limit
	* **k** : kernel manager
	* **/** : Search for variable
	* **q** : previous menu -- quit
	* **r** : Refresh explorer
	* **c-r** : Restart Daemon
	* **R** : Restart connection to daemon
	* **D** : Disconnect from daemon
	* **C** : Connect to daemon
	* **↓** : Next line
	* **↑** : Previous line
	* **→|↡** Next page
	* **←|↟** Previous page

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

- - -

## Configuration

![Configuration](https://github.com/ipselium/cpyvke/blob/master/docs/array.png)

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

### Python kernel version

The cpyvke/kd5 duo handles python 2.x or 3.x kernel equally. To setup the Python kernel you'll want to use :

`[kernel version]`

`version = 3`

The `version` can be 2 or 3 for python 2.x kernel or 3.x kernel, respectively.


- - -

## Known Bugs

*cpyvke* is still in developpement and may present unexpected behavior !

- - -
