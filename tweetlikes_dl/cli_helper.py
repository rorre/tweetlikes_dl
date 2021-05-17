import json
import os
from pathlib import Path
from typing import List, Tuple, Union

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


def parse_format(user_format: str, media: dict) -> Tuple[str, str]:
    user_filepath = user_format.format_map(media).split("/")
    user_folder = "/".join(user_filepath[:-1])
    user_filename = user_filepath[-1]
    return user_folder, user_filename


def download_medias(
    medias: List[dict],
    output_dir: str,
    user_format: str,
    ignore_existing: bool,
):
    with click.progressbar(medias, label="Downloading medias") as bar:
        for media in bar:
            cwd = os.getcwd()

            output_folder, output_filename = parse_format(user_format, media)
            target_folder = os.path.join(cwd, output_dir, output_folder)

            # Create directory, incase it doesn't exist.
            Path(target_folder).mkdir(parents=True, exist_ok=True)

            target_path = os.path.join(target_folder, output_filename)
            if os.path.exists(target_path) and ignore_existing:
                click.echo(f"{target_path}: Skipping.")
                continue

            download_file(media["url"], target_path)
