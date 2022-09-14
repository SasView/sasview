from sas.system.config.config import Config


def get_config() -> Config:
    return Config()

configuration = get_config()