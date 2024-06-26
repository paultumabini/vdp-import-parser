class FtpCredential:
    def __init__(
        self,
        ftp_host: str = None,
        ftp_port: int = None,
        ftp_user: str = None,
        ftp_pass: str = None,
    ) -> None:
        self._ftp_host = ftp_host
        self._ftp_port = ftp_port
        self._ftp_user = ftp_user
        self._ftp_pass = ftp_pass

    @property
    def ftp_host(self) -> str:
        """Getter for FTP host."""
        return self._ftp_host

    @ftp_host.setter
    def ftp_host(self, new_host: str) -> None:
        """Setter for FTP host with validation."""
        if not isinstance(new_host, str) or not new_host:
            raise ValueError('Please enter a valid host')
        self._ftp_host = new_host

    @property
    def ftp_port(self) -> int:
        """Getter for FTP port."""
        return self._ftp_port

    @ftp_port.setter
    def ftp_port(self, new_port: int) -> None:
        """Setter for FTP port with validation."""
        if not isinstance(new_port, int) or new_port <= 0:
            raise ValueError('Please enter a valid port')
        self._ftp_port = new_port

    @property
    def ftp_user(self) -> str:
        """Getter for FTP username."""
        return self._ftp_user

    @ftp_user.setter
    def ftp_user(self, new_uname: str) -> None:
        """Setter for FTP username with validation."""
        if not isinstance(new_uname, str) or not new_uname:
            raise ValueError('Please enter a valid username')
        self._ftp_user = new_uname

    @property
    def ftp_pass(self) -> str:
        """Getter for FTP password."""
        return self._ftp_pass

    @ftp_pass.setter
    def ftp_pass(self, new_pass: str) -> None:
        """Setter for FTP password with validation."""
        if not isinstance(new_pass, str) or not new_pass:
            raise ValueError('Please enter a valid password')
        self._ftp_pass = new_pass

    def provide_cred(
        self, ftp_host: str, ftp_port: int, ftp_user: str, ftp_pass: str
    ) -> None:
        """Provide credentials if not already set."""
        if not self._ftp_host:
            self._ftp_host = ftp_host
        if not self._ftp_port:
            self._ftp_port = ftp_port
        if not self._ftp_user:
            self._ftp_user = ftp_user
        if not self._ftp_pass:
            self._ftp_pass = ftp_pass


# os.environ.get('AIM_FTP_USER')
# os.environ.get('AIM_FTP_PASS')
# os.environ.get('AIM_FTP_HOST')
