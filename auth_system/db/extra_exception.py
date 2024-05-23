

class EmailAlreadyExistsError(Exception):
    def __init__(self, email):
        self.email = email
        super().__init__(f"User with email '{email}' already exists.")
