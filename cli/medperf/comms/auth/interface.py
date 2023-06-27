from abc import ABC, abstractmethod


class Auth(ABC):
    @abstractmethod
    def __init__(self):
        """constructor"""

    @abstractmethod
    def signup(self, email, password):
        """signup"""

    @abstractmethod
    def change_password(self, email):
        """change password"""

    @abstractmethod
    def login(self):
        """login"""

    @abstractmethod
    def logout(self):
        """logout"""

    @property
    @abstractmethod
    def access_token(self):
        """access token"""
