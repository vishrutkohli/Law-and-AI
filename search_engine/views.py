from django.shortcuts import render
import numpy as np
import gc
import pickle
import os
# nltk.data.path.append('./nltk_data/')
from collections import defaultdict
# import nltk 
# nltk.data.path.append('./nltk_data/')
from nltk.corpus import stopwords
from nltk import word_tokenize


postings = defaultdict(list)
stopWords = set(stopwords.words('english'))
from nltk.stem.porter import *
stemmer = PorterStemmer()
N_DOC = 910

# Create your views here.
try:
	
	dict_of_words = pickle.load(open("/search_engine/static/pickle_files/dict_of_words.p","rb"))
	postings = pickle.load(open("/search_engine/static/pickle_files/postings.p","rb"))

except Exception as e:
	print e
else:
	pass
finally:
	pass



def vectorise(text,postings):
    vector = np.zeros((len(postings),))
    text=re.sub(r'[^A-Za-z0-9 ]',' ',text)
    tok_txt = word_tokenize(text)
    tok_txt = [stemmer.stem(x.lower()) for x in tok_txt if x.lower() not in stopWords]
    for word in tok_txt:
        if word in dict_of_words:
            vector[dict_of_words[word]]+=1
    vector = vector/(np.linalg.norm(vector)+1e-9)
    for word in set(tok_txt):
        if word in dict_of_words:
            vector[dict_of_words[word]]+=np.log(N_DOC/doc_frequency[word])
    return vector/(np.linalg.norm(vector)+1e-9)


#gc.disable()
#doc_frequency = defaultdict(int)
N_DOC = 910
with open("/search_engine/static/pickle_files/doc_frequency.p","rb") as f:
    doc_frequency = pickle.load(f)
#for item in os.listdir("../Cases"):
#    if(item[-4:] == '.txt'):
#        N_DOC+=1
#        with open('../Cases/'+item) as f:
#            text = f.read()
#            text=re.sub(r'[^a-z0-9 ]',' ',text)
#            tok_txt = word_tokenize(text)
#            tok_txt = set([stemmer.stem(x.lower()) for x in tok_txt if x.lower() not in stopWords])
#            for word in tok_txt:
#                doc_frequency[word]+=1
                
#gc.enable()



#case_vectors = {}

#for item in os.listdir("../Cases"):
#    if(item[-4:] == '.txt'):
#        with open('../Cases/'+item) as f:
#            vd = vectorise(f.read(),postings)
#        case_vectors[item[:-4]] = vd

with open("/search_engine/static/pickle_files/case_vectors.p","rb") as f:
    case_vectors = pickle.load(f)

def make_query(query,postings,mode):
    query=re.sub(r'[^A-Za-z0-9 ]',' ',query)
    tok_txt = word_tokenize(query)
    tok_txt = [stemmer.stem(x.lower()) for x in tok_txt if x.lower() not in stopWords]
    search_results = set()
    if mode == "or":
            for item in tok_txt:
                if item in postings:
                    search_results |= set([x[0] for x in postings[item]])
        
    elif mode == "and" or mode == "phrase":
        for item in tok_txt:
                if len(search_results) == 0:
                    if item in postings:
                        search_results = set([x[0] for x in postings[item]])
                else:
                    if item in postings:
                        search_results &= set([x[0] for x in postings[item]])
        
        if mode == "phrase":
            refined_search_results = set()
            for doc_number in search_results:
                occurences = []
                for i,word in enumerate(tok_txt):
                    for document in postings[word]:
                        if document[0] == doc_number:
                            occurences.append(list(document[1]))
                            break
                    for j in range(len(occurences[-1])):
                        occurences[-1][j] -= i
                iterators = [0]*len(occurences)
                finished = False
                while(not finished):
                    all_same = True
                    prev = 0
                    min_t = 0
                    for i,it in enumerate(iterators):
                        if i==0:
                            prev = occurences[0][it]
                        else:
                            if(all_same):
                                if occurences[i][it]!=prev:
                                    all_same = False
                            if(occurences[i][it]<prev):
                                prev = occurences[i][it]
                                min_t = i
                    if all_same:
                        refined_search_results.add(doc_number)
                        """
                        for i,it in enumerate(iterators):
                            it+=1
                            if it >= len(occurences[i]):
                                finished=true
                                break
                        """
                        finished = True
                    
                    else:
                        iterators[min_t]+=1
                        if iterators[min_t] >= len(occurences[min_t]):
                            finished = True
                
                
            return refined_search_results
    
    return search_results




def ranked_results(query,postings,mode):
    docs = make_query(query,postings,mode)
    vq = vectorise(query,postings)
    cos_sim = []
    for doc in docs:
        with open("../Cases/"+doc+".txt","r") as f:
            vd = case_vectors[doc]
            cos_sim.append(np.dot(vd,vq))
    cos_sim = np.array(cos_sim)
    docs = np.array(list(docs))
    return docs[np.argsort(cos_sim)[-1:-6:-1]]

X = ranked_results("right to privacy",postings,"phrase")
print(X)

def index(request):
	context_dict = {}
	search_string = request.GET.get("searchstring") or ''
	type_of_search = request.GET.get("type") or ''

	if(search_string == '') :
		pass

	else:	
		list_of_cases = make_query(search_string,postings,type_of_search)
		print list_of_cases
		context_dict["list_of_cases"] = list_of_cases

	return render(request,'/search_engine/index.html',context_dict)
