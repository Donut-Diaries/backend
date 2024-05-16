class JWTSecretUndefined(Exception):
    def __init__(self, *args: object) -> None:
        self.message = "JWT_SECRET and JWT_SECRET_FILE not found. You have to declare at least one as env var"
        super().__init__(self.message)


class JWTSecretFileUndefined(Exception):
    def __init__(self, *args: object) -> None:
        self.message = "JWT_SECRET_FILE not found. You have to declare it as envvar or set default"
        super().__init__(self.message)


class JWTSecretFileNotFound(Exception):
    def __init__(self, *args: object) -> None:
        set_file_name = ""

        if args:
            set_file_name = args[0]

        self.message = f"The set JWT_SECRET_FILE not found: {set_file_name}"

        super().__init__(self.message)
