import os
from datetime import datetime

from typing import Optional

import click

from dateutil.parser import parse
from pytest import UsageError
from tweepy import TweepError

from tweetlikes_dl.cli_helper import download_medias
from tweetlikes_dl.helper import create_api, get_media_metadata, get_tweets
from tweetlikes_dl.config import Config


@click.group()
@click.pass_context
def cli(ctx: click.Context):
    """A simple tool to download twitter medias."""
    if not os.path.exists(Config.config_path):
        raise UsageError("Please run authorize first!")

    if ctx.invoked_subcommand == "authorize":
        return

    ctx.obj = Config.load()
    api, _, _ = create_api(
        ctx.obj.config_data["consumer_key"],
        ctx.obj.config_data["consumer_secret"],
        ctx.obj.config_data["access_token"],
        ctx.obj.config_data["access_token_secret"],
    )
    ctx.obj.api = api


@cli.command()
@click.argument("consumer_key")
@click.argument("consumer_secret")
@click.pass_obj
def authorize(config: Config, consumer_key: str, consumer_secret: str):
    """Authorize OAuth and saves authentication info."""
    try:
        _, access_token, access_token_secret = create_api(consumer_key, consumer_secret)
    except TweepError as e:
        # what the hell tweepy?
        if type(e.args[0].args[0]) == str:
            http_status = e.args[0].response.status_code
        else:
            # For no reason, this is TweepError(TweepError(BadToken(...)))
            http_status = e.args[0].args[0].response.status_code

        if http_status == 401:
            raise click.ClickException("Unauthorized, check your inputs again.")
        elif http_status >= 500:
            raise click.ClickException("A server error has occured, try again later.")
        raise e

    Config(
        {
            "consumer_key": consumer_key,
            "consumer_secret": consumer_secret,
            "access_token": access_token,
            "access_token_secret": access_token_secret,
        },
    ).save()


@cli.command()
@click.option("--username", "-u", default=None, help="Username to lookup.")
@click.option("--count", "-c", default=1000, help="Number of liked post to download.")
@click.option("--max-date", default=None, help="Most recent date to download.")
@click.option("--since-date", default=None, help="Oldest date to download.")
@click.option(
    "--max-id",
    default=None,
    type=int,
    help="Starts downloading after meeting this ID. (Most recent one)",
)
@click.option(
    "--since-id",
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
    "--like",
    "-l",
    is_flag=True,
    default=False,
    help="Download user's likes instead of timeline (and retweets).",
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
    since_date: Optional[str],
    max_date: Optional[str],
    since_id: int,
    max_id: int,
    retweet: bool,
    output_dir: str,
    format_: str,
    like: bool,
    ignore_existing: bool,
):
    """Batch download medias from user's timeline or likes."""
    if since_date:
        since_datetime = parse(since_date)
    else:
        since_datetime = datetime.min

    if max_date:
        max_datetime = parse(max_date)
    else:
        max_datetime = datetime.max

    try:
        method = config.api.favorites if like else config.api.user_timeline
        click.echo("Fetching tweets...")
        tweets_to_download = list(
            get_tweets(
                method,
                username,
                retweet,
                since_id,
                max_id,
                since_datetime,
                max_datetime,
                count,
            )
        )

        click.echo("Fetching media metadatas...")
        medias = get_media_metadata(config.api, tweets_to_download)
        download_medias(medias, output_dir, format_, ignore_existing)
    except TweepError as e:
        http_status = e.response.status_code
        if http_status == 401:
            raise click.ClickException("Unauthorized, please run authorize again.")
        elif http_status >= 500:
            raise click.ClickException("A server error has occured, try again later.")
        raise e


if __name__ == "__main__":
    cli()
