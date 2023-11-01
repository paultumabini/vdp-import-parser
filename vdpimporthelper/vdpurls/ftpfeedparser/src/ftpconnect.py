from ftplib import FTP
from io import BytesIO

from src.creds import FtpCredsProvider


class FtpConnect(FtpCredsProvider, FTP):
    _ftp = FTP()

    def __init__(self, feed_export):
        super().__init__()
        self._feed_export = feed_export

    @property
    def feed_export(self):
        return self._feed_export

    @feed_export.setter
    def feed_export(self, feed_export):
        return feed_export

    def connect_ftp(self):
        self.provide()
        self._ftp.connect(self._site, self._port)
        self._ftp.login(self._user, self._passwd)
        print(self._ftp.getwelcome(), ":Logged in...")

        for item in self._feed_export:
            r = BytesIO()
            # self._ftp.set_pasv(False)
            self._ftp.retrbinary(f'RETR /{item["file"]}', r.write)
            r.seek(0)
            yield [self._ftp, r, item]

        self._ftp.quit()
