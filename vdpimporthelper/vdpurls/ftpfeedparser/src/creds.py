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
        return self._ftp_host

    @ftp_host.setter
    def ftp_host(self, new_host: str) -> None:
        if not isinstance(new_host, str) or not new_host:
            raise ValueError('Please enter a valid host')
        self._ftp_host = new_host

    @property
    def ftp_port(self) -> int:
        return self._ftp_port

    @ftp_port.setter
    def ftp_port(self, new_port: int) -> None:
        if not isinstance(new_port, int) or new_port <= 0:
            raise ValueError('Please enter a valid port')
        self._ftp_port = new_port

    @property
    def ftp_user(self) -> str:
        return self._ftp_user

    @ftp_user.setter
    def ftp_user(self, new_uname: str) -> None:
        if not isinstance(new_uname, str) or not new_uname:
            raise ValueError('Please enter a valid username')
        self._ftp_user = new_uname

    @property
    def ftp_pass(self) -> str:
        return self._ftp_pass

    @ftp_pass.setter
    def ftp_pass(self, new_pass: str) -> None:
        if not isinstance(new_pass, str) or not new_pass:
            raise ValueError('Please enter a valid password')
        self._ftp_pass = new_pass

    def provide_cred(
        self, ftp_host: str, ftp_port: int, ftp_user: str, ftp_pass: str
    ) -> None:
        # Always refresh credentials per feed to avoid stale state reuse.
        self.ftp_host = ftp_host
        self.ftp_port = ftp_port
        self.ftp_user = ftp_user
        self.ftp_pass = ftp_pass
