# -*- coding: utf-8 -*-
from . import _
from Components.AVSwitch import AVSwitch
from Components.ProgressBar import ProgressBar
from Components.Sources.List import List
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Language import language
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigOnOff, ConfigText, ConfigSubsection, ConfigSelection,  getConfigListEntry
from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console
from enigma import eServiceReference, eTimer, getDesktop, ePixmap, ePicLoad, iPlayableService
from Screens.InfoBar import InfoBar, MoviePlayer
from Screens.Screen import Screen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ, system
from threading import Timer
from time import gmtime
from urllib import quote, urlencode
from urllib2 import urlopen, Request
import subprocess, gettext, os, re, json, urllib, urllib2 as urlreq, time, ssl, tempfile, traceback

screenWidth = getDesktop(0).size().width()

skin_fhd = """
  <screen name="TorrMenu" position="135,135" size="1650,855" title="TorrServer Enigma2">
	<eLabel backgroundColor="#ffffff" position="0,0" size="1650,3" />
	<widget font="Regular;33" foregroundColor="#ffff00" name="title" halign="center" position="30,30" size="550,35" transparent="1" valign="center" />
	<widget font="Regular;27" foregroundColor="#4f7942" name="statusbar" position="15,735" size="1620,30" transparent="1" />
	<eLabel backgroundColor="#ffffff" position="0,780" size="1650,3" />
	<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_red.png" position="30,810" size="20,20" zPosition="1" />
	<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_green.png" position="455,810" size="20,20" zPosition="1" />
	<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_yellow.png" position="840,810" size="20,20" zPosition="1" />
	<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_blue.png" position="1245,810" size="20,20" zPosition="1" />
	<widget backgroundColor="#9f1313" font="Regular;30" foregroundColor="#00ff2525" halign="left" name="key_red" position="55,792" size="400,57" transparent="1" valign="center" zPosition="2" />
	<widget backgroundColor="#1f771f" font="Regular;30" foregroundColor="#00389416" halign="left" name="key_green" position="480,792" size="375,57" transparent="1" valign="center" zPosition="2" />
	<widget backgroundColor="#a08500" font="Regular;30" foregroundColor="#00bab329" halign="left" name="key_yellow" position="875,792" size="375,57" transparent="1" valign="center" zPosition="2" />
	<widget backgroundColor="#18188b" font="Regular;30" foregroundColor="#006565ff" halign="left" name="key_blue" position="1270,792" size="375,57" transparent="1" valign="center" zPosition="2" />
	<widget name="poster" position="150,90" size="300,450" zPosition="2" alphatest="blend"/>
	<widget font="Regular;27" foregroundColor="#ffffff" name="original_title" halign="center" position="30,540" size="500,30" transparent="1" valign="center" />
	<widget name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/starsbar_empty.png" halign="center" position="185,570" size="210,21" alphatest="blend"  transparent="1" zPosition="2" />
	<widget name="stars" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/starsbar_filled.png" halign="center" position="185,570"  size="210,21" transparent="1" zPosition="3" />
	<widget font="Regular;27" foregroundColor="#ffffff" name="vote_average" halign="center" position="30,600" size="500,30" transparent="1" valign="center" />
	<widget font="Regular;27" foregroundColor="#ffffff" name="overview" position="30,640" size="1600,90" transparent="1" valign="center" />
    <widget source="menu" render="Listbox" position="600,25" size="1050,580" scrollbarMode="showOnDemand" transparent="1">
		<convert type="TemplatedMultiContent">
		  {"template": [
			MultiContentEntryText(pos = (15, 5), size = (1050, 580), font=0, flags = RT_HALIGN_LEFT, text = 0)
			],
			"fonts": [gFont("Regular", 23)],
			"itemHeight": 40
		  }
		</convert>
	</widget>
  </screen>"""
