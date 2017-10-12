import numpy as np
import sys
from googleapiclient.discovery import build
import urllib2
import urllib
import base64
import json
import sys
import math
import re
from nltk.stem import PorterStemmer

def getQueryResults(query, apiKey, engineId, service):
    '''
    getQueryResults takes query and returns the top 10 results
    args:
        query - list of words that make up query
        apiKey - Google Custom Search API Key
        engineId - Google Custom Search Engine ID
        service - service obj for interacting with search API
    output:
        results - top 10 results of query
    '''
    res = service.cse().list(q=query, cx=engineId, num=10).execute()
    results = []
    for i in res['items']:
        results.append({'url': i['formattedUrl'], 'title': i['title'], 'summary': i['snippet']})
    print("results", results)
    return results 

def getFeedback(results):
    '''
    takes the results, and gets user feedback for the results
    args:
        results - list of query results
    output:
        feedback - feedback for input results, 1 for relevant, 0 for irrelevant
    '''
  
    wordlist=[] #list of total words in all the 10 web results,as returned by Bing
    vector={} #For creating vectors based on the Vector-Model theory
    relevance=0
    feedback = {}
    notrelvant ={}
    print("Google Search Results:\n=====================")
    count = 0
    s = 0
    
    for i in results:
        words=[]
        count+=1
        print("Result "+str(count))
        print("[")
        print("URL: "+i['url'])
        print("Title: "+i['title'])
        print("Summary: "+i['summary'])
        print("]")
        words=words+re.split("\s|(?<!\d)[^\w']+|[^\w']+(?!\d)", i['title'])
        words=words+re.split("\s|(?<!\d)[^\w']+|[^\w']+(?!\d)", i['summary'])
        words = [x.lower() for x in words]
        words = filter(None, words)
        words = [str(w) for w in words]
        
        for wi,w in enumerate(words):
            poswt = 3.0/posWeight(wi,query,words)
            if w in invl:
                if i['url'] in invl[w]:
                    invl[w][i['url']]+= 1*poswt
                else:
                    invl[w][i['url']]= 1*poswt
            else:
                invl[w]={i['url']: 1*poswt}
            
        wordlist=wordlist+words
        f = raw_input("Relevant(Y/N)?")
        if f.upper()=="Y":
            relevance+=1
            s+=1
            feedback[i['url']]=[i['title'],i['summary']]
        else:
            s+=1
            if len(notrelvant) == 0:
                notrelvant[i['url']]=[i['title'],i['summary']]
            

    return feedback,notrelvant,words,wordlist,relevance,s,vector

def expandQuery(query, results, feedback, notrelvant, wordlist):
    '''
    takes original query, query results, and result feedback,
    and formulates and new query
    args:
        query - query from last iteration
        results - top 10 results from query
        feedback - relevance feedback for results
    output:
        newQuery - expanded query based on inputs
    '''
    for w in re.split(r"[^\w']+",query):
            if w in invl:
                if 'Query' in invl[w]:
                    invl[w]['Query']+=1
                else:
                    invl[w]['Query']=1
            else:
                invl[w]={'Query':1}


        #Creating vector representations for each document returned by Google Custom API and 
    wordlist=sorted(set(wordlist))
    for u in results:
        vector[u['url']]=[0]*len(wordlist)  #Initializing the vector of each doc by zero,dimension equal to total words in corpus
        for i,word in enumerate(wordlist):
            vector[u['url']][i]=getweight(word,u['url'])
    vector['Query']=[0]*len(wordlist)  #Initializing the vector for the Query
    for i,word in enumerate(wordlist):
        vector['Query'][i]=getweight(word,'Query')
          
    alpha=1
    beta=1
    gamma=1

    #IDE DEC HI ALGORITHM
    newQuery=[0]*len(wordlist)  #Initializing the vector for the modified/new query
    newQuery=[ x+alpha*y for x,y in zip(newQuery,vector['Query']) ]
    for k in list(feedback.viewkeys()):
        #new_query = [x + (beta*y/len(r)) for x,y in zip(new_query,vector[k] )]  normalization in rocchio algo
        newQuery = [x + (beta*y) for x,y in zip(newQuery,vector[k] )]
    for k in list(notrelvant.viewkeys()):
        #new_query = [x - (gamma*y/len(nr)) for x,y in zip(new_query,vector[k] )] normalization done for rocchio
        newQuery = [x - (gamma*y) for x,y in zip(newQuery,vector[k] )]

    #Modifying Query
    count = 0


    #Run till the new words to be added to the old query become 2 in number
    while count < 2:
        wordtoadd = wordlist[newQuery.index(max(newQuery))]  #Extracting the word with maximum weight from the new query

        #If the word to be added to old query,as calculated, is not already in the Query,and moreover if it is not a stop word
        #only then add it to form the new query
        st = PorterStemmer()
        stemmed = st.stem(wordtoadd)
        if wordtoadd not in query.lower() and wordtoadd not in stopwords and stemmed not in query.lower():
            count += 1
            query += ' ' + wordlist[newQuery.index(max(newQuery))]
            wordlist.remove(wordlist[newQuery.index(max(newQuery))])  #Removed from corpus,so that it's not considered again
            newQuery.remove(max(newQuery))
        else:
            wordlist.remove(wordlist[newQuery.index(max(newQuery))])
            newQuery.remove(max(newQuery))

    print query
    return query




