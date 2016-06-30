.. _templating:

GoPythonGo templating support
=============================

When you look at the list of parameters in the GoPythonGo help and/or this documentation, you will realize that some of
the parameters state "Supports templating" or "You can use templating here".

Basically, GoPythonGo acknowledges that build configuration is often variable in many ways. For example: With everything
else being the same, you want to change a Docker container's tags based off the branch it's built from.

Sometimes the best place to accomplish that is by using templated configuration files. Another such case might be that
you are using the ``fpm`` packer and you want to change the resulting package's filename. So you have been invoking
GoPythonGo with the parameter ``--fpm-opts=.gopythongo/my_fpm_options`` and ``my_fpm_options`` contained some simple
static configuration`. You can make ``my_fpm_options`` a template by simply using
``--fpm-opts=template:.gopythongo/my_fpm_options`` instead.

``my_fpm_options`` will then be processed by the Jinja2 template engine before the options contained within are being
passed on to ``fpm``. This allows you to liberally use information from the build environment, such as the output of
your chosen Versioners, to modify the parameters passed to ``fpm``.