skin_hd = """
  <screen name="TorrMenu" position="90,90" size="1100,570">
	<eLabel backgroundColor="#ffffff" position="0,0" size="1100,2" />
	<widget font="Regular;22" foregroundColor="#ffff00" name="title" position="20,20" size="335,24" transparent="1" valign="center" />
	<widget font="Regular;18" foregroundColor="#4f7942" name="statusbar" position="10,490" size="1080,20" transparent="1" />
	<eLabel backgroundColor="#ffffff" position="0,520" size="1100,2" />
	<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_red.png" position="15,540" size="20,20" zPosition="1" />
	<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_green.png" position="285,540" size="20,20" zPosition="1" />
	<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_yellow.png" position="555,540" size="20,20" zPosition="1" />
	<ePixmap alphatest="on" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_blue.png" position="825,540" size="20,20" zPosition="1" />
	<widget backgroundColor="#9f1313" font="Regular;20" foregroundColor="#00ff2525" halign="left" name="key_red" position="40,530" size="400,38" transparent="1" valign="center" zPosition="2" />
	<widget backgroundColor="#1f771f" font="Regular;20" foregroundColor="#00389416" halign="left" name="key_green" position="310,530" size="375,38" transparent="1" valign="center" zPosition="2" />
	<widget backgroundColor="#a08500" font="Regular;20" foregroundColor="#00bab329" halign="left" name="key_yellow" position="580,530" size="375,38" transparent="1" valign="center" zPosition="2" />
	<widget backgroundColor="#18188b" font="Regular;20" foregroundColor="#006565ff" halign="left" name="key_blue" position="850,530" size="375,38" transparent="1" valign="center" zPosition="2" />
	<widget name="poster" position="80,60" size="200,300" zPosition="2" alphatest="blend"/>
	<widget font="Regular;18" foregroundColor="#ffffff" name="original_title" position="20,360" size="335,20" transparent="1" valign="center" />
	<widget font="Regular;18" foregroundColor="#ffffff" name="vote_average" position="20,400" size="335,20" transparent="1" valign="center" />
	<widget name="starsbg" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/starsbar_empty.png" halign="center" position="20,380" size="210,21" alphatest="blend"  transparent="1" zPosition="2" />
	<widget name="stars" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/starsbar_filled.png" halign="center" position="20,380"  size="210,21" transparent="1" zPosition="3" />
	<widget font="Regular;18" foregroundColor="#ffffff" name="overview" position="20,420" size="1030,60" transparent="1" valign="center" />
    <widget source="menu" render="Listbox" position="350,17" size="700,385" scrollbarMode="showOnDemand" transparent="1">
		<convert type="TemplatedMultiContent">
		  {"template": [
			MultiContentEntryText(pos = (10, 4), size = (700, 30), font=0, flags = RT_HALIGN_LEFT, text = 0)
			],
			"fonts": [gFont("Regular", 20)],
			"itemHeight": 30
		  }
		</convert>
	</widget>
  </screen>"""

skinConf_hd = """
    <screen name="TorrConf" position="center,center" size="660,400" >
	  <widget name="statusbar" font="Regular;18" foregroundColor="#4f7942" position="15,340" size="630,20" halign="center" transparent="1" />
      <widget name="config" position="10,10" size="640,300" scrollbarMode="showOnDemand" transparent="1" />
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_red.png" position="80,370" size="20,20" transparent="1" alphatest="blend" />
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_green.png" position="240,370" size="20,20" transparent="1" alphatest="blend" />
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_blue.png" position="400,370" size="20,20" transparent="1" alphatest="blend" />
      <widget name="key_red" position="110,370" zPosition="5" size="160,25" font="Regular;18" valign="center" halign="left" transparent="1" shadowColor="black" />
      <widget name="key_green" position="270,370" zPosition="5" size="160,25" font="Regular;18" valign="center" halign="left" transparent="1" shadowColor="black" />
      <widget name="key_blue" position="430,370" zPosition="5" size="160,25" font="Regular;18" valign="center" halign="left" transparent="1" shadowColor="black" />
    </screen>"""
