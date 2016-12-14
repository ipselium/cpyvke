# cpyvke
Curses PYthon Variable and Kernel Explorer

![A Basic Client](https://github.com/ipselium/cpyvke/blob/master/docs/basic_menu.png)
![A Basic Client](https://github.com/ipselium/cpyvke/blob/master/docs/basic_inspect.png)
![A Basic Client](https://github.com/ipselium/cpyvke/blob/master/docs/basic_kernel.png)

![A Fancy Client](https://github.com/ipselium/cpyvke/blob/master/docs/fancy_menu.png)
![A Fancy Client](https://github.com/ipselium/cpyvke/blob/master/docs/fancy_inspect.png)
![A Fancy Client](https://github.com/ipselium/cpyvke/blob/master/docs/fancy_kernel.png)


cpyvke is **still in development**

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
* Tested with **python 2.7 only**
* 256 colors terminal is prefered, but cpyvke also works with 8 colors terminals.

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

`python setup.py install`

- - -

## Quick Start

### kd5 : The Daemon

*Usage: kd5 {start|stop|restart|list} [INTEGER]*

* start daemon : If no [INTEGER] is provided, a new ipython kernel is created. [INTEGER] is the id of the connection file.
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
	* **l** : limit display to varaible matching the given keyword
	* **u** : undo limit
	* **c** : kernel manager
	* **/** : Search for variable
	* **q** : previous menu -- quit

### Setup workspace

* You can directly launch `cpyvke`. It will create a new kernel, start the daemon and launch the client
* You can open an ipython instance like this :
	`ipython console --existing kernel-xxx_kernel_id_xxx.json`




