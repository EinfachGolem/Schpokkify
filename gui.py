import os, subprocess, sys, json
import validators
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
#import spotdl

from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.image import Image
from kivymd.uix.button import MDFillRoundFlatIconButton, MDFillRoundFlatButton, MDRoundFlatIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import OneLineIconListItem, IconLeftWidget, MDList, OneLineListItem
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.uix.modalview import ModalView
from kivymd.toast import toast

testlink = "https://open.spotify.com/playlist/5XdVwetkgEK8wOoUTsSnC5?si=88a46d9a93804558"

settingjson = json.load(open("setting.json", "r"))
print(settingjson)

class Setting:
    print("Initiating Settings...")
    def __init__(self, jsondata):
        self.bitrate = jsondata["bitrate"]
        self.libary = jsondata["libary"]
        self.audioformat = jsondata["audioformat"]
        self.output = jsondata["output"]
        self.clientid = jsondata["spotifyapi"]["clientid"]
        self.clientsecret = jsondata["spotifyapi"]["clientsecret"]
    
s = Setting(settingjson)
print("Settings successfully initiated...")

class App(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #self.screen = Builder.load_string(KV)
        #Window.bind(on_keyboard=self.events)
        self.screen = Builder.load_file("./kv/gui.kv")
        self.manager_open = False
        self.manager = None
        self.dialog = None
        self.dropDown = None
        self.Spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(s.clientid, s.clientsecret))
        self.LinkList = []

    def openDirectorydialog(self, *args):
        #print("Dialog should be open")
        if not self.manager:
            self.file_manager = MDFileManager(
                exit_manager=self.exit_manager, select_path=self.select_path)
            self.file_manager.show(os.getcwd() + "\processed")  # output manager to the screen
        self.manager_open = True

    def select_path(self, path):
        self.exit_manager()
        self.screen.ids.txt_directory.text = path
    
    def exit_manager(self, *args):
        self.file_manager.close()
        self.manager_open = False

    def addLinkToList(self, *args):
        link = self.screen.ids.txt_downloadlink.text
        if len(link) > 0:
            if self.validateURL(link):
                newLinkWidget = OneLineIconListItem(
                    IconLeftWidget(
                        id = str(len(self.LinkList)),
                        icon = "music-note-minus",
                        on_release= lambda x: self.removeLinkFromList(newLinkWidget)
                    ),
                    text=self.screen.ids.txt_downloadlink.text,
                )
                self.LinkList.append(newLinkWidget)
                print(f"Link {len(self.LinkList)} added: {self.screen.ids.txt_downloadlink.text}")
                self.screen.ids.spotdllinks.add_widget(newLinkWidget)
                self.screen.ids.txt_downloadlink.text = ""
            else:
                self.show_dialog_error("Der Link ist nicht GÜLTIG!")
        else:
            self.show_dialog_error("JUNGE! WO IST DER LINK!!!")
        

    def removeLinkFromList(self, widget):
        print(f"{widget.text} was removed!")
        self.screen.ids.spotdllinks.remove_widget(widget)
        self.LinkList.remove(widget)

    def validateURL(self, URL):
        return validators.url(URL)

    def show_dialog_error(self, alerttext):
        if not self.dialog:
            self.dialog = MDDialog(
                text=alerttext,
                buttons=[
                    MDFlatButton(
                        text="SCHREI MICH NICHT AN!",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release = self.close_dialog
                    ),
                ],
            )
            self.dialog.open()
    
    def show_dialog_success(self, alerttext):
        if not self.dialog:
            self.dialog = MDDialog(
                text=alerttext,
                buttons=[
                    MDFlatButton(
                        text="Alles klar",
                        theme_text_color="Custom",
                        text_color=self.theme_cls.primary_color,
                        on_release = self.close_dialog
                    ),
                ],
            )
            self.dialog.open()

    def close_dialog(self, *args):
        self.dialog.dismiss(force=True)
        self.dialog = None

    def startDownload(self, *args):
        if len(self.LinkList) < 1:
            print("No links in List... SKipping Download")
            return
        
        for widget in self.LinkList:
            link = widget.text
            check = SpotifyLoad(link, self.screen.ids.txt_directory.text)
            if check:
                self.show_dialog_success(f"The Download was successfull!\nDownload: {link}")
            else:
                self.show_dialog_error("The Download has failed...")
            self.removeLinkFromList(widget)

    def openSettingSetBitrate(self, *args):
        rates = ["auto", "disable", "8k", "16k", "24k", "32k", "40k", "48k", "64k", "72k", "80k", "88k", "96k", "112k", "128k", "160k", "192k", "224k", "256k", "320k"]
        itemse = []
        for rate in rates:
            itemse.append({
                "viewclass": "OneLineListItem",
                "text": rate,
                "on_release": lambda x = rate: self.setBitrateMenu(x)
            })

        self.dropDown = MDDropdownMenu(items=itemse, width_mult=2, caller=self.screen.ids.setting_bitrate)
        self.dropDown.open()
    
    def setBitrateMenu(self, menu_value):
        print(menu_value)
        self.screen.ids.setting_bitrate.text = menu_value
        self.updateSettings("bitrate", menu_value)
    
    def openSettingSetAudioFormat(self, *args):
        options = ["mp3", "flac", "ogg", "opus", "m4a", "wav"]
        itemse = []
        for option in options:
            itemse.append({
                "viewclass": "OneLineListItem",
                "text": option,
                "on_release": lambda x = option: self.setFormatMenu(x)
            })

        self.dropDown = MDDropdownMenu(items=itemse, width_mult=2, caller=self.screen.ids.setting_audioformat)
        self.dropDown.open()
    
    def setFormatMenu(self, menu_value):
        print(menu_value)
        self.screen.ids.setting_audioformat.text = menu_value
        self.updateSettings("audioformat", menu_value)

    def openSettingSetLibary(self, *args):
        options = ["youtube", "youtube-music", "soundcloud"]
        itemse = []
        for option in options:
            itemse.append({
                "viewclass": "OneLineListItem",
                "text": option,
                "on_release": lambda x = option: self.setLibaryMenu(x)
            })

        self.dropDown = MDDropdownMenu(items=itemse, width_mult=2, caller=self.screen.ids.setting_libary)
        self.dropDown.open()
    
    def setLibaryMenu(self, menu_value):
        print(menu_value)
        self.screen.ids.setting_libary.text = menu_value
        self.updateSettings("libary", menu_value)

    def updateSettings(self, entry, value):
        settingjson[entry] = value
        newdata = json.dumps(settingjson, indent=4)
        with open("setting.json", "w") as file:
            file.write(newdata)
            file.close()
        print(f"New Settings: [{entry}] = {value} saved...")
        self.dropDown.dismiss()
        self.dropDown = None


    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"

        self.screen.ids.txt_directory.text = os.getcwd() + "\processed"
        self.screen.ids.setting_bitrate.text = s.bitrate
        self.screen.ids.setting_audioformat.text = s.audioformat
        self.screen.ids.setting_libary.text = s.libary

        return self.screen


def SpotifyLoad(link, output):
    subprocess.run(f"spotdl {link} --audio {s.libary} --bitrate {s.bitrate} --format {s.audioformat} --output {output}")
    return True

App().run()