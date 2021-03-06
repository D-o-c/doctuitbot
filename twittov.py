#!/usr/bin/env python
"""Applies the Markov model to a user's Twitter feed.

  For more info, see:
    http://yaymukund.com/twittov/

  A TweetList holds a list of tweets for a Twitter username and defines functions
  for producing nonsensical text using a Markov algorithm.

    twittov is free software: you can redistribute it and/or modify it under the
    terms of the GNU General Public License as published by the Free Software
    Foundation, either version 3 of the License, or (at your option) any later
    version.

    twittov is distributed in the hope that it will be useful, but WITHOUT ANY 
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
    FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
    details.

    You should have received a copy of the GNU General Public License along
    with this program.  If not, see <http://www.gnu.org/licenses/>.

  Author:  Mukund Lakshman
  Contact: mhl008 [at] gmail [dot] com

"""

import string, sys, random, pickle
from optparse import OptionParser
from twython import Twython
from util import ingrams
from xml.dom import minidom
import xml.etree.cElementTree as ET


class TwitterAPIException(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

# Utility Functions
# =================
#
# Reusable functions to implement the Markov logic and scrape some amount of
# tweets from an account.

def markov(sequence, order, distribution=None, heads=None):
  """Process the text to gather a->b frequency distributions.

  For example:
  >>> pprint(frequency_distribution(
  ["Under","my","closet","I","found","cats","and","a","bat"],2))

  {('I', 'found'): set(['cats']),
  ('Under', 'my'): set(['closet']),
  ('and', 'a'): set(['bat']),
  ('cats', 'and'): set(['a']),
  ('closet', 'I'): set(['found']),
  ('found', 'cats'): set(['and']),
  ('my', 'closet'): set(['I'])}

  We can also apply this algorithm to letters:
   >>> pprint(db.frequency_distribution("Cats and a bat.",2))

  {(' ', 'a'): set([' ', 'n']),
   (' ', 'b'): set(['a']),
   ('C', 'a'): set(['t']),
   ('a', ' '): set(['b']),
   ('a', 'n'): set(['d']),
   ('a', 't'): set(['.', 's']),
   ('b', 'a'): set(['t']),
   ('d', ' '): set(['a']),
   ('n', 'd'): set([' ']),
   ('s', ' '): set(['a']),
   ('t', 's'): set([' '])}

  Keyword arguments:
  sequence -- A sequence of characters or words.
  order -- The order of the Markov model.
  distribution -- If specified, add to an existing frequency distribution.
  heads -- If specified,  add heads to an existing set.

  """
  # If the sequence is too short, exit quietly.
  if len(sequence) < order+1:
    return;

  if distribution is None:
    distributon = {}
  if heads is None:
    heads = set()

  heads.add(tuple(sequence[:order]))

  for ngram in ingrams(sequence, order+1):
    prefix = ngram[:-1]
    suffix = ngram[-1]

    if prefix not in distribution:
      distribution[prefix] = set([suffix])
    else:
      distribution[prefix].add(suffix)

  return distribution, heads

def get_tweets(username, amount, AK, AS, OT, OTS):
  """Given a Twitter username, scrape up to $amount entries.

  We do not fetch exactly $amount tweets. The account may not have $amount tweets,
  or we might skip over a few tweets if they are @replies or retweets.

  Keyword arguments:
  username -- The string username of the twitter user.
  amount -- The number of tweets to scrape.

  """
  tweets = []
  twitter = Twython(AK, AS, AT, ATS)	#APP_KEY, APP_SECRET, AUTH_TOKEN, AUTH_TOKEN_SECRET

  finished = False
  page = 1
  while not finished:

    if amount <= 200:
      # Make the API call.
      search_results = twitter.get_user_timeline(screen_name=username,
          page=str(page), count=str(amount))
      finished = True

    else:
      # Make the API call.
      search_results = twitter.get_user_timeline(screen_name=username,
          page=str(page), count='200')
      amount -= 200
      page += 1

    if isinstance(search_results, dict) and search_results['error']:
      raise TwitterAPIException(str(search_results['error']))
    elif not search_results:
      raise TwitterAPIException('User has no tweets.')

    for result in search_results:
      tweets.append(result['text']) 

  return tweets

class TweetList:
  def __init__(self, username, num_tweets, AK, AS, AT, ATS):
    self.username = username
    self.tweets = get_tweets(username, num_tweets, AK, AS, AT, ATS)	#APP_KEY, APP_SECRET, AUTH_TOKEN, AUTH_TOKEN_SECRET

  def generate_text(self, order, length, split_words):
    """Use the Markov chains to generate text.

    Keyword arguments:
    order -- The order of the Markov model.
    heads -- A set of heads, or strings to start from.
    length -- How much text, in characters, should we generate?
    split_words -- If true, we apply Markov to letters rather than words.

    """
    distribution, heads = self._generate_distribution(order, split_words)
    prefix = random.sample(heads, 1)[0] # Pick a random head.
    text = list(prefix)

    # Count the letters.
    current_length = sum([ len(i) for i in text ])

    while current_length < length:
      if prefix in distribution:
        suffix = random.sample(distribution[prefix], 1)[0]
        text.append(suffix)
        current_length += len(suffix)
        # Readjust the prefix.
        prefix = tuple(text[-order:])

      # If we have reached the end of a chain, start a new one.
      else:
        # Mark the end of a sentence.
        if split_words:
          text.append(' ')

        prefix = random.sample(heads, 1)[0]
        text.extend(prefix)
        current_length += sum([ len(i) for i in prefix])

    if split_words:
      separator = ''
    else:
      separator = ' '

    return separator.join(text).encode('utf-8')

  def _generate_distribution(self, order, split_words):
    """Apply the Markov algorithm repeatedly to self.tweets.

    Keyword arguments:
    order -- The order of the Markov model.
    split_words -- If true, we apply Markov to letters rather than words.

    """
    distribution = {}
    heads = set()

    for tweet in self.tweets:
      if not split_words:
        tweet = tweet.split()
      markov(tweet, order, distribution, heads)

    return distribution, heads

# Routine script stuff. We parse the arguments, generate the database, and
# run the Markov algorithm. Note that we use the pickle() functions to cache
# everything in .twittov.cache.
if __name__ == '__main__':

    
    # Standard argument parsing using the optparse module.
    parser = OptionParser(usage='Usage: twittov.py [options] username')
    parser.set_defaults(length=160, split_words=False, cache='.twittov.cache', must_cache=False, order=3, cache_size=200, verbose=False)

    parser.add_option('-l', '--length', type='int', dest='length', metavar='LENGTH', help='Set the *minimum* output length in characters. LENGTH must be a positive integer. Default is 160.')
    parser.add_option('-c', '--cache-file', dest='cache', type='string', metavar='FILE', help='Sets the cache file. By default, we save to .twittov.cache')
    parser.add_option('-f', '--force-cache-update', action='store_true', dest='mustCache', help='Force download all tweets and update cache, even if username is already in cache.')
    parser.add_option('-s', '--cache-size', type='int', dest='amount', default=200, help='How many tweets to scrape. Default is 200.')
    parser.add_option('-o', '--order', type='int', dest='order', help='The order of the markov chains. Default is 3.')
    parser.add_option('-x', '--split', action='store_true', dest='split_words', metavar='SPLIT', help='If set, operates on groups of letters rather than words.')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose', metavar='SPLIT', help='If set, displays verbose output.')
    parser.add_option('--API_KEY', type='string', dest='AK', default='0', help='Your API Key')
    parser.add_option('--API_SECRET', type='string', dest='AS', default='0', help='Your API Secret')
    parser.add_option('--ACCESS_TOKEN', type='string', dest='AT', default='0', help='Your Access Token')
    parser.add_option('--ACCESS_TOKEN_SECRET', type='string', default='0', dest='ATS', help='Your Access Token Secret')

    (options, args) = parser.parse_args()

    # Check if the parameters are all well formed.
    if len(args) != 1:
      parser.error('Incorrect number of arguments. Remember to specify a Twitter username.')
    else:
      username = args[0]

    if options.length <= 0:
      parser.error('Length must be a positive integer.')

    if options.cache_size <= 0:
      parser.error('Cache size must be a positive integer.')

    # We're caching all previous chains for now, so we don't overload Twitter.
    try:
      f = open(options.cache, 'rb')
    except IOError:
      if options.verbose:
        print ("Cannot open %s for reading." % options.cache)
      cache = {}
    else:
      cache = pickle.load(f)
      if options.verbose:
        print ("Loaded cache from %s successfully." % options.cache)
      f.close()

    # If it's in the cache, let's not generate anything.
    if not options.mustCache and username in cache:
      tweets = cache[username]
      found = True
      if options.verbose:
        print ("%s\'s tweets are already cached." % username)

    # Otherwise, we should parse pages.
    else:
      if (options.AK=='0' or options.AS=='0' or options.AT=='0' or options.ATS=='0'): #nothing in input
        try: #try to open xml file and search key element
          tok_doc = minidom.parse('.td')
          itemlist = tok_doc.getElementByTagName('key')
          AK=itemlist[0]
          AS=itemlist[1]
          AT=itemlist[2]
          ATS=itemlist[3]
        except IOError: #if failed, ERROR
          print ("There aren't token saved or in input. The application will close.")
          sys.exit(1)
        print ('No input data, using saved data')

      else:
        try: #try to open xml file
          tok_doc = minidom.parse('.td')
          itemlist = tok_doc.getElementByTagName('key')
          rx = raw_input('Saved data found, would you like to replace it?[Y/n]') #replace data found?

          if (rx!='n'): #YES

            remove('.td') #rimuovo file e riscrivo
            root = ET.element('root')
            keys = ET.SubElement(root, 'keys')
            key1 = ET.SubElement(keys, 'key')
            key1.text = options.AK
            key2 = ET.SubElement(keys, 'key')
            key2.text = options.AS
            key3 = ET.SubElement(keys, 'key')
            key3.text = options.AK
            key4 = ET.SubElement(keys, 'key')
            key4.text = options.AK
            tree = ET.ElementTree(root)
            tree.write('.td')
          

        except IOError: #file not exist, write it
          root = ET.element('root')
          keys = ET.SubElement(root, 'keys')
          key1 = ET.SubElement(keys, 'key')
          key1.text = options.AK
          key2 = ET.SubElement(keys, 'key')
          key2.text = options.AS
          key3 = ET.SubElement(keys, 'key')
          key3.text = options.AK
          key4 = ET.SubElement(keys, 'key')
          key4.text = options.AK
          tree = ET.ElementTree(root)
          tree.write('.td')

        AK = options.AK
        AS = options.AS
        AT = options.AT
        ATS = options.ATS
        
      
      found = False
      cache[username] = TweetList(username,
                                  options.amount,
                                  AK,   #APP_KEY
                                  AS,   #APP_SECRET
                                  AT,   #AUTH_TOKEN
                                  ATS)  #AUTH_TOKEN_SECRET
      tweets = cache[username]

      if not found:
        # Try to cache the new chains.
        try:
          f = open(options.cache, 'w')
        except IOError:
          if options.verbose:
            print ("Cannot open %s for writing." % options.cache)
        else:
          print (type(cache))
          print (type(f))
          pickle.dump(cache, f)
          f.close()
          if options.verbose:
            print ("Wrote %s with data for %s." % (options.cache, username))

    print (tweets.generate_text(options.order, options.length, options.split_words))
