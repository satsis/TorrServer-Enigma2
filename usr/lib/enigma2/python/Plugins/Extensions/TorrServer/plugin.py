# -*- coding: utf-8 -*-
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
from enigma import eServiceReference, eTimer, getDesktop, ePixmap, ePicLoad
from Screens.InfoBar import InfoBar, MoviePlayer
from threading import Timer
from Components.Pixmap import Pixmap
from time import gmtime
from urllib import quote, urlencode
from urllib2 import urlopen, Request
from Components.AVSwitch import AVSwitch
import subprocess, gettext, os, re, json, urllib, urllib2 as urlreq, time, ssl, tempfile

# Set default configuration
config.plugins.torrserver = ConfigSubsection()
config.plugins.torrserver.autostart = ConfigOnOff(default=False)
serv_url = 'http://127.0.0.1:8090/'
torr_path = '/usr/bin/TorrServer'
repolist = 'https://raw.githubusercontent.com/satsis/TorrServer-armv7ahf-vfp/main/release.json'
version = '0.5'
DEBUG = True
temp_dir = tempfile.gettempdir()
log_file = os.path.join(temp_dir, 'poster.log')
timeout = '5'
tmdb_api = '7bff10009e7deed9307ad50c67270b6b'
context = ssl._create_unverified_context()

REGEX = re.compile(
		r'[0-9]+\+|'
		r'([\(\[]).*?([\)\]])|'
		r'\d{1,3}\-я|'
		r'(с|С)ерия|'
		r'\d{1,3}\s(с|C)\-н|'
		r'\d{1,3}\sс|'
		r'(с|С)езон\s\d{1,3}|'
		r'(с|С)езон|'
		r'(х|Х)/ф|'
		r'(м|М)/ф|'
		r'(т|Т)/с|'
		r'(ч|Ч)асть|'
		r'(\s\-(.*?).*)|'
		r'[\\/\(]|', re.DOTALL)
		

HEADERS = {
	'User-Agent': 'Magic Browser',
	'Accept-encoding': 'gzip, deflate',
	'Connection': 'close',
	}

getRespData = lambda resp: {
			'deflate': lambda: zlib.decompress(resp.read(), -zlib.MAX_WBITS),
			'gzip'   : lambda: zlib.decompress(resp.read(), zlib.MAX_WBITS|16),
			}.get(resp.info().get('Content-Encoding'), lambda: resp.read())()
	
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

