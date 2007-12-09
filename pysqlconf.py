﻿#!/usr/bin/python
# -*- coding: utf-8 -*-

# Sébastien Renard (sebastien.renard@digitalfox.org)
# Code licensed under GNU GPL V2

"""This module defines the PysqlConf class
that handles all pysql configuration stuff"""

# Python imports:
import os
import sys
import cPickle
from ConfigParser import ConfigParser
import readline

# Pysql imports:
from pysqlexception import PysqlException
from pysqlcolor import BOLD, CYAN, GREEN, GREY, RED, RESET
from pysqlio import PysqlIO

class PysqlConf:
    """ Handles configuration stuff"""

    # Config instance (singleton)
    configInstance=None

    def __init__(self):
        """Config instance creation. Read the config file"""

        # Config Parser
        self.configParser=None

        # Config file path
        self.configPath=os.path.expandvars("$HOME/.pysqlrc")

        # Cache file path
        self.cachePath=os.path.expandvars("$HOME/.pysqlcache")

        # History file path
        self.historyPath=os.path.expandvars("$HOME/.pysqlhistory")

        # User SQL library file path
        self.sqlLibPath=os.path.expandvars("$HOME/.pysqlsqllibrary")

        # Config changed flag
        self.changed=False

        # Completionlist dictionary
        self.completeLists={}

        # User defined sql Library
        self.sqlLibrary={}

        # Initialiase IO
        self.stdout=PysqlIO.getIOHandler()

        # Tries to load previous completion List from disk
        try:
            self.completeLists=cPickle.load(file(self.cachePath))
        except Exception, e:
            # Cannot load any previous cache, start from a clear one
            pass

        # Tries to load previous history list from disk
        try:
            readline.read_history_file(self.historyPath)
        except Exception, e:
            # Cannot load any previous history. Start from a clear one
            pass

        # Tries to load previous sqlLibrary from disk
        try:
            self.sqlLibrary=cPickle.load(file(self.sqlLibPath))
        except Exception, e:
            # Cannot load any previous sqlLibrary, start from a clear one
            pass

        # Load default value for all parameters
        #TODO: rename separator csvsep
        self.default={
            "completionlistsize" : 100,
            "fetchsize"          : 30,
            "termwidth"          : 120,
            "widthmin"           : 5,
            "transpose"          : "no",
            "separator"          : ";",
            "colsep"             : "space",
            "shrink"             : "yes",
            "echo"               : "no",
            "unit"               : "mb",
            "graph_program"      : "auto",
            "graph_format"       : "png",
            "graph_fontname"     : "courier",
            "graph_fontsize"     : "10.0",
            "graph_fontcolor"    : "black",
            "graph_tablecolor"   : "ivory",
            "graph_linkcolor"    : "black",
            "graph_indexcolor"   : "skyblue",
            "graph_bordercolor"  : "black",
            "graph_linklabel"    : "off",
            "graph_depmaxdepth"  : 8,
            "graph_depmaxnodes"  : 100,
            "graph_viewer"       : "auto"
            }

        # Searches for config file..in $HOME first, or in pysql dir
        #TODO: will not work on windows...

        if not self.__isReadWrite(self.configPath):
            self.configPath=os.path.join(sys.path[0],"pysqlrc")
        self.stdout(CYAN+_("Using config file %s") % self.configPath + RESET)

        # Reads config file
        self.configParser=ConfigParser()
        try:
            self.configParser.readfp(open(self.configPath))
        except Exception, e:
            self.stdout(RED+BOLD+_("Cannot read configuration file pysqlrc in either $HOME or pysql dir."))
            self.stdout(_("Using default.\n(Reason was: %s)") % e + RESET)

        # Host codec used to display string on screen
        self.codec=None

    def getConfig(cls):
        """Factory for configuration instance singleton
        @return: PysqlConf instance"""
        if cls.configInstance is None:
            cls.configInstance=PysqlConf()
        return cls.configInstance
    getConfig=classmethod(getConfig)

    def get(self, key):
        """ Gets the value of the parameter key
        @param key: parameter name
        @type key: string
        @return: str or int (if cast if possible)
        """
        key=key.lower()
        if self.configParser is not None:
            try:
                value=self.configParser.get("PYSQL", key)
            except Exception:
                value=self.getDefault(key)
        else:
            value=self.getDefault(key)

        # Tries to cast to numeric. If it does not work, we assume the value is a string
        try:
            value=int(value)
        except (ValueError, TypeError):
            try:
                value=float(value)
            except (ValueError, TypeError):
                pass
        return value

    def getAll(self):
        """Gets all defined parameters
        @return: list of (key, userValue, defaultValue)
        """
        result={}
        # Populates with user value
        if self.configParser is not None:
            if self.configParser.has_section("PYSQL"):
                all=self.configParser.items("PYSQL")
                if all is not None:
                    for (key, value) in all:
                        # Try to cast to int
                        try:
                            value=int(value)
                        except (ValueError, TypeError):
                            pass
                        result[key]=[value, ""]
        # Populates with default value
        for (key, value) in self.default.items():
            if result.has_key(key):
                result[key]=[result[key][0], value]
            else:
                result[key]=["", value]

        # Transforms dict into list
        result=[[i[0]]+i[1] for i in result.items()]
        # Alphabetic sort
        result.sort()
        return result

    def getDefault(self, key):
        """Returns the default value for a parameter. If no default value is defined, return None"""
        if self.default.has_key(key):
            return self.default[key]
        else:
            self.stdout("(DEBUG) Key %s has no default value !" % key)
            return None

    def verify(self, key, value):
        """Checks if the key has correct value
        It does not update the value.
        @param key: key parameter to be tested
        @param value: value to be tested
        @return: True if value is correct, else False"""
        # Expanding shell variables
        if isinstance(value, str):
            value=os.path.expandvars(value)

        # Integer parameter
        if ( key in ("termwidth",
                     "fetchsize",
                     "widthmin",
                     "completionlistsize",
                     "graph_fontsize",
                     "graph_depmaxdepth",
                     "graph_depmaxnodes")
             ):
            try:
                value=int(value)
            except (ValueError, TypeError):
                return False
            if value>1:
                return True
            else:
                return False
        # Boolean parameter
        elif key in ("transpose", "shrink", "echo", "graph_linklabel"):
            if value in ("yes", "no"):
                return True
            else:
                return False
        # String parameter
        elif key in ("separator", "colsep", "graph_viewer"):
            if len(value)>0:
                return True
            else:
                return False
        # Lists defined string parameter
        elif key=="unit":
            if value in ("b", "kb", "mb", "gb", "tb", "pb"):
                return True
            else:
                return False
        elif key=="graph_program":
            if value in ("auto", "circo", "dot", "dotty", "fdp", "lefty", "neato", "twopi"):
                return True
            else:
                return False
        elif key=="graph_format":
            if value in ("dia", "dot", "gif", "jpg", "jpeg", "mp", "pcl", "pic", \
                         "plain", "png", "ps", "ps2", "svg", "svgz", "wbmp"):
                return True
            else:
                return False
        elif key=="graph_fontname":
            if value in ("arial", "courier", "times-roman", "verdana"):
                return True
            else:
                return False
        elif key in ("graph_bordercolor", "graph_linkcolor", "graph_tablecolor"):
            return True
        else:
            self.stdout("(DEBUG) Key %s does not exist or does not have a verify routine !" % key)
            return False

    def set(self, key, value):
        """Sets the parameter « key » to « value »"""
        key=str(key).lower()
        value=str(value).lower()
        if self.configParser is not None:
            if not self.configParser.has_section("PYSQL"):
                self.configParser.add_section("PYSQL")
                self.stdout(GREEN+_("(Config file created)")+RESET)
            if self.verify(key, value):
                self.configParser.set("PYSQL", key, value)
                self.setChanged(True)
            else:
                raise PysqlException("Sorry, value %s is not valid for parameter %s" % (value, key))
        else:
            raise PysqlException("Cannot set config, no configParser exist !")

    def write(self):
        """Writes config to disk"""
        #TODO: test needed
        #TODO: should be rewritten (quite ugly no ?)
        if self.changed:
            try:
                configFile=file(self.configPath, "w")
                self.configParser.write(configFile)
                configFile.close()
                self.setChanged(False)
                self.stdout(GREEN+_("(config file saved successfully)")+RESET)
            except Exception:
                self.stdout(CYAN+_("Cannot write config to %s. Using $HOME/.pysqlrc instead")
                             % self.configPath)
                self.configPath=os.path.expandvars("$HOME/.pysqlrc")
                try:
                    configFile=file(self.configPath, "w")
                    self.configParser.write(configFile)
                    configFile.close()
                    self.setChanged(False)
                    self.stdout(GREEN+_("(config file saved successfully)")+RESET)
                except Exception, e:
                    raise PysqlException(_("fail to write file: %s") % e)
        else:
            self.stdout(CYAN+_("(no need to save)")+RESET)

    def writeCache(self):
        """Writes completion list cache to disk"""
        try:
            cPickle.dump(self.completeLists, file(self.cachePath, "w"))
        except Exception, e:
            raise PysqlException(_("Fail to save completion cache to %s. Error was:\n\t%s")
                        % (self.cachePath, e))

    def writeSqlLibrary(self):
        """Writes user sql library to disk"""
        try:
            cPickle.dump(self.sqlLibrary, file(self.sqlLibPath, "w"))
        except Exception, e:
            raise PysqlException(_("Fail to open user sql library to %s. Error was:\n\t%s")
                        % (self.sqlLibPath, e))

    def writeHistory(self):
        """Writes shell history to disk"""
        try:
            # Open r/w and close file to create one if needed
            historyFile=file(self.historyPath, "w")
            historyFile.close()
            readline.set_history_length(1000)
            readline.write_history_file(self.historyPath)
        except Exception, e:
            raise PysqlException(_("Fail to save history to %s. Error was:\n\t%s")
                        % (self.historyPath, e))
    def setChanged(self, state):
        """Indicates if config data has changed. This is used
        to detect if it is necessary to save config file to disk"""
        self.changed=state

    def isChanged(self):
        """@return: change state (boolean)"""
        return self.changed

    def setCodec(self, codec):
        """Sets the host codec used to display string on screen
        @arg codec: codec name
        @type codec: str"""
        self.codec=codec

    def getCodec(self):
        """@return: host codec used to display string on screen"""
        return self.codec

    def __which(self, command):
        """Emulates the Unix which to search if command is in the PATH
        Instead of which, if multiple args are given, consider it as a command line
        and test only the first one.
        Returns the full path to command if found or None"""
        command=command.split()[0]
        for directory in os.getenv("PATH").split(":"):
            fullpath=os.path.join(directory,command)
            if os.access(fullpath, os.X_OK):
                return fullpath
        return None

    def __isReadWrite(self, filepath):
        """Checks if filepath is readable and writable. Returns a boolean
        @param filepath: the full path to the file
        @type filepath: str
        @return: Boolean"""
        if(os.access(filepath, os.R_OK) and os.access(filepath, os.W_OK)):
            return True
        else:
            return False