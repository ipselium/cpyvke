TODO :

* 12/14/16:
	* kd5 : fix unicode crash (when user assign a unicode to a string variable)
	* cpyvke : Viewer crash when trying to read unicode string
	* Client Log function
	* Kernel manager (restart dead kernel ?)
	* Fix bug : for ndarray savetxt : IndexError: list index out of range
	* Daemon : Fix some bugs
	* Kernel options (extra_arguments=["--matplotlib='inline'"])
	* Fix lockfile creation
	* Compatibility python 3.x :
	    * print : **ok**
	    * dict.keys() : **ok**
	    * import : **ok**
 	    * from io import open : to check
	    * class myclass(object) : **ok**
