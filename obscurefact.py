#/usr/lib/python2.7
# GPL'd; see LICENSE.
# Copyright 2013 Sumana Harihareswara, 2014 Frances Hocutt
# For a Wikipedia article: find the most obscure fact and tweet it.
# Twitter bot: @autowikifacts
#
# Tweets an obscure sentence from the most-recently changed Wikipedia page. 

import requests
import random
import twitter
import string

from twitterapi import api                     #TODO: fuss with folders etc.



# User-agent string for API neighborliness
headers =  {'User-Agent': 'obscure-fact project (https://github.com/fhocutt/), using Python requests library'}
    
##############
# wikipedia

def wikipediarecentchange():
# Finds the title and pageid of the most recently changed en.wikipedia page,
# ignoring bot and minor edits. Returns the tuple (title, pagetext).

# returns json-formatted text of page among other things
    URI = 'http://en.wikipedia.org/w/api.php?action=query&generator=recentchanges&grcshow=!bot|!minor&grcprop=title|ids&grcnamespace=0&grclimit=1&prop=extracts&format=json&explaintext=&redirects=&indexpageids'
    r = requests.get(URI, headers=headers)
    
    rtext = r.json()
    
    pageid = rtext["query"]["pageids"][0]
    
    title = rtext["query"]["pages"][pageid]["title"]
    pagetext = rtext["query"]["pages"][pageid]["extract"]
    
    return (title, pagetext)


############
# wikidata


def wikidata(): 
    recentchanges = wikidatarecentchanges()
#random title from the list, then English label and list of claims
    entity = recentchanges[random.randint(0, len(recentchanges)-1)]["title"]

    entitydata = getlabelclaims(entity)


    while (("claims" not in entitydata["entities"][entity]) or ("labels" not in entitydata["entities"][entity])): #TODO: split this line somehow

        entity = recentchanges[random.randint(0, len(recentchanges)-1)]["title"]
        entitydata = getlabelclaims(entity)
        #might want to put in a guarantee this ends someday...naaaah. #TODO

    label = entitydata["entities"][entity]["labels"]["en"]["value"]
    claims = entitydata["entities"][entity]["claims"]

    prop, claimvalue = randomclaim(claims)

    return (label, prop, claimvalue)

#API query to get the 100 most recent changes
def wikidatarecentchanges():
    URI = "http://wikidata.org//w/api.php?action=query&list=recentchanges&format=json&rcnamespace=0&rcprop=title&rcshow=!minor|!bot|!redirect&rclimit=100&rctype=edit|new"
    r = requests.get(URI, headers = headers)
    rtext = r.json()
    recentchanges = rtext["query"]["recentchanges"]
    return recentchanges


#finds the first English label of a given item
def findlabel(entity):

    URI = "http://wikidata.org/w/api.php?action=wbgetentities&format=json&ids=%s&props=labels&languages=en" % entity
    r = requests.get(URI, headers = headers)
    rtext = r.json()

    print rtext

    label = rtext["entities"][entity]["labels"]["en"]["value"]

    return label


#finds the label of a given item and a list of associated claims
def getlabelclaims(entity):

    URI = "http://wikidata.org/w/api.php?action=wbgetentities&format=json&ids=%s&props=labels|claims&languages=en&ungroupedlist=" % entity
    r = requests.get(URI, headers = headers)
    rtext = r.json()
    print rtext

    return (rtext)


def randomclaim(claims):
    print "\n\nclaims:\n"+str(claims)
    randclaim = claims[0]
    if len(claims) > 1:
        randclaim = claims[random.randint(0, len(claims)-1)]
    prop = randclaim["mainsnak"]["property"]
    proplabel = findlabel(prop)    #FAILS if prop has no label
    claimvalue = randclaim["mainsnak"]["datavalue"]["value"]
    claimtype = randclaim["mainsnak"]["datavalue"]["type"]

    if claimtype == "wikibase-entityid":
         claimvalue = findlabel("Q"+ str(claimvalue["numeric-id"])) # so very wasteful... FIXME

    return proplabel, claimvalue


#############
# wikivoyage

def wikivoyagerecentchange():
# Finds the title and pageid of the most recently changed en.wikivoyage page,
# ignoring bot and minor edits. Returns the tuple (title, pagetext).
# TODO: only the URI differs from wikipediarecentchange(), could refactor

    URI = 'http://en.wikivoyage.org/w/api.php?action=query&generator=recentchanges&grcshow=!bot|!minor&grcprop=title|ids&grcnamespace=0&grclimit=1&prop=extracts&format=json&explaintext=&redirects=&indexpageids'
    
    r = requests.get(URI, headers=headers)

    rtext = r.json()

    pageid = rtext["query"]["pageids"][0]
    
    title = rtext["query"]["pages"][pageid]["title"]
    pagetext = rtext["query"]["pages"][pageid]["extract"]
    
    return (title, pagetext)




