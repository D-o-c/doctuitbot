#!/usr/bin/env python

"""
Twittov

	twittov applies the Markov model to a user's Twitter feed. For more info, see:
		http://yaymukund.com/twittov/

	It depends on the BeautifulSoup module, which you can get at:
		http://www.crummy.com/software/BeautifulSoup/#Download

	It should also be noted that twittov creates a file .twittov.cache for caching,
	so we don't hammer the Twitter servers. However, the script never checks or
	updates the cache. This means if you tweet after twittov has cached your
	history, you'll need to remove .twittov.cache before your new tweets can get 
	indexed by the script.

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

import string, sys, urllib.request, urllib.error, random, pickle
from bs4 import BeautifulSoup, SoupStrainer
from optparse import OptionParser

def scrape(url): 

	"""	Returns a list of tweets, given a page like http://twitter.com/user?page=#
			If there aren't any tweets on the page, we return an empty list.
	"""

	tweets = []

	# We make a SoupStrainer to speed up parsing.
	entriesOnly  = SoupStrainer('span', 'entry-content')

	try:
	  page = urllib.request.urlopen(url).read()
	  entries = BeautifulSoup(page, parseOnlyThese = entriesOnly)

	except urllib.error.HTTPError as error:
		print ('The server couldn\'t fulfill your request.')
		print ('Error code:', error.code)
		exit(1)

	else:
		for entry in entries:
			# Strip tags, convert to string, append to list.
			tweet = entry.findAll(text = True)
			tweet = string.join(tweet).encode('utf-8')
			tweets.append(tweet)

	return tweets

def getTweets(username):

	""" Given a Twitter username, we scrape their entries and return them as a list.
	"""

	allTweets = []
	baseURL = 'http://www.twitter.com/' + username + '?page='
	pageNumber = 1

	finished = False

	if not options.quiet:
		sys.stdout.flush()
		sys.stdout.write('Loading ' + username + '\'s tweets ')

	while not finished:
		if not options.quiet:
			sys.stdout.flush()
			sys.stdout.write('|')

		tweets = scrape(baseURL + str(pageNumber))
		if not tweets: # Empty.
			finished = True
		else:
			allTweets.extend(tweets)
			pageNumber = pageNumber + 1

	if not options.quiet:
		print (' done!')
	if options.verbose:
		print ('Fetched {0} pages.'.format(pageNumber))
	
	return allTweets

def triples(words):
	
	""" Generates triples from the given data string. So if our string were
			"What a lovely day", we'd generate (What, a, lovely) and then
			(a, lovely, day).
	"""
	
	if len(words) < 3:
		return
	
	for i in range(len(words) - 2):
		yield (words[i], words[i+1], words[i+2])

class MarkovTable:

	""" This maintains a dictionary of Markov chains and heads.
	"""

	def __init__(self, data, name):
		
		self.name = name
		self.chains = {}
		self.heads = []
		self.tails = []

		try:
			self.chainify(data)
		except TypeError as e:
			if not options.quiet:
				print ('Error: Data contains at least one non-str, non-list element.')
			exit(1)

	def chainify(self, data):
		
		""" Processes the text and gathers a->b relations for the database. Input
				can be either a sequence of strings, or a single string.
		"""

		if isinstance(data, str):
			words = data.split()
			for i in range(words.count('@')):
				index = words.index('@')
				if index < len(words) - 1:
					words[index+1] = '@' + words[index+1]
				words.pop(index)

			if len(words) >= 3:
				head = (words[0], words[1])
				if head not in self.heads:
					self.heads.append(head)

				tail = (words[-2], words[-1])
				if tail not in self.tails:
					self.tails.append(tail)

			for w1, w2, w3 in triples(words):
				pair = (w1, w2)
				if pair not in self.chains:
					self.chains[pair] = [w3]
				else:
					self.chains[pair].append(w3)

		elif isinstance(data, list) or isinstance(data, tuple):
			for tweet in data:
				try:
					self.chainify(tweet)
				except TypeError:
					raise

		else:
			raise TypeError

	def genSeed(self, randomness):
	
		""" Uses the Markov chains to generate a single sentence. If we can't meet
				the randomness threshold, the function returns False.
		"""

		seed = random.choice(self.heads)
		text = [ seed[0], seed[1], random.choice(self.chains[seed]) ]

		branches = 0
		while (text[-2], text[-1]) in self.chains:
			results = self.chains[(text[-2], text[-1])]
			branches = branches + len(results) - 1
			text.append(random.choice(results))

			# If it's long and we're at a tail, we can stop.
			if len(text) >= 10 and (text[-2], text[-1]) in self.tails:
				break

			# We check to make sure we're not infinite looping.
			if len(text) >= 3 and text[-1] == text[-2] and text[-2] == text[-3]:
				break
			
		if branches < randomness:
			return False 

		text.append('\n')
		return text 

	def prettify(self, textArray):
	
		""" Converts the text to a string, and then converts to paragraphs.
		"""

		text = string.join(textArray)
		text = text.split('\n')

		i = 1
		length = len(text)
		while i < length:
			if not i % 6:
				i += 1
				text.insert(i, '\n\n')
			i += 1
			length = len(text)

		text = string.join(text).strip()
		return text

	def markov(self, length, randomness, text = ''):
	
		""" Uses our markov chains to generate text of a minimum no. words.
		"""

		# If text is empty, we have to generate a seed.
		tries = 0
		while not text:
			text = self.genSeed(randomness)
			tries += 1
			if tries > 100:
				print ('Couldn\'t produce a seed. Try decreasing the randomness.')
				exit(1)
		if len(text) >= length:
			return self.prettify(text)

		else:
			text.extend(self.genSeed(randomness))
			return self.markov(length, randomness, text)

"""	Routine script stuff. We parse the arguments, generate the database, and
		run the Markov algorithm. Note that we use the pickle() functions to cache
		everything in .twittov.cache.
