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
$ tdl download --help
Usage: tdl download [OPTIONS]

Options:
  -c, --count INTEGER  Number of liked post to download.
  --max-date TEXT      Oldest date to download.
  --max-id INTEGER     Stops downloading after meeting this ID.
  --help               Show this message and exit.
```

## TODO
- Better README
- Help texts
- Testing