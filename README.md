doctuitbot
==========

Authors: Mattia Pini, Emanuele Tironi <br>
Version: 1.1

_(Very very bugged)_

Fork of:<br>
 **Twittov**<br>
 Author: Mukund Lakshman<br>
 Website: http://www.twittov.com/<br>
 Version: 1.0<br>

Twittov is a simple script that generates nonsense from your tweets.

Usage: `twittov.py [options] username`

Options | meanings
-------------|------------
`-h`, `--help` | show this help message and exit
`-l LENGTH`, `--length=LENGTH` | Set the *minimum* output length in characters. LENGTH must be a positive integer. Default is 160.
`-c FILE`, `--cache-file=FILE` | Sets the cache file. By default, we save to twittov.cache
`-f`, `--force-cache-update` | Force download all tweets and update cache, even if username is already in cache.
`-s AMOUNT`, `--cache-size=AMOUNT` | How many tweets to scrape. Default is 200.
`-o ORDER`, `--order=ORDER` | The order of the markov chains. Default is 3.
`-x`, `--split` | If set, operates on groups of letters rather than words.
`-v`, `--verbose` | If set, displays verbose output.