skinConf_fhd = """
    <screen name="TorrConf" position="center,center" size="900,600" >
	  <widget name="statusbar" font="Regular;25" foregroundColor="#4f7942" position="15,520" size="870,30" halign="center" transparent="1" />
      <widget name="config" position="10,10" size="880,460" itemHeight="35" font="Regular;25" scrollbarMode="showOnDemand" transparent="1" />
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_red.png" position="100,575" size="20,20" transparent="1" alphatest="blend" />
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_green.png" position="330,575" size="20,20" transparent="1" alphatest="blend" />
      <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/key_blue.png" position="560,575" size="20,20" transparent="1" alphatest="blend" />
      <widget name="key_red" position="130,570" zPosition="5" size="160,25" font="Regular;22" valign="center" halign="left" transparent="1" shadowColor="black" />
      <widget name="key_green" position="360,570" zPosition="5" size="160,25" font="Regular;22" valign="center" halign="left" transparent="1" shadowColor="black" />
      <widget name="key_blue" position="590,570" zPosition="5" size="160,25" font="Regular;22" valign="center" halign="left" transparent="1" shadowColor="black" />
    </screen>"""

# Set default configuration
config.plugins.torrserver = ConfigSubsection()
config.plugins.torrserver.autostart = ConfigOnOff(default=False)
config.plugins.torrserver.infobarMode = ConfigSelection(default='file', choices=[
    ('file', _('Name file')), ('title', _('Title')), ('original_title', _('Original Title'))])
config.plugins.torrserver.player = ConfigSelection(default='4097', choices=[
    ('4097', _('Default')), ('5002', _('Exteplayer')), ('5001', _('Gstplayer'))])

serv_url = 'http://127.0.0.1:8090/'
torr_path = '/usr/bin/TorrServer'
repolist = 'https://releases.yourok.ru/torr/server_release.json'
version = '0.6.0'
DEBUG = False
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
        r'[\\/\(_]|', re.DOTALL)


HEADERS = {
    'User-Agent': 'Magic Browser',
    'Accept-encoding': 'gzip, deflate',
    'Connection': 'close',
    }

getRespData = lambda resp: {
            'deflate': lambda: zlib.decompress(resp.read(), -zlib.MAX_WBITS),
            'gzip'   : lambda: zlib.decompress(resp.read(), zlib.MAX_WBITS|16),
            }.get(resp.info().get('Content-Encoding'), lambda: resp.read())()

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
        ver = subprocess.check_output(torr_path + ' --version', shell=True)
        match = re.match(r'TorrServer (.*)', ver)
        return str(match.group(1).strip())
    except subprocess.CalledProcessError:
        return 'no version'

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

def download_torr(url):
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

class TorrPlayer(MoviePlayer):
    def __init__(self, session, service):
        MoviePlayer.__init__(self, session, service)
        self.skinName = 'MoviePlayer'
        self.servicelist = InfoBar.instance and InfoBar.instance.servicelist
        self.started = False
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
            {
                iPlayableService.evSeekableStatusChanged: self.TorrPlayerseekableStatusChanged
            })

    def TorrPlayerseekableStatusChanged(self):
        service = self.session.nav.getCurrentService()

    def leavePlayerOnExit(self):
        self.is_closing = True
        self.session.openWithCallback(self.leavePlayerOnExitCallback, MessageBox, _("Exit torrent player?"), simple=True)

    def leavePlayer(self):
        self.leavePlayerConfirmed([None, 'quit'])

    def leavePlayerOnExitCallback(self, answer):
        if answer:
            self.leavePlayerConfirmed([None, 'quit'])

    def leavePlayerConfirmed(self, answer):
        if answer and answer[1] == 'quit':
            service = self.session.nav.getCurrentService()
            self.close()
#            self.close(answer)

    def showMovies(self):
        pass

