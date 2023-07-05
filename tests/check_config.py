"""
Check if local config is present use it instead of the default one
"""
import os
import sys
from pathlib import Path

def check_config():
    """
    Check if local config is present use it instead of the default one
   """
    test_dir = os.path.abspath(os.path.dirname(__file__))
    main_dir = os.path.abspath(os.path.dirname(test_dir))
    if main_dir not in sys.path:
        sys.path.append(main_dir)
    if test_dir not in sys.path:
        sys.path.append(test_dir)

    config_file_main_local = Path.joinpath(Path(main_dir), "config_local.ini")
    config_file_main_global = Path.joinpath(Path(main_dir), "config.ini")
    config_file_test_local = Path.joinpath(Path(test_dir), "config_test_unitaire_local.ini")
    config_file_test_global = Path.joinpath(Path(test_dir), "config_test_unitaire.ini")

    # Default to using local config files unless if they are present
    if config_file_main_local.is_file():
        config_file_main_path = str(config_file_main_local)
    elif config_file_main_global.is_file():
        config_file_main_path = str(config_file_main_global)
    else:
        raise FileNotFoundError('No config file was found: %s and %s do not exist' % \
            (config_file_main_local, config_file_main_global))

    if config_file_test_local.is_file():
        config_file_test_path = str(config_file_test_local)
    elif config_file_test_global.is_file():
        config_file_test_path = str(config_file_test_global)
    else:
        raise FileNotFoundError('No config file was found: %s and %s do not exist' % \
            (config_file_test_local, config_file_test_global))

    return config_file_test_path, config_file_main_path
