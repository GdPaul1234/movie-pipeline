from configparser import ConfigParser, ExtendedInterpolation

class ConfigLoader:
    def __init__(self) -> None:
        self._config = ConfigParser(interpolation=ExtendedInterpolation())
        self._config.read('config.ini', encoding='utf-8')

    @property
    def config(self):
        return self._config
