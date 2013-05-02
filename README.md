pylpi
=====

A simple fabric friendly way to create a local pypi mirror

Installation
============

* Make sure you have Fabric (pip install fabric) installed on your virtualenv (or system wide Python installation)
* fab production install_server_os_packages
* fab production deploy
* fab production start
* You should be able to access your local pypi mirror server on http://<server_ip>/simple
