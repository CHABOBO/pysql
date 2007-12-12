#!/usr/bin/python
# -*- coding: utf-8 -*-

# Sébastien Renard (sebastien.renard@digitalfox.org)
# Code licensed under GNU GPL V2

from distutils.core import setup

langs=["fr"]
data_files=[]
for lang in langs:
    data_files.append(["share/locale/%s/LC_MESSAGES/" % lang, 
                       ["locale/%s/LC_MESSAGES/pysql.mo" % lang]])

 
setup(name="pysql",
      version="0.11",
      description="PySQL is an Oracle enhanced client",
      author="Sébastien Renard and Sébastien Delcros",
      author_email="pysql@digitalfox.org",
      url="http://pysql.sf.net",
      package_dir={"pysql" : "src"},
      packages=["pysql"],
      scripts=["pysql"],
      data_files=data_files
      )