############
# wikibooks

def wikibooksrecentchange():
# Returns the title and most specific section/category/page of a random recently 
# changed wikibooks page, ignoring bot and minor edits.
# Returns the tuple (book title, chapter).

    #API call returns a list of the 100 most-recently-edited wikibooks pages 

    URI = 'http://en.wikibooks.org/w/api.php?action=query&list=recentchanges&format=json&rcnamespace=0&rcprop=title&rcshow=!minor|!bot|!redirect&rclimit=100&rctype=edit|new&rctoponly=&indexpageids='
    r = requests.get(URI, headers=headers)
    rtext = r.json()

    #gets the title of a random page of the 100 returned, for more randomness
    title = rtext["query"]["recentchanges"][random.randint(0, 99)]["title"]
    titleparts = title.split("/")
    book = titleparts[0]
    chapter = titleparts[len(titleparts)-1]
    return (book, chapter)


############
# wikisource


#def wikisourcerandom():


# Finds the title and page of a random wikiquote page.
# Returns the tuple (title, chapter).


#    return (title, chapter)



############
# more general methods

##def choosetopic():
###not used; may use this to get random info on a tweeted topic later
##    a = raw_input("What topic do you want to know about? ")
##    return a


# User chooses site on command line. Acceptable answers:
# Wikipedia, Wikivoyage, Wikibooks

#TODO: extend the inputs to get an @-tweet from the twitter API

# does the API call, returns text or error
def choosesite():

    # which site do we query?
    site = raw_input("Would you like information from Wikipedia, Wikivoyage, \
Wikidata, or Wikibooks?\n") #could insert these from a separate list for easier maintenance
    site = string.lower(site) #handling case
    site = string.strip(site) #removing whitespace

    if site == "wikipedia":
        topic, text = wikipediarecentchange()
        sentence = findobscuresentence(text)
        obscurefact = "%s: %s" % (topic, sentence)
        return ("WP", obscurefact)

    elif site == "wikivoyage":        
        location, text = wikivoyagerecentchange()
        sentence = findobscuresentence(text)
        obscurefact = "%s: %s" % (location, sentence)
        return ("WV", obscurefact)

    elif site == "wikibooks":
	title, section = wikibooksrecentchange()
        if title == section: 
            obscurefact = title
        else:
            obscurefact = "%s: %s" % (title, section)
        return ("WB", obscurefact)

    elif site == "wikidata":
        label, prop, claimvalue = wikidata() 
        obscurefact = "(%s) %s (%s)" % (label, prop, claimvalue)
        return ("WD", obscurefact )

    else:  #re-prompt
        print "Please enter one of the options in the list or hit ctrl+C to end this program. \n"
        choosesite()


##def tweetedsite():                               #TODO: write code for this
### takes in the content of a tweet to @autowiki, returns wikisource/wikibooks/etc
### otherwise tweet out error msg listing valid inputs
##    tweet = [twitter method to get tweets]
##    if tweet contains "data", return wikidata
##    etc. 
##    else tweet out "@[user], please ask for one of these: ..."
##            #see if I need anything else


def findobscuresentence(pagetext): # expects Wikipedia-style plaintext
# Returns the first sentence of the longest section's final paragraph

# TODO: should probably use regex for better split.  Also, check out docutils.
    sectionlist = pagetext.split(" ==\n")
    section = max(sectionlist, key = len) 
    para = section.split('/n')[-1]
    sentence = para.split(". ")[0] # this doesn't catch "./n" as an ending
    return sentence


##def findrandomsentence(pagetext):
###not currently used; may let the user choose later
##    sectionlist = pagetext.split(" ==/n")
##    section = random.choice(sectionlist)
##    sentencelist = section.split(". ")
##    sentence = random.choice(sentencelist)
##    return sentence


def tweet(site, obscurefact):
    tweet = "(%s) %s" % (site, obscurefact)

    if len(obscurefact) > 140:   #shorten to <=140 chars
        tweet = tweet[:139]

    api.PostUpdate(tweet)


#Get the user to choose a site to tweet out, tweet the result, and print it 
#to the command line for immediate gratification/debugging.
def run():
    site, obscurefact = choosesite()
    tweet(site, obscurefact)
    print "(%s) %s\n" % (site, obscurefact)


if __name__ == "__main__":
    run()
