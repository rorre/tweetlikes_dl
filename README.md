# Twitter Likes Downloader

## Usage
1. Get consumer key and consumer secret from [Developer Console](http://developer.twitter.com/)
2. Install this thing with poetry.
```bash
$ poetry install
```
3. Authorize your account.
```bash
$ tdl authorize <CUSTOMER_KEY> <CUSTOMER_SECRET>
```
4. Download whatever you want.
```
$ tdl --help

Usage: tdl [OPTIONS] COMMAND [ARGS]...

  A simple tool to download twitter medias.

Options:
  -q, --quiet  Disables all output.
  --help       Show this message and exit.

Commands:
  authorize  Authorize OAuth and saves authentication info.
  download   Batch download medias from user's timeline or likes.
  profile    Prints currently authorized user.
```

```
$ tdl download --help
Usage: tdl download [OPTIONS]

  Batch download medias from user's timeline or likes.

Options:
  -u, --username TEXT    Username to lookup. [Default: Current authenticated
                         user]
  -c, --count INTEGER    Number of liked post to download. [Default: 1000]
  -r, --retweet          Also download user's retweets.
  --only-retweet         Download only user's retweets.
  -l, --like             Download user's likes instead of timeline and
                         retweets.
  -o, --output-dir TEXT  Set output directory where all medias will be
                         downloaded. [Default: output]
  -f, --format TEXT      Format output filename with tokens. (Available
                         tokens: id, extension, filename, url, username)
  --max-date TEXT        Most recent date to download.
  --since-date TEXT      Oldest date to download.
  --max-id INTEGER       Starts downloading after meeting this ID. (Most
                         recent one)
  --since-id INTEGER     Stops downloading after meeting this ID. (Oldest one)
  --ignore-existing      Ignore existing files. [Default: Replaces all
                         downloaded files]
  --help                 Show this message and exit.
```

## TODO
- Better README
- ~~Help texts~~
- Download List timeline
- Testing