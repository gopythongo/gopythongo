GoPythonGo creates Python deployment artifacts
==============================================

GoPythonGo is still under very active development. Currently you can use it to build .deb packages to deploy virtual
environments using Debian packages.

Getting started
---------------

On Debian:

  1. Install GoPythonGo and [aptly](https://aptly.info). As `root`:

    echo "deb http://gopythongo.s3-website.eu-central-1.amazonaws.com/debian jessie main" > /etc/apt/sources.list.d/gopythongo.list
    echo "deb http://repo.aptly.info/ squeeze main" > /etc/apt/sources.list.d/aptly.list
    apt-get update
    apt-get install gopythongo aptly
    
  2. create a simple example project:
  
    ```
            mkdir -p /tmp/helloworld/helloworld
            cat > /tmp/helloworld/helloworld/__init__.py << EOF
        # -* encoding: utf-8
        
        def main():
            print("hello world!")
            
        if __name__ == "__main__":
            main()
        EOF
        
            cat > /tmp/helloworld/setup.py << EOF
        #!/usr/bin/env python -u
        import os
        from setuptools import setup
        
        setup(
            name='helloworld',
            version="1.0",
            packages=["helloworld",],
        )
        EOF
    ```

  3. Create a GoPythonGo configuration:

    ```  
        cd /tmp/helloworld
        /opt/gopythongo/bin/gopythongo --init pbuilder_deb
        sed -e s/mypackage/helloworld/ .gopythongo/config | sed -e s/# aptly-publish-opts/aptly-publish-opts/ > .gopythongo/config.1
        mv .gopythongo/config.1 .gopythongo/config
        sed -e s/PACKAGENAME/helloworld/ .gopythongo/fpm_opts > .gopythongo/fpm_opts.1
        mv .gopythongo/fpm_opts.1 .gopythongo/fpm_opts
    ```
   
  4. Create a Debian repo and a 2048 bit RSA signing keypair. Choose "password" or a secure passphrase and insert it
     below:

    ```  
        aptly repo create helloworld
        gpg --no-default-keyring --keyring /root/helloworld_sign.gpg --gen-key
        echo "password" > /root/helloworld_passphrase.txt
    ```
    
  5. Build the helloworld package:

    ```  
        /opt/gopythongo/bin/gopythongo /opt/helloworld /tmp/helloworld
    ```
