import os
from datetime import datetime

from typing import Optional

import click

from dateutil.parser import parse
from pytest import UsageError
from tweepy.errors import TweepyException

from tweetlikes_dl.cli_helper import download_medias
from tweetlikes_dl.helper import create_api, get_media_metadata, get_tweets
from tweetlikes_dl.config import Config


def null_print(*args, **kwargs):
    pass


class AliasedGroup(click.Group):
    _ALIASES = {
        "dl": "download",
        "auth": "authorize",
    }

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        if cmd_name in self._ALIASES:
            return click.Group.get_command(self, ctx, self._ALIASES[cmd_name])

        return None


@click.group(cls=AliasedGroup)
@click.option("-q", "--quiet", is_flag=True, default=False, help="Disables all output.")
@click.pass_context
def cli(ctx: click.Context, quiet):
    """A simple tool to download twitter medias."""
    if quiet:
        click.echo = null_print

    if ctx.invoked_subcommand == "authorize":
        return

    if not os.path.exists(Config.config_path):
        raise UsageError("Please run authorize first!")

    ctx.obj = Config.load()
    api, _, _ = create_api(
        ctx.obj.config_data["consumer_key"],
        ctx.obj.config_data["consumer_secret"],
        ctx.obj.config_data["access_token"],
        ctx.obj.config_data["access_token_secret"],
    )
    ctx.obj.api = api


@cli.command()
@click.pass_obj
def profile(config: Config):
    """Prints currently authorized user."""
    me = config.api.verify_credentials()
    click.echo(f"Authorized as {me.name} (@{me.screen_name})")


@cli.command()
@click.argument("consumer_key")
@click.argument("consumer_secret")
def authorize(consumer_key: str, consumer_secret: str):
    """Authorize OAuth and saves authentication info."""
    try:
        _, access_token, access_token_secret = create_api(consumer_key, consumer_secret)
    except TweepyException as e:
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
@click.option(
    "--username",
    "-u",
    default=None,
    help="Username to lookup. [Default: Current authenticated user]",
)
@click.option(
    "--count",
    "-c",
    default=1000,
    help="Number of liked post to download. [Default: 1000]",
)
@click.option(
    "--retweet",
    "-r",
    is_flag=True,
    default=False,
    help="Also download user's retweets.",
)
@click.option(
    "--only-retweet",
    is_flag=True,
    default=False,
    help="Download only user's retweets.",
)
@click.option(
    "--like",
    "-l",
    is_flag=True,
    default=False,
    help="Download user's likes instead of timeline and retweets.",
)
@click.option(
    "--output-dir",
    "-o",
    type=str,
    default="output",
    help="Set output directory where all medias will be downloaded. [Default: output]",
)
@click.option(
    "--format",
    "-f",
    "format_",
    type=str,
    default="{username}/{id}-{filename}",
    help="Format output filename with tokens. (Available tokens: id, extension, filename, url, username)",
)
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
    "--ignore-existing",
    is_flag=True,
    default=False,
    help="Ignore existing files. [Default: Replaces all downloaded files]",
)
@click.pass_context
@click.pass_obj
def download(
    config: Config,
    ctx: click.Context,
    username: Optional[str],
    count: int,
    since_date: Optional[str],
    max_date: Optional[str],
    since_id: int,
    max_id: int,
    retweet: bool,
    only_retweet: bool,
    output_dir: str,
    format_: str,
    like: bool,
    ignore_existing: bool,
):
    """Batch download medias from user's timeline or likes."""
    ctx.invoke(profile)
    if since_date:
        since_datetime = parse(since_date)
    else:
        since_datetime = datetime.min

    if max_date:
        max_datetime = parse(max_date)
    else:
        max_datetime = datetime.max

    condition = None
    if only_retweet:
        retweet = True
        condition = lambda x: hasattr(x, "retweeted_status")  # noqa

    try:
        method = config.api.get_favorites if like else config.api.user_timeline
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
                condition,
            )
        )

        click.echo("Fetching media metadatas...")
        medias = get_media_metadata(config.api, tweets_to_download)
        download_medias(medias, output_dir, format_, ignore_existing)
    except TweepyException as e:
        http_status = e.response.status_code
        if http_status == 401:
            raise click.ClickException("Unauthorized, please run authorize again.")
        elif http_status == 404:
            raise click.ClickException("User not found.")
        elif http_status >= 500:
            raise click.ClickException("A server error has occured, try again later.")
        raise e


if __name__ == "__main__":
    cli()
