

import page_rank
import sqlite3 as lite
import urllib2
import urlparse
from BeautifulSoup import *
from collections import defaultdict
import re

def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""

WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')

class crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    def __init__(self, db_conn, url_file):
        """Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing."""
        self._url_queue = [ ]
        self._doc_id_cache = { }
        self._word_id_cache = { }
        
        self._inverted_dict= { }		#the inverted, wordid is key, docid value
        self._inverted_resolved_dict= { }	#word id as key, url as value
        self._lexicon={}				#different from word_id_cache, lexicon is user input not website words
	self._from_to_link=[]
	
        
        # functions to call when entering and exiting specific tags
        self._enter = defaultdict(lambda *a, **ka: self._visit_ignore)
        self._exit = defaultdict(lambda *a, **ka: self._visit_ignore)

        # add a link to our graph, and indexing info to the related page
        self._enter['a'] = self._visit_a

        # record the currently indexed document's title an increase
        # the font size
        def visit_title(*args, **kargs):
            self._visit_title(*args, **kargs)
            self._increase_font_factor(7)(*args, **kargs)

        # increase the font size when we enter these tags
        self._enter['b'] = self._increase_font_factor(2)
        self._enter['strong'] = self._increase_font_factor(2)
        self._enter['i'] = self._increase_font_factor(1)
        self._enter['em'] = self._increase_font_factor(1)
        self._enter['h1'] = self._increase_font_factor(7)
        self._enter['h2'] = self._increase_font_factor(6)
        self._enter['h3'] = self._increase_font_factor(5)
        self._enter['h4'] = self._increase_font_factor(4)
        self._enter['h5'] = self._increase_font_factor(3)
        self._enter['title'] = visit_title

        # decrease the font size when we exit these tags
        self._exit['b'] = self._increase_font_factor(-2)
        self._exit['strong'] = self._increase_font_factor(-2)
        self._exit['i'] = self._increase_font_factor(-1)
        self._exit['em'] = self._increase_font_factor(-1)
        self._exit['h1'] = self._increase_font_factor(-7)
        self._exit['h2'] = self._increase_font_factor(-6)
        self._exit['h3'] = self._increase_font_factor(-5)
        self._exit['h4'] = self._increase_font_factor(-4)
        self._exit['h5'] = self._increase_font_factor(-3)
        self._exit['title'] = self._increase_font_factor(-7)

        # never go in and parse these tags
        self._ignored_tags = set([
            'meta', 'script', 'link', 'meta', 'embed', 'iframe', 'frame', 
            'noscript', 'object', 'svg', 'canvas', 'applet', 'frameset', 
            'textarea', 'style', 'area', 'map', 'base', 'basefont', 'param',
        ])

        # set of words to ignore
        self._ignored_words = set([
            '', 'the', 'of', 'at', 'on', 'in', 'is', 'it',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
            'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
            'u', 'v', 'w', 'x', 'y', 'z', 'and', 'or',
        ])

        # TODO remove me in real version
        self._next_doc_id = 1
        self._next_word_id = 1

        # keep track of some info about the page we are currently parsing
        self._curr_depth = 0
        self._curr_url = ""
        self._curr_doc_id = 0
        self._font_size = 0
        self._curr_words = None

        # get all urls into the queue
        try:
            with open(url_file, 'r') as f:
                for line in f:
                    self._url_queue.append((self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass
    


    def _insert_document(self, url):
        """A function that pretends to insert a url into a document db table
        and then returns that newly inserted document's id."""
        ret_id = self._next_doc_id
        self._next_doc_id += 1
        return ret_id
    
    # TODO remove me in real version
    def _insert_word(self, word):
        """A function that pretends to inster a word into the lexicon db table
        and then returns that newly inserted word's id."""
        ret_id = self._next_word_id
        self._next_word_id += 1
        self._lexicon[word]=ret_id
        return ret_id
    
    def word_id(self, word):
        """Get the word id of some specific word."""
        if word in self._word_id_cache:
            return self._word_id_cache[word]
        
        # TODO: 1) add the word to the lexicon, if that fails, then the
        #          word is in the lexicon
        #       2) query the lexicon for the id assigned to this word, 
        #          store it in the word id cache, and return the id.

        word_id = self._insert_word(word)
        self._word_id_cache[word] = word_id
        return word_id
        
        
    #implementation of get inverted index    
    def get_inverted_index(self):
        return self._inverted_dict
        
    def get_resolved_inverted_index(self):
        return self._inverted_resolved_dict
        
        
    def document_id(self, url):
        """Get the document id for some url."""
        if url in self._doc_id_cache:
            return self._doc_id_cache[url]
        
        # TODO: just like word id cache, but for documents. if the document
        #       doesn't exist in the db then only insert the url and leave
        #       the rest to their defaults.
        
        doc_id = self._insert_document(url)
        self._doc_id_cache[url] = doc_id
        return doc_id
    
    def _fix_url(self, curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""
            
        # compute the new url based on import 
        curr_url = urlparse.urldefrag(curr_url)[0]
        parsed_url = urlparse.urlparse(curr_url)
        return urlparse.urljoin(parsed_url.geturl(), rel)

    def add_link(self, from_doc_id, to_doc_id):
        """Add a link into the database, or increase the number of links between
        two pages in the database."""
        self._from_to_link.append([from_doc_id,to_doc_id])

    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        title_text = self._text_of(elem).strip()
        print "document title="+ repr(title_text)

        # TODO update document title for document id self._curr_doc_id
    
    def _visit_a(self, elem):
        """Called when visiting <a> tags."""

        dest_url = self._fix_url(self._curr_url, attr(elem,"href"))

        #print "href="+repr(dest_url), \
        #      "title="+repr(attr(elem,"title")), \
        #      "alt="+repr(attr(elem,"alt")), \
        #      "text="+repr(self._text_of(elem))

        # add the just found URL to the url queue
        self._url_queue.append((dest_url, self._curr_depth))
        
        # add a link entry into the database from the current document to the
        # other document

        self.add_link(self._curr_doc_id, self.document_id(dest_url))

        # TODO add title/alt/text to index for destination url
    
    def _add_words_to_document(self):
        # TODO: knowing self._curr_doc_id and the list of all words and their
        #       font sizes (in self._curr_words), add all the words into the
        #       database for this document
        print "    num words="+ str(len(self._curr_words))

    def _increase_font_factor(self, factor):
        """Increade/decrease the current font size."""
        def increase_it(elem):
            self._font_size += factor
        return increase_it
    
    def _visit_ignore(self, elem):
        """Ignore visiting this type of tag"""
        pass

    def _add_text(self, elem):
        """Add some text to the document. This records word ids and word font sizes
        into the self._curr_words list for later processing."""
        words = WORD_SEPARATORS.split(elem.string.lower())
        for word in words:
            word = word.strip()
            if word in self._ignored_words:
                continue
            self._curr_words.append((self.word_id(word), self._font_size))
        
    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = [ ]
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))
            
            return " ".join(text)
        else:
            return elem.string

    def _index_document(self, soup):
        """Traverse the document in depth-first order and call functions when entering
        and leaving tags. When we come accross some text, add it into the index. This
        handles ignoring tags that we have no business looking at."""
        class DummyTag(object):
            next = False
            name = ''
        
        class NextTag(object):
            def __init__(self, obj):
                self.next = obj
        
        tag = soup.html
        stack = [DummyTag(), soup.html]

        while tag and tag.next:
            tag = tag.next

            # html tag
            if isinstance(tag, Tag):

                if tag.parent != stack[-1]:
                    self._exit[stack[-1].name.lower()](stack[-1])
                    stack.pop()

                tag_name = tag.name.lower()

                # ignore this tag and everything in it
                if tag_name in self._ignored_tags:
                    if tag.nextSibling:
                        tag = NextTag(tag.nextSibling)
                    else:
                        self._exit[stack[-1].name.lower()](stack[-1])
                        stack.pop()
                        tag = NextTag(tag.parent.nextSibling)
                    
                    continue
                
                # enter the tag
                self._enter[tag_name](tag)
                stack.append(tag)

            # text (text, cdata, comments, etc.)
            else:
                self._add_text(tag)
    
    #get inverted index, return a dictionary with set as values
    #def get_inverted_index():
        #dictionary={}
        #for c in range(len(self._doc_id_cache)):
            
        #return dictionary
        
    
    def crawl(self, depth=2, timeout=3):
        """Crawl the web!"""
        seen = set()
        while len(self._url_queue):

            url, depth_ = self._url_queue.pop()

            # skip this url; it's too deep
            if depth_ > depth:
                continue

            doc_id = self.document_id(url)
	    #print doc_id
            # we've already seen this document
            if doc_id in seen:
                continue

            seen.add(doc_id) # mark this document as haven't been visited
            
            socket = None
            try:
                socket = urllib2.urlopen(url, timeout=timeout)
                soup = BeautifulSoup(socket.read())

                self._curr_depth = depth_ + 1
                self._curr_url = url
                self._curr_doc_id = doc_id
                #print self._curr_doc_id
                self._font_size = 0
                self._curr_words = [ ]
                
                self._index_document(soup)
                self._add_words_to_document()
                
                print "    url="+repr(self._curr_url)
                #print self._curr_doc_id
                #print self._curr_words
                #store these curr_word_id and doc_id into the global dictionary#########
                for c in range (len(self._curr_words)):
                    d = set()
                    d.add(self._curr_doc_id)
                    # if the word id has already been stored in dict, this means this doc id need to be appended to the end of this set
                    if self._curr_words[c][0] in self._inverted_dict:
                       self._inverted_dict[self._curr_words[c][0]].add(self._curr_doc_id)
                    #else this is a new word id , just create a new set for it
                    else:
                       self._inverted_dict[self._curr_words[c][0]]= d

	        #######################################################################
            except Exception as e:
                print e
                pass
            finally:
                if socket:
                    socket.close()
                             
       
        for c in self._inverted_dict: # check every element in dictionary, c is the key value of this element
          reversed_word_key =''
	  reversed_doc_key = set()
	  
          for k in self._inverted_dict[c]: #check every value(doc id) of this element of the dictionary
              for b in self._doc_id_cache: #now check doc_id_cache to find the matching one
                  if k == self._doc_id_cache[b]:# found the matching one 
                     reversed_doc_key.add(b)    # assign the value to the new set for later use
                     
          for a in self._word_id_cache:    #similar as above, now swapping word_id 
             # print a
              if c== self._word_id_cache[a]:
                 reversed_word_key = a
          self._inverted_resolved_dict[reversed_word_key]= reversed_doc_key #store into global dictionary
        
       # print self._doc_id_cache 
        con=lite.connect("dbFile.db")
       	cur=con.cursor()
            
        cur.execute('CREATE TABLE IF NOT EXISTS inverted_index(wordid INTEGER , docid INTEGER, PRIMARY KEY(wordid,docid));')
	cur.execute('CREATE TABLE IF NOT EXISTS Lexicon(wordid INTEGER PRIMARY KEY, word TEXT);')
	cur.execute('CREATE TABLE IF NOT EXISTS DocId_url(docid INTEGER, url TEXT, PRIMARY KEY(docid,url));')
	cur.execute('CREATE TABLE IF NOT EXISTS PageRank(docid INTEGER, rank REAL, PRIMARY KEY(docid,rank));')
	
        for c in self._inverted_dict:
          for k in self._inverted_dict[c]:

             cur.execute('INSERT OR IGNORE INTO inverted_index VALUES(?,?)',[c,k])
        con.commit()
        
        
        for c in self._doc_id_cache:
          	 cur.execute('INSERT OR IGNORE INTO DocId_url VALUES(?,?)',[self._doc_id_cache[c],c])
        con.commit()

        for c in self._lexicon:
          	 cur.execute('INSERT OR IGNORE INTO Lexicon VALUES(?,?)',[self._lexicon[c],c])
        con.commit()
        
        
        con.close
        
          
           
                
	    
    def pagerank_calc(self):
    	ranklist=page_rank.page_rank(self._from_to_link, 20, 1)
    	con=lite.connect("dbFile.db")
       	cur=con.cursor()
       	print ranklist

       	for i in ranklist:
       		print type(i)
       		cur.execute('INSERT OR REPLACE INTO PageRank VALUES(?,?)',[i,ranklist[i]])
       		con.commit()
    	con.close
    

if __name__ == "__main__":
    bot = crawler(None, "urls.txt")
    bot.crawl(depth=1)
    bot.pagerank_calc()
    
    
    #page_rank method is to be called here
    
    
    #after it's called then save data to db
