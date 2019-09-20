import pkg_resources
import multiprocessing
from win32.win32gui import SystemParametersInfo
from requests import get
from os import getcwd, path, system
from threading import Thread
from json import load, loads
from time import sleep
from infi.systray import SysTrayIcon
import sys

CONFIG = '{\n"source":"unsplash",\n"size":"1920x1080",\n"interval":300,\n"filename":"current.jpg",\n"keywords":[]\n}'

SOURCES = {
    "unsplash": "https://source.unsplash.com/random/",
}

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = path.abspath(".")

    return path.join(base_path, relative_path)

class AutoWallpaper:

    def __init__(self, config='config.json', *args, **kwargs):
        self.error = False
        self.get_config(config)
        self.default_interval = 120
        self.thread = Thread(target=self._start, name='wall_thread')

        self.report = {
            "errors": 0,
            "success": 0,
            "requests": 0,
            "saved": 0,
            "interval": self.config.get("interval")
        }

    def get_app_path(self):
        if getattr(sys, 'frozen', False):
            application_path = path.dirname(sys.executable)
        elif __file__:
            application_path = path.dirname(__file__)
        
        return application_path

    def get_config(self, config):

        config_path = path.join(self.get_app_path(), config)

        size = path.getsize(config_path) if path.isfile(config_path) else 0

        if size > 0:
            with open(config_path, 'r') as cf:
                self.config = load(cf)
        else:
            print("config.json not found in current directory. Using Default Settings")
            with open(config_path, 'w') as cf:
                cf.write(CONFIG)
            self.config = loads(CONFIG)


    def get_wallpaper(self):
        source = SOURCES.get(self.config.get("source", "unsplash"))
        size = self.config.get("size")
        keywords = ",".join(self.config.get("keywords"))

        self._binary = get(source + size, params=keywords)

        self.report["requests"] += 1

        if self._binary.status_code == 200:
            self.error = False
            self.report["success"] += 1
        else:
            self.error = True
            print("\rProblem with the network...Error ", self._binary.status_code)
            self.report["errors"] += 1

        self.write_wallpaper()
    
    def write_wallpaper(self):
        with open(self.config.get("filename"), 'wb') as f:
            f.writelines(self._binary.iter_content())
    
    def get_path(self):
        p = path.join(getcwd(), self.config.get("filename"))
        return p

    def save_wallpaper(self, wallpaper):
        raise NotImplementedError

    def set_wallpaper(self):
        SystemParametersInfo(0x0014, self.get_path())

    def _start(self):
        interval = self.config.get("interval", self.default_interval)

        while True:
            self.get_wallpaper()
            self.set_wallpaper() if not self.error else None
            sleep(interval)

    def print_report(self):
        print("---report---")
        for item in self.report:
            print(f"{item}: {self.report.get(item)}")
        print("---------")

    def start(self):
        print("Auto Wallpaper started...")
        self.thread.start()

    def refresh(self, s=None):
        self.get_wallpaper()
        self.set_wallpaper() if not self.error else None
    
    def restart(self, s=None):
        self.get_config()
        self.refresh()
        


def main():
    wall = AutoWallpaper()
    wall.start()
    menu = (("Refresh", None, wall.refresh), ("Restart", None, wall.restart))
    res = resource_path("icon.ico")
    systray = SysTrayIcon(res, "Auto Wallpaper", menu, on_quit=sys.exit)
    systray.start()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
    
    