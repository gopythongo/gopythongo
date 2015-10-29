.. GoPythonGo documentation master file

A sane, fully documented Python deployment model
================================================

During my tenure as CTO of `LaterPay <https://laterpay.net/>`_ we (that mostly being @jdelic (me), @arenstar and
@doismellburning) experimented a lot with deploying Python in different ways. Now that I am a free agent, I first
started improving on what we had at LaterPay for my own use, but subsequently realized that it might be useful
for other people. So, have a fully documented sane deployment model for Python. For free. :)

The two parts of GoPythonGo
---------------------------
This project consists of two parts:

  1. a process description, information and links on what a good Python deployment process looks like and how you can
     implement one for your project, how you integrate it with configuration data and other services in your project

  2. a tool, written in Python, that makes it easy to build ready-to-deploy .deb/.rpm packages and put them on an
     APT or YUM repository for easy installation

.. toctree::
    :maxdepth: 1
    :numbered:
    :caption: The process

    process/intro
    process/build_process
    process/configuration
    process/virtualenvs
    process/docker

.. toctree::
    :maxdepth: 1
    :numbered:
    :caption: The toolkit

    toolkit/intro


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