class TorrMenu(Screen):
    def __init__(self, session):
        if screenWidth and screenWidth == 1920:
            self.skin = skin_fhd
        else:
            self.skin = skin_hd
        Screen.__init__(self, session)
        self.setTitle(_("Plugin TorrServer Enigma2 version %s") % pluginversion())
        self["title"] = Label()
        self["original_title"] = Label()
        self["overview"] = Label()
        self["vote_average"] = Label()
        self["key_red"] = Label()
        self["key_green"] = Label(_("Start"))
        self["key_yellow"] = Label(_("Info"))
        self["key_blue"] = Label(_("Settings"))
        self["statusbar"] = Label()
        self["poster"] = Pixmap()
        self["stars"] = ProgressBar()
        self["starsbg"] = Pixmap()
        self["stars"].hide()
        self["starsbg"].hide()
        self.ratingstars = 0
        menulist = []
        self["menu"] = List(menulist)
        self['actions'] = ActionMap(["ShortcutActions", "WizardActions", "DirectionActions"],
            {
            "cancel": self.cancel,
            "back": self.cancel,
            "red": self.cancel,
            "green": self.start_stop,
            "yellow": self.info,
            "blue": self.torrconf,
            "ok": self.action,
            "downUp": self.cross,
            "upUp": self.cross,
            "leftUp": self.cross,
            "rightUp": self.cross,
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
        #if DEBUG: write_log('first: %s' % self.menulist)
        if get_pid("TorrServer") and self.menulist:
            self.evntNm = str(self["menu"].getCurrent()[0])
            if DEBUG: write_log('first yes: %s' % self.evntNm)
            self.showPoster()

    def createList(self):
        self.menulist = []
        url = serv_url + 'torrents'
        values = {'action': "list"}
        dictData = post_json(url, values)
        if dictData != False:
            for item in dictData:
                torname = str(item.get('title'))
                if not torname:
                    torname = str(item.get('name'))
                    if torname == 'None': torname = ''
                torplay = str(serv_url + 'stream/?link=' + item['hash'] + '&index=1&play')
                self.menulist.append((torname, torplay))
            self["menu"].updateList(self.menulist)

    def get_status(self):    
        if os.path.isfile(torr_path) == False:
            self['statusbar'].setText(_('TorrServer is') + " " + _('not installed :('))
        elif (get_pid("TorrServer")):
            version = get_version()
            self['statusbar'].setText(_('TorrServer is') + " " + _('running') + " " + _('version') + " " +  version)
            self["key_green"].setText(_("Stop"))
        else:
            self['statusbar'].setText(_('TorrServer is') + " " + _('down :('))
            self["key_green"].setText(_("Start"))

    def cancel(self):
        self.close(None)

    def action(self, currentSelect = None):
        if currentSelect is None and self.menulist:
            currentSelect = str(self["menu"].getCurrent()[1])
            self.hide()
            service = eServiceReference(int(config.plugins.torrserver.player.value), 0, currentSelect)
            if config.plugins.torrserver.infobarMode.value == 'original_title' and self['original_title'].getText() != "":
                infobarname = self['original_title'].getText()
            elif config.plugins.torrserver.infobarMode.value == 'title' and self['title'].getText() != "":
                infobarname = self['title'].getText()
            else:
                infobarname = self["menu"].getCurrent()[0]
            service.setName(str(infobarname))
            self.session.openWithCallback(self.playCallback, TorrPlayer, service)

    def playCallback(self):
        self.session.open(TorrMenu)
#
#    def torrconf(self):
#        self.session.openWithCallback(self.createList(), TorrConf)


    def cross(self):
        if get_pid("TorrServer") and self.menulist:
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

    def getPoster(self):
        if self.evntNm == '':
            return ''
        self.year = self.filterSearch(str(self.evntNm))
        if DEBUG: write_log('self.year: %s' % self.year)
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

                url = 'https://api.themoviedb.org/3/search/multi'

                data = get_url(url, params)
                with open(temp_json,'wb') as f:
                    f.write(data)
                    f.close()
                data = json.loads(data)

            if data.get('results'):
                json_item = data['results']

                i = k = 0
                exitFlag=False
                for item in json_item:
                    if item['media_type'] == 'movie' or item['media_type'] == 'tv':
                        if "release_date" in item:
                            release_date = self.filterSearch(item['release_date'])
                            if DEBUG: write_log('release_date %s ' % i + 'is %s ' % release_date)
                            if self.year == release_date:
                                k = i
                                if DEBUG: write_log('year=release_date: %s' % release_date)
                                exitFlag=True
                    if(exitFlag):
                        break
                    i += 1

                pfname = str(json_item[k]['poster_path'])
                if pfname:
                    self.tempfile = temp_dir + pfname
                    self.downloadPoster('https://image.tmdb.org/t/p/w300%s' % pfname, self.tempfile)
                    if DEBUG: write_log(json.dumps(pfname[1:], indent=4, sort_keys=True))
                if "title" in json_item[k]:
                    self['title'].setText(str(json_item[k]['title']))
                    if DEBUG: write_log('title: %s' % json_item[k]['title'])
                else:
                    self['title'].setText(str(json_item[k]['name']))
                    if DEBUG: write_log('name: %s' % json_item[k]['name'])
                if "original_title" in json_item[k]:
                    self['original_title'].setText(str(json_item[k]['original_title']))
                else:
                    self['original_title'].setText(str(json_item[k]['original_name']))

                Ratingtext = _("User Rating") + ": %s /10" % str(json_item[k]['vote_average']) + ' (' + _("Votes") + ": " + str(json_item[k]['vote_count']) + ')'
                if DEBUG: write_log('Ratingtext: %s' % Ratingtext)
                self.ratingstars = int(10*(float(str(json_item[k]['vote_average']))))
                self["starsbg"].show()
                if DEBUG: write_log('self.ratingstars: %s' % self.ratingstars)
                self["stars"].setValue(self.ratingstars)
                self["stars"].show()
                self['overview'].setText(str(json_item[k]['overview']))
                self["vote_average"].setText(Ratingtext)
                self["overview"].setText(str(json_item[k]['overview']))
            else:
                self.tempfile = '/usr/lib/enigma2/python/Plugins/Extensions/TorrServer/images/poster_none.png'
                self['title'].setText(self.evntNm)
                self['original_title'].setText('')
                self['overview'].setText('')
                self['vote_average'].setText('')
                self["starsbg"].hide()
                self["stars"].hide()

        except Exception as e:
            if DEBUG:
                write_log('JSON request: %s' % traceback.format_exc())

    def showPoster(self):
        if self.evntNm == '':
            return ''
        self.getPoster()
        self.picload = ePicLoad()
        self['poster'].instance.setPixmap(None)
        self['poster'].hide()
        jpg_file = str(self.tempfile)
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

    def filterSearch(self, filmname):
        try:
            yr = [ _y for _y in re.findall(r'\d{4}', filmname) if '1930' <= _y <= '%s' % gmtime().tm_year ]
            return '%s' % yr[-1] if yr else ''
        except:
            return ''

    def filtername(self):
        sd = self.evntNm
        try:
            yr = [ _y for _y in re.findall(r'\d{4}', sd) if '1930' <= _y <= '%s' % gmtime().tm_year ]
            parts = sd.split(yr[0], -1)
            res = parts[0]
            if DEBUG: write_log('res: %s' % res)
        except:
            res = sd

        try:
            dig = [ _y for _y in re.findall(r'[\\/]', res) ]
            parts = sd.split(dig[0], -1)
            res2 = parts[0]
            if DEBUG: write_log('res2: %s' % res2)
        except:
            res2 = res

        try:
            dig = [ _y for _y in re.findall(r'\d{4}p', res2) ]
            parts = sd.split(dig[0], -1)
            self.evntNm = parts[0]
            if DEBUG: write_log('res3: %s' % self.evntNm)
        except:
            self.evntNm = res2

        return self.evntNm

    def torrconf(self):
        self.session.openWithCallback(self.createList(), TorrConf)

class TorrConf(ConfigListScreen, Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        if screenWidth == 1920:
            self.skin = skinConf_fhd
        else:
            self.skin = skinConf_hd
        self["statusbar"] = Label()
        self['key_red'] = Label(_('Cancel'))
        self['key_green'] = Label( _('Save'))
        self["key_yellow"] = Label()
        self["key_blue"] = Label(_("Install"))
        self.setTitle(_('Settings torreserver'))
        ConfigListScreen.__init__(self, [getConfigListEntry(_('Autostart'), config.plugins.torrserver.autostart),
         getConfigListEntry(_('Player torrent'), config.plugins.torrserver.player),
         getConfigListEntry(_('Infobar mode:'), config.plugins.torrserver.infobarMode)])
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'],
        {'ok': self.save,
         'green': self.save,
         "blue": self.install_update,
         'cancel': self.exit,
         'red': self.exit}, -2)
        self.get_status()
        self.timer = eTimer()
        self.ftimer = eTimer()

    def save(self):
        for x in self['config'].list:
            x[1].save()
        self.close()

    def exit(self):
        for x in self['config'].list:
            x[1].cancel()
        self.close()
    
    def get_status(self):
        if os.path.isfile(torr_path) == False:
            self['statusbar'].setText(_('TorrServer is') + " " + _('not installed :('))
            self["key_blue"].setText(_("Install"))
        elif (get_pid("TorrServer")):
            version = get_version()
            self['statusbar'].setText(_('TorrServer is') + " " + _('running') + " " + _('version') + " " +  version)
            self["key_blue"].setText(_("Check updates"))
        else:
            self['statusbar'].setText(_('TorrServer is') + " " + _('down :('))
            self["key_blue"].setText(_("Check updates"))

    def install_update(self):
        arch = subprocess.check_output('uname -m; exit 0', shell=True)
        arch = arch.strip()
        repo_json = get_url(repolist)
        repo_json = '[' + repo_json + ']'
        repo_json = json.loads(repo_json)
        if repo_json != False:
            for item in repo_json:
                new_ver = str(item['version'])
                if DEBUG: write_log('version: %s' % version)
                if arch == 'armv7l':
                    url = str(item['links']['linux-arm7'])
                elif (arch == 'mips'):
                    url = str(item['links']['linux-mipsle'])
                else:
                    self['statusbar'].setText(_('No version TorrServer!'))
                    return False
        if os.path.isfile(torr_path) == False:
            self['statusbar'].setText(_('TorrServer is') + " " + _('try install :)'))
            if DEBUG: write_log('no server - try download: %s' % version)
            res = download_torr(url)
        elif get_version() != new_ver:
            self['statusbar'].setText(_('TorrServer is') + " " + _('try update :)'))
            self.start_stop()
            if DEBUG: write_log('find new ver - try download: %s' % version)
            res = download_torr(url)
            self.start_stop()
        else:
            if DEBUG: write_log('no new ver - go home: %s' % version)
            self['statusbar'].setText(_('No update TorrServer found'))
            res = False
        if res == True:
            self["key_red"].setText(_("Check updates"))
            self['statusbar'].setText(_('TorrServer is') + " " + _('installed :)'))

    def start_stop(self):
        if get_pid("TorrServer") == False:
            fh = open(os.devnull, 'wb')
            os.system('export GODEBUG=madvdontneed=1')
            p = subprocess.Popen(['/usr/bin/TorrServer'], shell=False, stdout = fh, stderr = fh)
            fh.close()
            time.sleep(0.5)
            menulist = []
            self.timer = eTimer()
            self.timer.callback.append(self.get_status)
            self.timer.start(5000, False)
            self.ftimer.start(1000, True)
        else:
            os.system("killall TorrServer")
            time.sleep(0.5)
            self.timer.stop()
        self.get_status()
        self.onClose.append(self.timer.stop)

def autoStart(reason, **kwargs): # starts DURING the Enigma2 booting
    if config.plugins.torrserver.autostart.value == True and get_pid("TorrServer") == False and os.path.isfile(torr_path) == True:
        fh = open(os.devnull, 'wb')
        os.system('export GODEBUG=madvdontneed=1')
        p = subprocess.Popen(['/usr/bin/TorrServer'], shell=False, stdout = fh, stderr = fh)
        fh.close()

def main(session, **kwargs):
    session.open(TorrMenu)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            where = PluginDescriptor.WHERE_AUTOSTART, fnc = autoStart),
        PluginDescriptor(
            name = _("TorrServer runner"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "plugin.png", description = _("Plugin for run TorrServer"), fnc = main)
    ]
