#!/usr/bin/env python
# Copyright (C) 2005 Insecure.Com LLC.
#
# Authors: Adriano Monteiro Marques <py.adriano@gmail.com>
#          Cleber Rodrigues <cleber.gnu@gmail.com>
#                           <cleber@globalred.com.br>
#          
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import os
import os.path
import sys
import re

from distutils.core import setup
from distutils.command.install import install
from distutils.command.sdist import sdist
from distutils.file_util import copy_file

from ConfigParser import ConfigParser
from glob import glob
from stat import ST_MODE

# Try to load py2exe (works only on Windows)
# Bail out silently if not possible
build_exe = install
if os.name == 'nt':
    try:
        import py2exe
        from py2exe.build_exe import py2exe as build_exe
    except ImportError:
        pass
        

##################################################################################
# Main Variables

# Directories
pixmaps_dir = os.path.join('share', 'pixmaps', 'umit')
icons_dir = os.path.join('share', 'icons', 'umit')
locale_dir = os.path.join('share', 'locale')
umit_version = os.path.join("config", "umit_version")

config_dir = os.path.join('config', 'umit')
dist_config_dir = os.path.join('dist', config_dir)
dist_umit_conf = os.path.join(dist_config_dir, "umit.conf")

umit_core = os.path.join("umitCore")
paths_file = os.path.join(umit_core, "Paths.py")
backup_paths_file = os.path.join(umit_core, "Backup_Paths.py")



user_dir = '.umit'


###################################################################################
# Main Functions

def umit_version():
    return open("umit_version").readlines()[0]

def check_dependencies():
    '''Tries to check all dependencies, and abort instalation if something is missing
    Checking:
    - gtk
    - psyco
    - pysqlite2
    '''
    
    try:
        import gtk

        # Checking PyGTK version
        if gtk.pygtk_version[0] < 2 or gtk.pygtk_version[1] < 6:
            raise Exception, "PyGTK must be version 2.6 or higher. Found version %s.%s.%s"\
                        % (gtk.pygtk_version[0], gtk.pygtk_version[1], gtk.pygtk_version[2])

        if gtk.gtk_version[0] < 2 or gtk.pygtk_version[1] < 6:
            raise Exception, "GTK must be version 2.6 or higher. Found version %s.%s.%s"\
                        % (gtk.gtk_version[0], gtk.gtk_version[1], gtk.gtk_version[2])
    except ImportError:
        print "No GTK found"
    except Exception, msg:
        print msg

    try:
        from pysqlite2 import dbapi2
    except ImportError:
        print "No pysqlite2 found"

    try:
        import psyco
    except ImportError:
        print "Install psyco and get a better performance!"
        print "http://psyco.sourceforge.net"


def mo_find(result, dirname, fnames):
    files = []
    for f in fnames:
        p = os.path.join(dirname, f)
        if os.path.isfile(p) and f.endswith(".mo"):
            files.append(p)
        
    if files:
        result.append((dirname, files))


#####################################################################################
# Installation variables

# SVG files are used only in Linux, so there is no need to copy them in othe platforms
svg = []
if sys.platform == 'linux2':
    svg = glob(os.path.join('share', 'pixmaps', '*.svg'))


data_files = [ (pixmaps_dir, svg + glob(os.path.join('share', 'pixmaps', '*.png')) +
                             glob(os.path.join('share', 'pixmaps', 'umit.o*'))),
               (config_dir, [os.path.join('config', 'umit.conf')] +
                            [os.path.join('config', 'scan_profile.usp')] +
                            ['umit_version'] + 
                            glob(os.path.join('config', '*.xml'))+
                            glob(os.path.join('config', '*.txt')) +
                            glob(os.path.join('config', '*.dmp'))), 
               (icons_dir, glob(os.path.join('share', 'icons', '*.ico')))]

# Add i18n files to data_files list
os.path.walk(locale_dir, mo_find, data_files)



#########################################################################################
# Distutils subclasses