"""

# Standard argument parsing using the optparse module.
parser = OptionParser(usage='Usage: twittov.py [options] username')
parser.set_defaults(verbose=False, quiet=False, randomness=15, length=1, cache='.twittov.cache', mustCache=False)

parser.add_option('-q', '--quiet', action='store_true', dest='quiet', help='Don\'t print status messages to stdout.')
parser.add_option('-v', '--verbose', action='store_true', dest='verbose', help='Print all messages to stdout.')
parser.add_option('-r', '--randomness', type='int', dest='randomness', help='Sets the randomness of the output. Must be an integer. Default is 15.')
parser.add_option('-l', '--length', type='int', dest='length', metavar='NUMWORDS', help='Sets the *minimum* output length, in number of words. NUMWORDS must be a positive integer. Default is 1.')
parser.add_option('-c', '--cache-file', dest='cache', type='string', metavar='FILE', help='Sets the cache file. By default, we save to .twittov.cache')
parser.add_option('-f', '--force-cache-update', action='store_true', dest='mustCache', help='Force download all tweets and update cache, even if username is already in cache.')

(options, args) = parser.parse_args()

# Check if the parameters are all well formed.
if len(args) != 1:
	parser.error('Incorrect number of arguments. Remember to specify a Twitter username.')
else:
	username = args[0]

if options.quiet and options.verbose:
	parser.error('"quiet" and "verbose" are mutually exclusive.')

if options.length <= 0:
	parser.error('Length must be a positive integer.')

# We're caching all previous chains for now, so we don't overload Twitter.
try:
	with open(options.cache, 'rb') as f:
		cache = pickle.load(f)
except IOError:
	if options.verbose:
		print ('Cannot open {0} for reading.'.format(options.cache))
	cache = {}
except EOFError:
	cache = {}
else:
	
	if options.verbose:
		print ('Loaded cache from "{0}" successfully.'.format(options.cache))
	f.close()

# If it's in the cache, let's not generate anything.
if not options.mustCache and username in cache:
	table = cache[username]
	found = True
	if options.verbose:
		print ('{0}\'s tweets are already cached.'.format(username))

# Otherwise, we should parse pages.
else:
	found = False
	tweets = getTweets(username)
	table = MarkovTable(tweets, username)
	cache[username] = table

	if not found:
		# Try to cache the new chains.
		try:
			f = open(options.cache, 'wb')
		except IOError:
			if not options.quiet:
				print ('Cannot open "{0}" for writing.'.format(options.cache))
		else:
			pickle.dump(cache, f)
			f.close()
			if not options.quiet:
				print ('Wrote "{0}" with data for {1}.'.format(options.cache, username))

print (table.markov(options.length, options.randomness))
