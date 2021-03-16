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
from enigma import eServiceReference, eTimer, getDesktop
from Screens.InfoBar import InfoBar, MoviePlayer
from threading import Timer
import subprocess, gettext, os, re, json, urllib, urllib2 as urlreq, time, ssl

# Set default configuration
config.plugins.torrserver = ConfigSubsection()
config.plugins.torrserver.autostart = ConfigOnOff(default=False)
serv_url = 'http://127.0.0.1:8090/'
torr_path = '/usr/bin/TorrServer'
repolist = 'https://raw.githubusercontent.com/satsis/TorrServer-armv7ahf-vfp/main/release.json'
version = '0.5'

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("TorrSettings", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/TorrServer/locale/"))

class TorrPlayer(MoviePlayer):
	def __init__(self, session, service):
		MoviePlayer.__init__(self, session, service)
		self.started = False

def _(txt):
	t = gettext.dgettext("TorrSettings", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

def pluginversion():
	return version
	
def get_pid(name):
	try:
		return subprocess.check_output(["pidof",name])
	except subprocess.CalledProcessError:
		return False
		
def get_version():
	try:
		url = serv_url + 'echo'
		req = urlreq.Request(url)
		html = urlreq.urlopen(req).read()
		r1 = html.strip()
		return r1
	except urlreq.URLError:
		return False

def post_json(url, values = ''):
	try:
		data = json.dumps(values)
		req = urlreq.Request(url, data)
		response = urlreq.urlopen(req)
		the_page = response.read()
		dictData = json.loads(the_page)
		return dictData
	except urlreq.URLError:
		return False

def get_url(url, values = ''):
	try:
		data = urllib.urlencode(values)
		if values != '':
			req = urlreq.Request(url + "?" + data)
		else:
			req = urlreq.Request(url)
		context = ssl._create_unverified_context()
		resp = urlreq.urlopen(req, context=context)
		return resp.read()
	except urlreq.URLError:
		self['statusbar'].setText(urlreq.URLError)
		return False

def install_torr():
	arch = subprocess.check_output('uname -m; exit 0', shell=True)
	arch = arch.strip()
	repo_json = get_url(repolist)
	repo_json = json.loads(repo_json)
	if repo_json != False:
		for item in repo_json:
			if arch == 'armv7l':
				url = str(item['Links']['linux-arm7'])
			elif (arch == 'mips'):
				url = str(item['Links']['linux-mipsle'])
			else:
				self['statusbar'].setText(_('No version TorrServer!'))
				return False
	try:
		with open(torr_path,'wb') as f:
			req = urlreq.Request(url)
			context = ssl._create_unverified_context()
			f.write(urlreq.urlopen(req, context=context).read())
			f.close()
			time.sleep(0.5)
			subprocess.call(['chmod', '0755', torr_path])
		return True
	except urlreq.HTTPError, e:
		print 'We failed with error code - %s.' % e.code
		if e.code == 404:
			os.remove(torr_path)
			return '404 not found'
		else:
			os.remove(torr_path)
			return e.code
	except urlreq.URLError:
		self['statusbar'].setText(urlreq.URLError)
		return False

class TorrSettings(Screen):
	def __init__(self, session):
		self.skin = self.setSkin()
		print self.skin
		Screen.__init__(self, session)
		self.setTitle(_("Plugin TorrServer Enigma2 version %s" % pluginversion()))
		self["title"] = Label()
		self["key_red"] = Label(_("Install"))
		self["key_green"] = Label(_("Start"))
		self["key_yellow"] = Label(_("Info"))
		self["key_blue"] = Label(_())
		self["statusbar"] = Label()
		self['statusserver'] = Label()
		menulist = []
		self["menu"] = List(menulist)
		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
			{
			"cancel": self.cancel,
			"back": self.cancel,
			"red": self.install_update,
			"green": self.start_stop,
			"yellow": self.info,
			"blue": self.autostart,
			"ok": self.action,
			})
		self.createList()
		self.get_status()
		self.timer = eTimer()
		self.timer.callback.append(self.createList)
		self.timer.callback.append(self.get_status)
		self.timer.start(5000, False)
		self.onClose.append(self.timer.stop)

	def setSkin(self):
		try:
			screenWidth = getDesktop(0).size().width()
		except:
			screenWidth = 720
		if screenWidth >= 1280:
			with open('/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/skins/main.xml', 'r') as f:
				skin = f.read()
				return skin
		else:
			print '1280'
			with open('/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/skins/main.xml', 'r') as f:
				skin = f.read()
				return skin

	def createList(self):
		menulist = []
		url = serv_url + 'torrents'
		values = {'action': "list"}
		dictData = post_json(url, values)
		if dictData != False:
			for item in dictData:
				torname = str(item.get('title'))
				if not torname:
					torname = str(item['name'])
				torplay = str(serv_url + 'stream/?link=' + item['hash'] + '&index=1&play')
				menulist.append((torname, torplay))
			self["menu"].updateList(menulist)
	
	def get_status(self):
		if os.path.isfile(torr_path) == False:
			self['statusbar'].setText(_('TorrServer is') + " " + _('not installed :('))
			self["key_red"].setText(_("Install"))
		elif (get_pid("TorrServer")):
			version = get_version()
			self['statusbar'].setText(_('TorrServer is') + " " + _('running') + " " + _('version') + " " +  version)
			self["key_red"].setText(_("Check updates"))
			self["key_green"].setText(_("Stop"))
		else:
			self['statusbar'].setText(_('TorrServer is') + " " + _('down :('))
			self["key_red"].setText(_("Check updates"))
			self["key_green"].setText(_("Start"))

	def cancel(self):
		self.close()

	def action(self, currentSelect = None):
		if currentSelect is None:
			currentSelect = str(self["menu"].getCurrent()[1])
			self.hide()
			sref = eServiceReference(4097, 0, currentSelect)
			self.session.open(TorrPlayer, sref)
			#self.session.nav.playService(sref)

	def start_stop(self):
		if get_pid("TorrServer") == False:
			fh = open(os.devnull, 'wb')
			os.system('export GODEBUG=madvdontneed=1')
			p = subprocess.Popen(['/usr/bin/TorrServer'], shell=False, stdout = fh, stderr = fh)
			fh.close()		
			time.sleep(0.5)
			menulist = []
			self.createList()
			self.timer = eTimer()
			self.timer.callback.append(self.createList)
			self.timer.callback.append(self.get_status)
			self.timer.start(5000, False)
		else:
			os.system("killall TorrServer")
			time.sleep(0.5)
			self.timer.stop()
		self.get_status()
		self.onClose.append(self.timer.stop)

	def info(self):
		self['statusbar'].setText(_('TorrServer is %s') % (_('running') if get_pid('TorrServer') else _('down :(')))

	def autostart(self):
		if config.plugins.torrserver.autostart.value == False:
			config.plugins.torrserver.autostart.value = True
			self['statusbar'].setText(_("Run on starup is") + " " + _("ON"))
			self["key_blue"].setText(_("Autostart is") + " " + _("ON"))
		else:
			config.plugins.torrserver.autostart.value = False
			self['statusbar'].setText(_("Run on starup is") + " " + _("OFF"))
			self["key_blue"].setText(_("Autostart is") + " " + _("OFF"))
		config.plugins.torrserver.autostart.save()

	def install_update(self):
		if os.path.isfile(torr_path) == False:
			res = install_torr()
			if res == True:
				self["key_red"].setText(_("Check updates"))
				self['statusbar'].setText(_('TorrServer is') + " " + _('installed :)'))
		else:
			self['statusbar'].setText(_('TorrServer is') + " " + _('installed :)'))

def autoStart(reason, **kwargs): # starts DURING the Enigma2 booting
	if config.plugins.torrserver.autostart.value == True and get_pid("TorrServer") == False and os.path.isfile(torr_path) == True:
		fh = open("NUL","w")
		os.system('export GODEBUG=madvdontneed=1')
		p = subprocess.Popen(['/usr/bin/TorrServer'], shell=False, stdout = fh, stderr = fh)
		fh.close()

def main(session, **kwargs):
	session.open(TorrSettings)

def Plugins(path, **kwargs):
	return [
		PluginDescriptor(
			where = PluginDescriptor.WHERE_AUTOSTART, fnc = autoStart),
		PluginDescriptor(
			name = _("TorrServer runner"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "plugin.png", description = _("Plugin for run TorrServer"), fnc = main)
	]