def write_log(value):
	with open(log_file, 'a') as f:
		f.write('%s\n' % value)	
	
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
		self["original_title"] = Label()
		self["overview"] = Label()
		self["vote_average"] = Label()
		self["vote_count"] = Label()
		self["key_red"] = Label(_("Install"))
		self["key_green"] = Label(_("Start"))
		self["key_yellow"] = Label(_("Info"))
		self["key_blue"] = Label()
		self['key_blue'].setText(_('Autostart is %s') % (_('ON') if config.plugins.torrserver.autostart.value else _('OFF')))
		self["statusbar"] = Label()
		self['statusserver'] = Label()
		self["poster"] = Pixmap()
		menulist = []
		self["menu"] = List(menulist)
		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions", "DirectionActions"],
			{
			"cancel": self.cancel,
			"back": self.cancel,
			"red": self.install_update,
			"green": self.start_stop,
			"yellow": self.info,
			"blue": self.autostart,
			"ok": self.action,
			"downUp": self.cross,
			"upUp": self.cross,
			})
		self.createList()
		self.get_status()
		self.timer = eTimer()
		self.ftimer = eTimer()
		self.timer.callback.append(self.createList)
		self.timer.callback.append(self.get_status)
		self.ftimer.callback.append(self.firstposter)
		self.timer.start(5000, False)
		self.ftimer.start(1000, True)
		self.onClose.append(self.timer.stop)
		
	def firstposter(self):
		if get_pid("TorrServer"):
			self.evntNm = str(self["menu"].getCurrent()[0])
			if DEBUG: write_log('first: %s' % self.evntNm)
			self.showPoster()

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
	
	def cross(self):
		if get_pid("TorrServer"):
			self.evntNm = str(self["menu"].getCurrent()[0])
			if DEBUG: write_log('cross menu: %s' % self.evntNm)
			self.showPoster()
	
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
			self.ftimer.start(1000, True)
		else:
			os.system("killall TorrServer")
			time.sleep(0.5)
			self.timer.stop()
		self.get_status()
		self.onClose.append(self.timer.stop)

	def info(self):
		self['statusbar'].setText('TorrServer plugin from maxya (satsis.info). Thanks Dorik1972')
		
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

	def getPoster(self):
		self.year = self.filterSearch()
		self.filtername()
		self.evntNm = REGEX.sub('', self.evntNm).strip()
		self.evntNm = self.evntNm.replace(".", " ").strip()
		self.evntNm = re.sub(" +", " ", self.evntNm)
		temp_json = temp_dir + '/' + self.evntNm
		try:
			if DEBUG: write_log('temp_json: %s' % temp_json)
			if DEBUG: write_log('temp_json is: %s' % os.path.isfile(temp_json))
			if os.path.isfile(temp_json) == True:
				if DEBUG: write_log('Parsed TITLE: "%s"' % self.evntNm)
				jf = open(temp_json)
				data = json.loads(jf.read())
			else:
				if DEBUG: write_log('Parsed TITLE: "%s"' % self.evntNm)
				if DEBUG: write_log('Try to get info from JSON')
				params = {
					'api_key': tmdb_api,
					'query': self.evntNm,
					'region': 'RU',
					'language': 'ru-RU',
					'include_adult': 1,
					}
				
				if self.year:
					if DEBUG: write_log('year: %s' % self.year)
					# params.update({
						# 'primary_release_year': self.year,
						# })

				url = 'https://api.themoviedb.org/3/search/multi'

				data = get_url(url, params)
				with open(temp_json,'wb') as f:
					f.write(data)
					f.close()
				data = json.loads(data)

			if data.get('results'):
				pfname = data['results'][0]['poster_path']
				if pfname:
					self.tempfile = temp_dir + pfname
					self.downloadPoster('https://image.tmdb.org/t/p/w300%s' % pfname, self.tempfile)
					if DEBUG: write_log(json.dumps(pfname[1:], indent=4, sort_keys=True))
				if "title" in data['results'][0]:
					self['title'].setText(str(data['results'][0]['title']))
					if DEBUG: write_log('title: %s' % data['results'][0]['title'])
				else:
					self['title'].setText(str(data['results'][0]['name']))
					if DEBUG: write_log('name: %s' % data['results'][0]['name'])
				if "original_title" in data['results'][0]:
					self['original_title'].setText(str(data['results'][0]['original_title']))
				else:
					self['original_title'].setText(str(data['results'][0]['original_name']))
				self['overview'].setText(str(data['results'][0]['overview']))
				self['vote_average'].setText(str(data['results'][0]['vote_average']))
				self['vote_count'].setText(str(data['results'][0]['vote_count']))
			else:
				self.tempfile = '/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/poster_none.png'
				self['title'].setText(self.evntNm)
				self['original_title'].setText('')
				self['overview'].setText('')
				self['vote_average'].setText('')
				self['vote_count'].setText('')

		except Exception as e:
			if DEBUG:
				write_log('An error occurred while processing JSON request: %s' % repr(e))

	def showPoster(self):
		self.getPoster()
		self.picload = ePicLoad()
		self['poster'].instance.setPixmap(None)
		self['poster'].hide()
		jpg_file = str(self.tempfile)
		#jpg_file = '/tmp/xn0z7kZ4DLOoNeDNrvCrsDAvm8y.jpg'
		size = self["poster"].instance.size()
		if DEBUG: write_log('size: %s' % size.height())
		scale = AVSwitch().getFramebufferScale()
		#0=Width 1=Height 2=Aspect 3=use_cache 4=resize_type 5=Background(#AARRGGBB)
		self.picload.setPara((size.width(), size.height(), scale[0], scale[1], False, 1, '#00000000'))
		self.picload.startDecode(jpg_file, 0, 0, False)
		ptr = self.picload.getData()
		if ptr:
			self["poster"].instance.setPixmap(ptr)
			if DEBUG: write_log('ptr: YES')
			self["poster"].show()

	def downloadPoster(self, url, tempfile):
		if os.path.isfile(tempfile) == False:
			if DEBUG: write_log('Try download poster')
			try:
				with open(tempfile,'wb') as f:
					req = urlreq.Request(url)
					f.write(urlreq.urlopen(req, context=context).read())
					f.close()
				return True
			except urlreq.HTTPError, e:
				print 'We failed with error code - %s.' % e.code
				if e.code == 404:
					os.remove(tempfile)
					return '404 not found'
				else:
					os.remove(tempfile)
					return e.code
			except urlreq.URLError:
				self['statusbar'].setText(urlreq.URLError)
				return False
				
	def filterSearch(self):
		sd = self.evntNm
		try:
			yr = [ _y for _y in re.findall(r'\d{4}', sd) if '1930' <= _y <= '%s' % gmtime().tm_year ]
			return '%s' % yr[-1] if yr else ''
		except:
			return ''
			
	def filtername(self):
		sd = self.evntNm
		try:
			yr = [ _y for _y in re.findall(r'\d{4}', sd) if '1930' <= _y <= '%s' % gmtime().tm_year ]
			parts = sd.split(yr[0], -1)
			res = parts[0]
		except:
			res = sd

		try:
			dig = [ _y for _y in re.findall(r'[\\/]', res) ]
			parts = sd.split(dig[0], -1)
			res2 = parts[0]
		except:
			res2 = res
			
		try:
			dig = [ _y for _y in re.findall(r'\d{4}p', res2) ]
			parts = sd.split(dig[0], -1)
			self.evntNm = parts[0]
		except:
			self.evntNm = res2
			
		return self.evntNm

def autoStart(reason, **kwargs): # starts DURING the Enigma2 booting
	if config.plugins.torrserver.autostart.value == True and get_pid("TorrServer") == False and os.path.isfile(torr_path) == True:
		fh = open(os.devnull, 'wb')
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
