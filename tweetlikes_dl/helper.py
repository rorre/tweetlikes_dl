from typing import Any, List, Optional, Tuple, Iterator

import click
import tweepy
from tweepy.models import ResultSet, Status


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

    api = tweepy.API(auth, wait_on_rate_limit=True)
    return (api, auth.access_token, auth.access_token_secret)


def get_favorites(
    api: tweepy.API,
    start_id: Optional[int] = None,
    end_id: Optional[int] = None,
) -> ResultSet[Status]:
    return api.favorites(
        count=200,
        since_id=start_id,
        max_id=end_id,
        include_entities=True,
    )


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
                medias.append(
                    {
                        "id": tweet.id_str,
                        "username": tweet.user.screen_name,
                        "url": get_media_url(media),
                    }
                )

    return medias


# fmt: off
def chunks(lst: List[Any], n: int) -> Iterator[List[Any]]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
# fmt: on
