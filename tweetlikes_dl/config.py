import json
import os
from pathlib import Path

import tweepy
from appdirs import AppDirs


class Config:
    api: tweepy.API = None
    appdirs = AppDirs("twitterlikes_dl", "rorre")
    config_path = os.path.join(appdirs.user_data_dir, "config.json")

    def __init__(self, config_data: dict):
        self.config_data = config_data
        Path(self.appdirs.user_data_dir).mkdir(parents=True, exist_ok=True)

    @classmethod
    def load(cls):
        with open(cls.config_path, "r") as f:
            return cls(json.load(f))

    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config_data, f)
