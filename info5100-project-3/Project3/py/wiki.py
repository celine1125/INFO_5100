import re
import socket
import urllib.request
from bs4 import BeautifulSoup # https://www.crummy.com/software/BeautifulSoup/bs4/doc/
from time import time
from collections import defaultdict
import json
import sys

# src_url = sys.argv[1]
# des_url = sys.argv[2]

TIME_LIMIT = 60 # define "unreachable to philosophy" as "can reach philosophy in 60 seconds"
PREFIX = "https://en.wikipedia.org" # used to assist generating next visiting url
PHILOSOPHY = "https://en.wikipedia.org/wiki/Philosophy" # target page


INTERESTED = 'compsci'
sports_words = []
with open( '../txts/' + INTERESTED + '.txt', 'r') as f:
    for line in f.readlines():
        word = line.strip('\n')
        sports_words.append("https://en.wikipedia.org/wiki/" + word)
print ('interested words: ', sports_words)



class wiki_page():
    """
    a wiki_page class able to extract the page body, clean the content and find next urls. 
    """
    def __init__(self, url):
        self.url = url
        response = urllib.request.urlopen(self.url)
        html = response.read()
        self.soup = BeautifulSoup(html, 'html.parser')
        self.url_candidates = []

    def get_body(self):
        """
        Get the raw string "true body block" we want
        return a string
        """
        body = self.soup.find('div', attrs={'id': 'mw-content-text', 'class': 'mw-content-ltr'})  # found by chrome extension mode
        return str(body)

    def remove_paranthese(self):
        """
        remove paranthese contents byregular expression
        return a beautifulsoup object
        """
        rule = re.compile(r'[^_]\([^()]*\)') # cannot begin with "_", because some links have parenthesis. e.g. /wiki/Discipline_(academia)
        str_body = re.sub(rule, '', self.get_body())  # remove all the links inside parenthesis.
        self.soup = BeautifulSoup(str_body, 'html.parser')

    def remove_italicized(self):
        """
        remove italicized content
        modify self.soup
        """
        for i_tag in self.soup("i"):
            i_tag.decompose()

    def remove_tables(self):
        """
        remove table content
        modify self.soup
        """
        for table_tag in self.soup("table"):
            table_tag.decompose()

    def remove_headnotes(self):
        """
        remove headnotes
        modify self.soup
        """
        # notice that some pages doesn't contain headnotes
        try:
            notes = self.soup.find_all('div', attrs={"role" : "note"})
            for note in notes:
                note.extract()
        except:
            pass


    def get_candidate_urls(self):
        """
        find all valid candidate urls (not only the first one)
        return list of string urls
        """
        # clean the soup first
        self.remove_paranthese()
        self.remove_headnotes()
        self.remove_tables()
        self.remove_italicized()
        for p in self.soup.find_all('p'):
            for link in p.find_all('a', href=True):
            # for link in self.soup.find_all('a', href=True):
                # save the qualified next urls
                key = link["href"]
                if len(key.split(".")) > 1 or len(key.split(":")) > 1: # e.g. art.jpg is not we want. talk:art (wiki talk page) is also not we want
                    continue
                if link["href"].startswith("/wiki"):  # valid wiki pages
                    url = PREFIX + link["href"]
                    self.url_candidates.append(url)
        return self.url_candidates


def main():
    unreachable = 0 # unreachable url count
    memo = defaultdict(int) # a memo to record the visited page distances to philosophy
    PAGE_CNT = len(sports_words)
    res = [];

    for i in range(PAGE_CNT):
        try:
            print ("no. ", i, ". reachable rate temp: ", (PAGE_CNT - unreachable) / float(PAGE_CNT))
            in_memo = False # whether the url is in memo
            print(sports_words[i])
            Error = False
            skip = False
            old_time = time() # timestamp before searching
            page = wiki_page(sports_words[i])
            #res.append([sports_words[i]])
            res.append([page.url[30:]]) # avoid infinite loops
            # loop until philosophy is found.
            while page.url != PHILOSOPHY:
                print (page.url)
                candidates = page.get_candidate_urls()
                if len(candidates) == 0:
                    skip = True
                    break
                # get next url and mark as visited
                for next_url in candidates: # the first few canditates may be visited before so a for loop is needed
                    if next_url[30:] not in res[i]:
                        #print(next_url[30:])
                        try: #  avoid error: [Errno 11001] getaddrinfo failed
                            page = wiki_page(next_url)
                            res[i].append(page.url[30:])
                            break
                        except socket.gaierror:
                            Error = True
                            break
                # either timeout or gaierror, skip this url. Remember to reset skip to True in next loop
                if time()-old_time > TIME_LIMIT or Error:
                    print ("timeout or error")
                    skip = True
                    break
                # if in memo, can update the distribution depend on memo
        except:
            print ('skipped: ', sports_words[i])
            skip = True
            continue

        # if timeout or error, give up this link and continue the next one
        #print (res)
        res[i].reverse()
        print (len(res[i]))
        if skip:
            unreachable += 1
            continue

    # summary printout
    print ("res: \n", res)

    data = json.dumps(res)
    with open("../jsons/" + INTERESTED + '_tree' + ".json", 'w') as f:
        f.write(data)


if __name__ == "__main__":
    main()

############## side notes
# soup.find method return type <class 'bs4.element.Tag'>. findall method return type <class 'bs4.element.ResultSet'>


