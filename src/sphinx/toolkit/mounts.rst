Making file system resources available in the build environment
===============================================================


Bind mounts are not recursive
-----------------------------
**(or: "why is this subfolder empty inside the build environment?")**. A
common problem that might get you is that when using the ``--mount``
command-line parameter, you might find out that some subfolders of your
mounted path are empty. This can happen if that subfolder is itself a
mount point of another file system, because *bind mounts are not 
themselves recursive*. So if you need to access resources which are
mounted to a mountpoint inside a subfolder of one of your mounts,
**you must use ``--mount`` twice on the command-line and explicitly
mount that subfolder as well**.
