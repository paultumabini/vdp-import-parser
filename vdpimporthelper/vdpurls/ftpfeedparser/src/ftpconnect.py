from ftplib import FTP
from io import BytesIO

from src.creds import FtpCredential


class FtpConnect(FTP, FtpCredential):
    def __init__(self, config_items):
        super().__init__()  # Initialize the FTP class
        FtpCredential.__init__(self)  # Initialize the FtpCredential
        self._config_items = config_items

    @property
    def config_items(self):
        return self._config_items

    @config_items.setter
    def config_items(self, config_items):
        return config_items

    def connect_ftp(self):
        """Connect to FTP server and yield file streams."""
        try:

            for item in self.config_items:
                self.provide_cred(
                    item.get('ftp_host'),
                    item.get('ftp_port'),
                    item.get('ftp_user'),
                    item.get('ftp_pass'),
                )
                self.connect(self.ftp_host, self.ftp_port)
                self.login(self.ftp_user, self.ftp_pass)
                print(
                    self.getwelcome(),
                    f"-> {item.get('provider_name').upper()} Logged in...",
                )

                r = BytesIO()
                # self.set_pasv(False)
                self.retrbinary(f'RETR /{item["file"]}', r.write)
                r.seek(0)
                yield [r, item]
        except Exception as e:
            print(
                f"\nError MSG: {e}! \nCheck your connection and your VPN setup if applicable\n"
            )

        finally:
            self.quit()
