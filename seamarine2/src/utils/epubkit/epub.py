from . import Container, Mimetype
import zipfile
import os

class Epub:
    def __init__(self):
        self.mimetype: Mimetype = None
        self.container: Container = None

    