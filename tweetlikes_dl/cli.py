import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from appdirs import AppDirs
from dateutil.parser import parse

from tweetlikes_dl.cli_helper import download_medias, load_config, write_config
from tweetlikes_dl.helper import chunks, create_api, get_favorites, get_medias


class Config:
    api = None

    def __init__(self):
        self.appdirs = AppDirs("twitterlikes_dl", "rorre")
        self.config_path = os.path.join(self.appdirs.user_data_dir, "config.json")

        Path(self.appdirs.user_data_dir).mkdir(parents=True, exist_ok=True)


@click.group()
@click.option("--consumer-key", envvar="CONSUMER_KEY", required=False)
@click.option("--consumer-secret", envvar="CONSUMER_SECRET", required=False)
@click.option("--access-token", envvar="ACCESS_TOKEN", required=False)
@click.option("--access-token-secret", envvar="ACCESS_TOKEN_SECRET", required=False)
@click.pass_context
def cli(
    ctx,
    consumer_key: Optional[str],
    consumer_secret: Optional[str],
    access_token: Optional[str],
    access_token_secret: Optional[str],
):
    ctx.obj = Config()

    if ctx.invoked_subcommand == "authorize":
        return

    api = None
    if not os.path.exists(ctx.obj.config_path):
        if consumer_key and consumer_secret:
            api, access_token, access_token_secret = create_api(
                consumer_key,
                consumer_secret,
                access_token,
                access_token_secret,
            )
            write_config(
                ctx.obj.config_path,
                {
                    "consumer_key": consumer_key,
                    "consumer_secret": consumer_secret,
                    "access_token": access_token,
                    "access_token_secret": access_token_secret,
                },
            )
        else:
            raise click.UsageError("Consumer key and consumer secret must be supplied.")
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
@click.option("--count", "-c", default=1000, help="Number of liked post to download.")
@click.option("--max-date", default=None, help="Oldest date to download.")
@click.option(
    "--max-id", default=-1, type=int, help="Stops downloading after meeting this ID."
)
@click.pass_obj
def download(config: Config, count: int, max_date: Optional[str], max_id: int):
    if max_date:
        max_datetime = parse(max_date)
    else:
        max_datetime = datetime.min

    run_loop = True
    end_id = None

    tweets_to_download = []
    counter = 0
    page_number = 1
    while run_loop:
        click.echo(f"Downloading tweet data page: {page_number}")
        tweets = get_favorites(config.api, end_id=end_id)
        for t in tweets:
            if t.created_at <= max_datetime or t.id == max_id:
                run_loop = False
                break
            tweets_to_download.append(t.id)

            if counter >= count:
                run_loop = False
                break
            counter += 1
        page_number += 1
        end_id = tweets.max_id

    medias = []
    with click.progressbar(
        chunks(tweets_to_download, 100), label="Fetching media URLs"
    ) as bar:
        for status_ids in bar:
            medias.extend(get_medias(config.api, status_ids))

    download_medias(medias)


if __name__ == "__main__":
    cli()