class umit_install(install):
    def run(self):
        check_dependencies()
        
        install.run(self)

        self.create_uninstaller()
        self.adequate_umit_conf()
        self.adequate_paths()

        self.finish_banner()

    def create_uninstaller(self):
        uninstaller_filename = os.path.join(self.install_scripts, "uninstall_umit")
        uninstaller = """#!/usr/bin/env python
import os, sys

print
print '%(line)s Uninstall Umit %(version)s %(line)s'
print

answer = raw_input('Are you sure that you want to completly uninstall Umit %(version)s? \
(yes/no) ')

if answer != 'yes' and answer != 'y':
    sys.exit(0)

print
print '%(line)s Uninstalling Umit %(version)s... %(line)s'
print
""" % {'version':umit_version(), 'line':'-'*10}

        for output in self.get_outputs():
            uninstaller += "print 'Removing %s...'\n" % output
            uninstaller += "os.remove('%s')\n" % output

        uninstaller += "print 'Removing uninstaller itself...'\n"
        uninstaller += "os.remove('%s')\n" % uninstaller_filename

        uninstaller_file = open(uninstaller_filename, 'w')
        uninstaller_file.write(uninstaller)
        uninstaller_file.close()

        # Set exec bit for uninstaller
        mode = ((os.stat(uninstaller_filename)[ST_MODE]) | 0555) & 07777
        os.chmod(uninstaller_filename, mode)

    def adequate_umit_conf(self):
        install_config_dir = os.path.join(self.install_data, config_dir)
        
        config = dict(config_file = os.path.join(install_config_dir, 'umit.conf'),
                      scan_profile = os.path.join(install_config_dir, 'scan_profile.usp'),
                      wizard = os.path.join(install_config_dir, 'wizard.xml'),
                      pixmaps_dir = os.path.join(self.install_data, pixmaps_dir),
                      profile_editor = os.path.join(install_config_dir, 'profile_editor.xml'),
                      options = os.path.join(install_config_dir, 'options.xml'),
                      i18n_dir = os.path.join(self.install_data, locale_dir),
                      umit_op = self.get_file("umit.op"),
                      umit_opi = self.get_file("umit.opi"),
                      umit_opt = self.get_file("umit.opt"),
                      umit_opf = self.get_file("umit.opf"),
                      services_dump = self.get_file("services.dmp"),
                      os_dump = self.get_file("os_db.dmp"),
                      umit_version = self.get_file("umit_version"),
                      os_classification = self.get_file("os_classification.dmp"),
                      umit_icon = self.get_file("umit_48.ico"))

        umit_conf_file = open(config['config_file'], 'r')
        umit_conf = umit_conf_file.read()
        umit_conf_file.close()

        # Putting the paths informations inside umit.conf
        umit_conf %= config
        
        umit_conf_file = open(config['config_file'], 'w')
        umit_conf_file.write(umit_conf)
        umit_conf_file.close()

    def adequate_paths(self):
        paths_file = self.get_file("Paths.py")
        umit_conf = self.get_file("umit.conf")
        umit_conf_dir = os.path.split(umit_conf)[0]

        if not paths_file or not umit_conf:
            print "Error while trying to adequate Umit configurations! Aborting..."
            sys.exit(1)

        paths_content = open(paths_file, 'r').read()
        paths_content = re.sub('umit_conf_dir = ".*"',
                               'umit_conf_dir = "%s"' % umit_conf_dir, paths_content)

        open(paths_file, 'w').write(paths_content)

    def get_file(self, filename):
        for output in self.get_outputs():
            if re.findall(".*[\\/]%s" % (re.escape(filename)), output):
                return output

    def finish_banner(self):
        print 
        print "%s Thanks for using Umit %s %s" % ("#"*10, umit_version(), "#"*10)
        print


class umit_sdist(sdist):
    def run(self):
        # Update content that is going to the packages
        os.system("python utils/add_splash_version.py") # Add version number to splash image
        os.system("python utils/create_os_list.py") # Update/Create dumped os list
        os.system("python utils/create_services_dump.py") # Update/Create dumped services list
        os.system("python utils/generate_classification.py") # Update/Create os_classification
        os.system("bash utils/remove_unused_files.sh") # Remove some unused files

        sdist.run(self)

        self.finish_banner()

    def finish_banner(self):
        print 
        print "%s The packages for Umit %s are in ./dist %s" % ("#"*10, umit_version(), "#"*10)
        print


