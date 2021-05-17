import os
from datetime import datetime
from typing import Any, Iterator, List, Optional, Tuple
from urllib.parse import urlparse

import click
import tweepy
from tweepy.models import Status


def create_api(
    consumer_key: str,
    consumer_secret: str,
    access_token: Optional[str] = None,
    access_token_secret: Optional[str] = None,
) -> Tuple[tweepy.API, str, str]:
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    if access_token and access_token_secret:
        auth.set_access_token(access_token, access_token_secret)
    else:
        redirect_url = auth.get_authorization_url()
        click.echo("Go to the following URL and log in: " + redirect_url)

        verifier = click.prompt("PIN")
        auth.get_access_token(verifier)

    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    return (api, auth.access_token, auth.access_token_secret)


def get_tweets(
    method,
    username: Optional[str],
    include_retweet: bool,
    min_id: Optional[int],
    max_id: Optional[int],
    min_datetime: datetime,
    max_datetime: datetime,
    limit: int,
) -> Iterator[Status]:

    tweet: Status
    for tweet in tweepy.Cursor(
        method,
        id=username,
        include_rts=include_retweet,
        include_entities=True,
        tweet_mode="extended",
        since_id=max_id,
        max_id=min_id,
    ).items(limit):
        if tweet.created_at > min_datetime:
            continue
        if tweet.created_at < max_datetime:
            break

        yield tweet


def get_media_url(media: dict):
    if media["type"] == "photo":
        return media["media_url_https"]
    else:
        available_videos = media["video_info"]["variants"]
        valid_videos = list(
            filter(lambda x: x["content_type"] == "video/mp4", available_videos)
        )
        valid_videos.sort(key=lambda x: x["bitrate"], reverse=True)
        return valid_videos[0]["url"]


def get_medias(api: tweepy.API, status_ids: List[int]):
    tweets = api.statuses_lookup(status_ids)

    medias = []
    for tweet in tweets:
        if "extended_entities" in tweet._json:
            for media in tweet.extended_entities["media"]:
                media_url = get_media_url(media)
                filename = os.path.basename(urlparse(media_url).path)

                # Set metadata to retweeted status, if it's a retweet.
                if hasattr(tweet, "retweeted_status"):
                    tweet = tweet.retweeted_status

                medias.append(
                    {
                        "id": tweet.id_str,
                        "username": tweet.user.screen_name,
                        "url": media_url,
                        "extension": filename[-3:],
                        "filename": filename,
                    }
                )

    return medias


def get_media_metadata(api: tweepy.API, tweets: List[Status]):
    medias = []
    with click.progressbar(chunks(tweets, 100), label="Fetching media URLs") as bar:
        for tweet_chunks in bar:
            tweet_ids = [t.id for t in tweet_chunks]
            medias.extend(get_medias(api, tweet_ids))
    return medias


# fmt: off
def chunks(lst: List[Any], n: int) -> Iterator[List[Any]]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
# fmt: on