def printUsage():
    '''
    prints usage instructions for this file
    '''
    print('Usage: proj1.py <API Key> <Engine Key> <Precision> <Query>')
    return

def printParams(apiKey, engineId, precision, query):
    '''
    prints parameters to main
    args:
        apiKey - Google Custom Search API Key
        engineId - Google Custom Search Engine ID
        precision - target value for precision, between 0 and 1
        query - list of words that make up query
    '''
    print("Parameters:")
    print("Client key ="+apiKey)
    print("Engine key ="+engineId)
    print("Query ="+query)
    print("Precision ="+str(precision))
    return

#posWeight() Returns positional weight for a word, proportional to its distance
#from the nearst query term in the document
#For Example, for a query "woods", and a document "tiger woods plays golf", the positional weight for golf = 3/2,
#positional weight for tiger = 3/1. So closer terms get bigger weights.
def posWeight(i,searchString,words):
    slist = searchString.split()
    #Taken an arbitrary large value in Matches, Matches stores the index of search terms where found in words
    matches = [1000]
    for s in slist:

        matches += [ii for ii,x in enumerate(words) if x==s.lower()]
        
    #store min distance from any search term from i
    dist = sorted([math.fabs(x-i) for x in matches])[0]
    
    if dist == 0:
        return 3
    else:
        return dist

stopwords = [line.strip() for line in open('stopwords.txt')]
stopwords = set(stopwords)

#getweight() Returns weights, given the word and url/doc
def getweight(word,url):
    st = PorterStemmer()
    stemmedword = st.stem(word)
    if url not in invl[word]:
        return 0
    tf = invl[word][url] #term frequency
    tf2 = 0

    #Example:
    #If the query has 'fruits',but the document has 'fruit' in it,we would want that 'fruits' should get the term frequency of                      #itself(if it is present) plus the term frequency of 'fruit' ideally,so that 'fruits' has some weight,else its weight will                      #be zero and that doc will not be retrieved
    if stemmedword in invl and stemmedword != word and stemmedword not in stopwords:
        if url in invl[stemmedword]:
            tf2 = invl[stemmedword][url] #term frequency for stemmed word

    df=len(invl[word]) #document frequency
    tfidf=(1+math.log(tf+tf2)*math.log(10.0/df)) #TF-IDF weight is the TermFrequency of the word times the Inverse Document Frequency
    return tfidf

if __name__ == "__main__":

    invl={} #Inverted index
    if len(sys.argv) !=5:
        printUsage()
    else:
        apiKey = sys.argv[1]
        engineId = sys.argv[2]
        targetPrecision = float(sys.argv[3])
        query = sys.argv[4]
        printParams(apiKey, engineId, targetPrecision, query)
        precision = 0
        service = build("customsearch", "v1", developerKey=apiKey)
        count=0
        while precision < targetPrecision:
            count+=1
            results = getQueryResults(query, apiKey, engineId, service)
            if len(results)<10:
                print("Error: less than 10 results. Exiting.")
                break
            feedback,notrelvant,words,wordlist,relevance,s,vector = getFeedback(results)
            precision = float(relevance)/float(s)
            print("iteration "+str(count)+ " precision:"+str(precision))
            if precision == 0:
                print("Error: no relevant results. Exiting")
                break
            elif precision < targetPrecision:
                query = expandQuery(query, results, feedback,notrelvant, wordlist)
