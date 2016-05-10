.. _execution_plans:

Execution plans
===============

.. code::

    --- builders (mock, pbuilder, docker, vagrant)
    pbuilder create                     | docker build/pull
    pbuilder exec gopythongo subprocess | docker run gopythongo subprocess
    
    -- versioners? (aptly, reprorepo, fromenv)
    
    -- assemblers (apt, virtualenv, copy, managepy)
      | apt-get                             | SAME
      | virtualenv                          |
      | copyin/pip install                  |
      | manage.py collectstatic             |
      | [aptly find version]                |
      
    --- packers (fpm, tar, docker)
      | fpm/tar                             |
      | copy out                            |
      |                                     | docker run gopythongo subprocess
      |                                     | copyin/apt-get install/tar xfz
      
    -- stores (aptly, rpm, docker, awsami?)
    aptly repo add                      | docker push/rm/rmi
