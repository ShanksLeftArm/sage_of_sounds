import json

config = None
with open('config.json') as f:
    config = json.load(f)
    config['DEFAULT_VOLUME'] = config['DEFAULT_VOLUME'] if 'DEFAULT_VOLUME' in config else 0.5
