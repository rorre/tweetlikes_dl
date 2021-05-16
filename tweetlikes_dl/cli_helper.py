import json
import os
from pathlib import Path
from typing import List, Union

import click
import requests


def download_file(url: str, target_path: Union[os.PathLike, str]):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(target_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def load_config(config_path: Union[os.PathLike, str]) -> dict:
    with open(config_path, "r") as f:
        return json.load(f)


def write_config(config_path: Union[os.PathLike, str], data: dict):
    with open(config_path, "w") as f:
        json.dump(data, f)


def download_medias(medias: List[dict]):
    is_skip_all = False
    is_replace_all = False
    with click.progressbar(medias, label="Downloading medias") as bar:
        for media in bar:
            cwd = os.getcwd()
            target_folder = os.path.join(cwd, "downloads", media["username"])
            extension = media["url"][-3:]

            # Create directory, incase it doesn't exist.
            Path(target_folder).mkdir(parents=True, exist_ok=True)

            target_path = os.path.join(target_folder, f"{media['id']}.{extension}")
            replace = is_replace_all
            if os.path.exists(target_path):
                while not (is_skip_all or is_replace_all):
                    click.echo("File already exist, do you want to replace?")
                    value = click.prompt("[Y]es/[N]o/[S]kip all/[R]eplace all")
                    if value == "Y":
                        replace = True
                        break
                    if value == "R":
                        replace = True
                        is_replace_all = True
                    if value == "S":
                        is_skip_all = True

                if not replace:
                    continue

            if replace:
                click.echo("Replacing file.")
            download_file(media["url"], target_path)
