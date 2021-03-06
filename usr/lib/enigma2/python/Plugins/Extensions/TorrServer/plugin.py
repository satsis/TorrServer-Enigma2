from Screens.Screen import Screen
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Components.Label import Label
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from Screens.MessageBox import MessageBox
from Components.Language import language
from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigOnOff, ConfigText, ConfigSubsection
from os import environ, system
from Screens.Console import Console
import subprocess
import gettext
import os

# Set default configuration
config.plugins.torrserver = ConfigSubsection()
config.plugins.torrserver.autostart = ConfigOnOff(default=False)

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("TorrSettings", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/TorrServer/locale/"))

def _(txt):
   t = gettext.dgettext("TorrSettings", txt)
   if t == txt:
      t = gettext.gettext(txt)
   return t

def get_pid(name):
    try:
        return subprocess.check_output(["pidof",name])
    except subprocess.CalledProcessError:
        return False

class TorrSettings(Screen):
   def __init__(self, session):
      with open('/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/skins/main.xml', 'r') as f:
        self.skin = f.read()
      Screen.__init__(self, session)
      self.setTitle(_("Plugin for run TorrServer"))
      self["key_red"] = Label(_("Close"))
      self["key_green"] = Label(_("Start"))
      self["key_yellow"] = Label(_("Stop"))
      self["key_blue"] = Label(_("AutoStart"))
      self['statusserver'] = Label()
      self['statusautostart'] = Label()
      self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
      {
         "cancel": self.cancel,
         "back": self.cancel,
         "red": self.cancel,
         "green": self.start,
         "yellow": self.stop,
         "blue": self.autostart,
         })
      if config.plugins.torrserver.autostart.value == True:
          self['statusautostart'].setText(_('Run on starup is ON'))
      else:
          self['statusautostart'].setText(_('Run on starup is OFF'))
      statusserver = get_pid("TorrServer-linux-arm7")
      self['statusserver'].setText(statusserver)
      if get_pid("TorrServer-linux-arm7") != False:
          self['statusserver'].setText(_('TorrServer is running'))
      else:
          self['statusserver'].setText(_('TorrServer is down :('))

   def cancel(self):
      self.close()

   def start(self):
      if get_pid("TorrServer-linux-arm7") == False:
          fh = open("NUL","w")
          p = subprocess.Popen(['/usr/bin/TorrServer-linux-arm7'], shell=False, stdout = fh, stderr = fh)
          fh.close()
          if get_pid("TorrServer-linux-arm7") != False:
              self['statusserver'].setText(_('TorrServer is running'))
          else:
              self['statusserver'].setText(_('TorrServer is down :('))

   def stop(self):
      os.system("killall TorrServer-linux-arm7")
      if get_pid("TorrServer-linux-arm7") != False:
          self['statusserver'].setText(_('TorrServer is running'))
      else:
          self['statusserver'].setText(_('TorrServer is down :('))

   def autostart(self):
      if config.plugins.torrserver.autostart.value == False:
          config.plugins.torrserver.autostart.value = True
          self['statusautostart'].setText(_('Run on starup is ON'))
      else:
          config.plugins.torrserver.autostart.value = False
          self['statusautostart'].setText(_('Run on starup is OFF'))
      config.plugins.torrserver.autostart.save()

def autoStart(reason, **kwargs): # starts DURING the Enigma2 booting
    if config.plugins.torrserver.autostart.value == True and get_pid("TorrServer-linux-arm7") == False:
        fh = open("NUL","w")
        p = subprocess.Popen(['/usr/bin/TorrServer-linux-arm7'], shell=False, stdout = fh, stderr = fh)
        fh.close()
        with open("/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/log.txt","a") as f:
            f.write("reason = %s, config.plugins.torrserver.autostart.value = %s \n" % (reason, config.plugins.torrserver.autostart.value))

def main(session, **kwargs):
   session.open(TorrSettings)

def Plugins(path, **kwargs):
    return [
      PluginDescriptor(
            where = PluginDescriptor.WHERE_AUTOSTART, fnc = autoStart),
      PluginDescriptor(
            name = _("TorrServer runner"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "plugin.png", description = _("Plugin for run TorrServer"), fnc = main)
    ]