class umit_py2exe(build_exe):
    def run(self):
        check_dependencies()

        # Make a backup of Paths, and then, adequate it for compilation process
        self.backup_paths()
        self.adequate_paths()

        build_exe.run(self)

        # Adequate installed umit.conf
        self.adequate_umit_conf()
        self.get_paths_back()
    
        self.finish_banner()

    def adequate_umit_conf(self):
        install_config_dir = os.path.join("config", "umit")
        install_pixmaps_dir = os.path.join("share", "pixmaps", "umit")
        install_icon_dir = os.path.join("share", "icons", "umit")
        install_i18n_dir = os.path.join("share", "locale")

        config = dict(config_file = os.path.join(install_config_dir, 'umit.conf'),
                      scan_profile = os.path.join(install_config_dir, 'scan_profile.usp'),
                      wizard = os.path.join(install_config_dir, 'wizard.xml'),
                      pixmaps_dir = install_pixmaps_dir,
                      profile_editor = os.path.join(install_config_dir, 'profile_editor.xml'),
                      options = os.path.join(install_config_dir, 'options.xml'),
                      i18n_dir = install_i18n_dir,
                      umit_op = os.path.join(install_pixmaps_dir, "umit.op"),
                      umit_opi = os.path.join(install_pixmaps_dir, "umit.opi"),
                      umit_opt = os.path.join(install_pixmaps_dir, "umit.opt"),
                      umit_opf = os.path.join(install_pixmaps_dir, "umit.opf"),
                      umitdb = os.path.join(install_config_dir, "umit.db"),
                      services_dump = os.path.join(install_config_dir, "services.dmp"),
                      os_dump = os.path.join(install_config_dir, "os_db.dmp"),
                      umit_version = os.path.join(install_config_dir, "umit_version"),
                      os_classification = os.path.join(install_config_dir, "os_classification.dmp"),
                      umit_icon = os.path.join(install_icon_dir, "umit_48.ico"))

        umit_conf_file = open(dist_umit_conf, 'r')
        umit_conf = umit_conf_file.read()
        umit_conf_file.close()

        umit_conf %= config
        umit_conf_file = open(dist_umit_conf, 'w')
        umit_conf_file.write(umit_conf)
        umit_conf_file.close()

    def adequate_paths(self):
        paths_content = open(paths_file, 'r').read()
        paths_content = re.sub('umit_conf_dir = "config"', 
                               'umit_conf_dir = "%s"' % os.path.join("config", "umit"), paths_content)

        open(paths_file, 'w').write(paths_content)

    def backup_paths(self):
        try: os.remove(backup_paths_file)
        except: pass

        copy_file(paths_file, backup_paths_file)

    def get_paths_back(self):
        try: os.remove(paths_file)
        except: pass

        copy_file(backup_paths_file, paths_file)

    def finish_banner(self):
        print 
        print "%s The compiled version of Umit %s is in ./dist %s" % ("#"*10, umit_version(), "#"*10)
        print


##################### Umit banner ########################
print
print "%s Umit %s %s" % ("#"*10, umit_version(), "#"*10)
print
##########################################################

setup(name = 'umit',
      license = 'GNU GPL (version 2 or later)',
      url = 'http://umit.sourceforge.net',
      download_url = 'http://sourceforge.net/project/showfiles.php?group_id=142490',
      author = 'Adriano Monteiro & Cleber Rodrigues',
      author_email = 'py.adriano@gmail.com, cleber@globalred.com.br',
      maintainer = 'Adriano Monteiro',
      maintainer_email = 'py.adriano@gmail.com',
      description = """UMIT is a nmap frontend, developed in Python and GTK and was \
started with the sponsoring of Google's Summer of Code.""",
      long_description = """The project goal is to develop a nmap frontend that \
is really useful for advanced users and easy to be used by newbies. With UMIT, a network admin \
could create scan profiles for faster and easier network scanning or even compare \
scan results to easily see any changes. A regular user will also be able to construct \
powerful scans with UMIT command creator wizards.""",
      version = umit_version(),
      scripts = ['umit'],
      packages = ['', 'umitCore', 'umitGUI', 'higwidgets'],
      data_files = data_files,
      cmdclass = {"install":umit_install,
                  "sdist":umit_sdist,
                  "py2exe":umit_py2exe},
      windows = [{"script" : "umit",
                  "icon_resources" : [(1, os.path.join("share", "icons", "umit_48.ico"))]}],
      options = {"py2exe":{"compressed":1,
                           "optimize":2,
                           "packages":"encodings",
                           "includes" : "pango,atk,gobject,pickle,bz2,encodings,\
encodings.*,cairo,pangocairo,atk,psyco,pysqlite2"}})