from configparser import ConfigParser, ExtendedInterpolation

class ConfigLoader:
    def __init__(self, options) -> None:
        self._config = ConfigParser(interpolation=ExtendedInterpolation())
        self._config.read(options.config_path, encoding='utf-8')

    @property
    def config(self):
        return self._config
