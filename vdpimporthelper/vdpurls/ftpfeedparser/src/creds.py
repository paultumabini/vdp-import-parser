import os


class Credentials:
    def __init__(self):
        self._user = None
        self._passwd = None
        self._site = None
        self._port = None

    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, username):
        if not self._user:
            self._user = username

    @property
    def password(self):
        return self._passwd

    @password.setter
    def password(self, password):
        if not self._passwd:
            self._passwd = password

    @property
    def site(self):
        return self._passwd

    @site.setter
    def site(self, site):
        if not self._site:
            self._site = site

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        if not self._port:
            self._port = port


class FtpCredsProvider(Credentials):
    def provide(self):
        if not self._user:
            self.username = os.environ.get('AIM_FTP_USER')
        if not self._passwd:
            self.password = os.environ.get('AIM_FTP_PASS')
        if not self._site:
            self.site = os.environ.get('AIM_FTP_SITE')
        if not self._port:
            self.port = 21
