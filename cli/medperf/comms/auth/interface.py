from abc import ABC, abstractmethod


class Auth(ABC):
    @abstractmethod
    def __init__(self):
        """Initialize the class"""

    @abstractmethod
    def signup(self, email, password):
        """Sign up a user"""

    @abstractmethod
    def change_password(self, email):
        """User password change"""

    @abstractmethod
    def login(self, email):
        """Log in a user"""

    @abstractmethod
    def logout(self):
        """Log out a user"""

    @property
    @abstractmethod
    def access_token(self):
        """An access token to authorize requests to the MedPerf server"""
