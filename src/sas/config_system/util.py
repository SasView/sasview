from sas.config_system.config import Config

import sys
import os
import os

def get_config() -> Config:
    return Config()







def load_local_config(app_dir):
    assert False
    filename = 'local_config.py'
    path = os.path.join(app_dir, filename)
    try:
        module = load_module_from_path('sas.local_config', path)
        #logger.info("GuiManager loaded %s", path)
        return module
    except Exception as exc:
        #logger.critical("Error loading %s: %s", path, exc)
        sys.exit()

configuration = get_config()