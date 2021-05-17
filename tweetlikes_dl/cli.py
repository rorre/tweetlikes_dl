import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import tweepy
from appdirs import AppDirs
from dateutil.parser import parse
from pytest import UsageError

from tweetlikes_dl.cli_helper import download_medias, load_config, write_config
from tweetlikes_dl.helper import create_api, get_media_metadata, get_tweets


class Config:
    api: tweepy.API = None

    def __init__(self):
        self.appdirs = AppDirs("twitterlikes_dl", "rorre")
        self.config_path = os.path.join(self.appdirs.user_data_dir, "config.json")

        Path(self.appdirs.user_data_dir).mkdir(parents=True, exist_ok=True)


@click.group()
@click.pass_context
def cli(ctx: click.Context):
    """A simple tool to download twitter medias."""
    ctx.obj = Config()

    if ctx.invoked_subcommand == "authorize":
        return

    api = None
    if not os.path.exists(ctx.obj.config_path):
        raise UsageError("Please run authorize first!")
    else:
        config = load_config(ctx.obj.config_path)
        api, _, _ = create_api(
            config["consumer_key"],
            config["consumer_secret"],
            config["access_token"],
            config["access_token_secret"],
        )
    ctx.obj.api = api


@cli.command()
@click.argument("consumer_key")
@click.argument("consumer_secret")
@click.pass_obj
def authorize(config: Config, consumer_key: str, consumer_secret: str):
    """Authorize OAuth and saves authentication info."""
    _, access_token, access_token_secret = create_api(consumer_key, consumer_secret)
    write_config(
        config.config_path,
        {
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
        },
    )


@cli.command()
@click.option("--username", "-u", default=None, help="Username to lookup.")
@click.option("--count", "-c", default=1000, help="Number of liked post to download.")
@click.option("--min-date", default=None, help="Most recent date to download.")
@click.option("--max-date", default=None, help="Oldest date to download.")
@click.option(
    "--min-id",
    default=None,
    type=int,
    help="Starts downloading after meeting this ID. (Most recent one)",
)
@click.option(
    "--max-id",
    default=None,
    type=int,
    help="Stops downloading after meeting this ID. (Oldest one)",
)
@click.option(
    "--retweet",
    "-r",
    is_flag=True,
    default=False,
    help="Also download user's retweets.",
)
@click.option(
    "--output-dir",
    "-o",
    type=str,
    default="output",
    help="Set output directory where all medias will be downloaded.",
)
@click.option(
    "--format",
    "-f",
    "format_",
    type=str,
    default="{username}/{id}-{filename}",
    help="Format output filename with tokens. (Available tokens: id, extension, filename, url, username)",
)
@click.option(
    "--like",
    "-l",
    is_flag=True,
    default=False,
    help="Download user's likes instead of timeline (and retweets).",
)
@click.option(
    "--ignore-existing",
    is_flag=True,
    default=False,
    help="Ignore existing files, defaults to replacing all previously downloaded files.",
)
@click.pass_obj
def download(
    config: Config,
    username: Optional[str],
    count: int,
    min_date: Optional[str],
    max_date: Optional[str],
    min_id: int,
    max_id: int,
    retweet: bool,
    output_dir: str,
    format_: str,
    like: bool,
    ignore_existing: bool,
):
    """Batch download medias from user's timeline or likes."""
    if min_date:
        min_datetime = parse(min_date)
    else:
        min_datetime = datetime.max

    if max_date:
        max_datetime = parse(max_date)
    else:
        max_datetime = datetime.min

    method = config.api.favorites if like else config.api.user_timeline
    click.echo("Fetching tweets...")
    tweets_to_download = list(
        get_tweets(
            method,
            username,
            retweet,
            min_id,
            max_id,
            min_datetime,
            max_datetime,
            count,
        )
    )

    click.echo("Fetching media metadatas...")
    medias = get_media_metadata(config.api, tweets_to_download)
    download_medias(medias, output_dir, format_, ignore_existing)


if __name__ == "__main__":
    cli()
