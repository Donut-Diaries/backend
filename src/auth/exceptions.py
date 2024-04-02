class JWTSecretUndefined(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.message = "JWT_SECRET and JWT_SECRET_FILE not found. You have to declare at least one as envvar"


class JWTSecretFileUndefined(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.message = "JWT_SECRET_FILE not found. You have to declare it as envvar or set default"
