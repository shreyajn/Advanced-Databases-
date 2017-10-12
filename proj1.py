import numpy as np
import sys
import re
import operator
from googleapiclient.discovery import build

stopWordString = "a,about,above,after,again,against,all,am,an,and,any,are,arent,as,at,be,because,been,before,being,below,between,both,but,by,cant,cannot,could,couldnt,did,didnt,do,does,doesnt,doing,dont,down,during,each,few,for,from,further,had,hadnt,has,hasnt,have,havent,having,he,hed,hes,her,here,heres,hers,herself,him,himself,his,how,hows,i,id,im,ive,if,in,into,is,isnt,it,its,itself,lets,me,more,most,mustnt,my,myself,no,nor,not,of,off,on,once,only,or,other,ought,our,ours,ourselves,out,over,own,same,shant,she,shes,should,shouldnt,so,some,such,than,that,thats,the,their,theirs,them,themselves,then,there,theres,these,they,theyd,theyll,theyre,theyve,this,those,through,to,too,under,until,up,very,was,wasnt,we,weve,were,werent,what,whats,when,whens,where,wheres,which,while,who,whos,whom,why,whys,with,wont,would,wouldnt,you,youd,youll,youre,youve,your,yours,yourself,yourselves"
stopWords = stopWordString.split(",")

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
    return results

def getFeedback(results):
    '''
    takes the results, and gets user feedback for the results
    args:
        results - list of query results
    output:
        feedback - feedback for input results, 1 for relevant, 0 for irrelevant
    '''
    feedback = []
    print("Google Search Results:\n=====================")
    count = 0
    for i in results:
        count+=1
        print("Result "+str(count))
        print("[")
        print("URL: "+i['url'])
        print("Title: "+i['title'])
        print("Summary: "+i['summary'])
        print("]")
        f = input("Relevant(Y/N)?")
        if f.upper()=="Y":
            feedback.append(1)
        else:
            feedback.append(0)
    print("feedback", feedback)
    return feedback

def processWord(token):
    '''
    takes a word and process to remove punctuation etc
    args:
        token - input token string
    output:
        words - output list of words parsed from token
    '''
    words = []
    word = re.sub('[^0-9a-zA-Z]+', '', token)
    word = word.lower()
    if len(word)>2 and (word not in stopWords):
        words.append(word)
    return words

def parseWords(aString):
    '''
    takes a string and parses it into a list of words
    args:
        aString - input string to be parsed
    output:
        words - list of words parsed from string
    '''
    #replace '-' and '\n' with space to split into diff words
    aString = aString.replace("-", " ")
    aString = aString.replace("\n", " ")
    tokens = aString.split(" ")
    words = []
    for t in tokens:
        wordList = processWord(t)
        for w in wordList:
            words.append(w)
    return words

def expandQuery(query, results, feedback):
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
    #create dictionaries of word appearance in docs
    relDict = {} #relevant
    nRelDict = {} #not relevant
    wordFreqDict = {} #all docs

    queryWords = parseWords(query)
    for f in range(len(feedback)):
        relevantResult = results[f]
        wordList1 = parseWords(relevantResult['title'])
        wordList2 = parseWords(relevantResult['summary'])
        wordSet = set()
        for w in wordList1:
            wordSet.add(w)
        for w in wordList2:
            wordSet.add(w)
        for w in wordSet:
            if w in wordFreqDict:
                wordFreqDict[w] +=1
            else:
                wordFreqDict[w] = 1
            if feedback[f]==1:
                if w in relDict:
                    relDict[w]+=1
                else:
                    relDict[w]=1
                if w not in nRelDict:
                    nRelDict[w]=0
            elif feedback[f]==0:
                if w in nRelDict:
                    nRelDict[w]+=1
                else:
                    nRelDict[w] = 1
                if w not in relDict:
                    relDict[w]=0

    #calculate prob of each word given relevance
    probDict = {}
    numResults = len(feedback)
    numRel = sum(feedback)
    numNRel = numResults - numRel
    probList = []
    for word in wordFreqDict.keys():
        if word in queryWords:
            continue
        if wordFreqDict[word] == numResults:
            continue
        probRel = float(relDict[word])/float(numRel)
        probNRel = float(nRelDict[word])/float(numNRel)
        probDict[word] = [probRel, probNRel]
        probList.append([word, probRel, probNRel])

    #sort by relevance probability and append the highest probability
    count = 0
    newQuery = query
    #get the highest relevant probability with the lowest non-relevant probability
    sortedList = sorted(probList, key=operator.itemgetter(2))
    sortedList = sorted(sortedList, key=operator.itemgetter(1), reverse=True)
    for item in sortedList:
        if count<2:
            newQuery = newQuery + " " + item[0]
        count+=1
    print("newQuery:", newQuery)
    return newQuery

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

if __name__ == "__main__":
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
            feedback = getFeedback(results)
            precision = float(sum(feedback))/float(len(feedback))
            print("iteration "+str(count)+ " precision:"+str(precision))
            if precision == 0:
                print("Error: no relevant results. Exiting")
                break
            elif precision < targetPrecision:
                query = expandQuery(query, results, feedback)



