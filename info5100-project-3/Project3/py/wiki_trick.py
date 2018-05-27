import re
import socket
import urllib.request
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup # https://www.crummy.com/software/BeautifulSoup/bs4/doc/
from time import time
from collections import defaultdict
import json


PAGE_CNT = 1 # number of pages used to draw the distribution of distance to philosophy
TIME_LIMIT = 120
PREFIX = "https://en.wikipedia.org" # used to assist generating next visiting url
PHILOSOPHY = "https://en.wikipedia.org/wiki/Philosophy" # target page
RANDOM_URL = "http://en.wikipedia.org/wiki/Special:Random" # this url is found by using Chrome developer mode
sports_words = []
INTERESTED = "animals"
with open( './txts/' + INTERESTED + '.txt', 'r') as f:
    for line in f.readlines():
        word = line.strip('\n')
        sports_words.append("http://en.wikipedia.org/wiki/" + word)
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
    distri = defaultdict(int) # key: page idx, val: distance to philosophy
    memo = defaultdict(int) # a memo to record the visited page distances to philosophy
    PAGE_CNT = len(sports_words)
    res = {} # 3300 project3
    data = {"nodes":[], "links":[]}

    for i in range(PAGE_CNT):
        try:
            print ("no. ", i, ". reachable rate temp: ", (PAGE_CNT - unreachable) / float(PAGE_CNT))
            in_memo = False # whether the url is in memo
            Error = False
            skip = False
            old_time = time() # timestamp before searching
            page = wiki_page(sports_words[i])
            visited = [page] # avoid infinite loops
            while page.url != PHILOSOPHY:
                print (page.url)
                add_node = {"id": page.url, "group": 1}
                if add_node not in data['nodes']:
                    data["nodes"].append(add_node)
                    # nodes_set.add(page.url)
                candidates = page.get_candidate_urls()
                if len(candidates) == 0:
                    skip = True
                    break
                # get next url and mark as visited
                for next_url in candidates: # the first few canditates may be visited before so a for loop is needed
                    data["links"].append({"source": page.url, "target": next_url, "value": 100})
                    if {"id": next_url, "group": 1} not in data['nodes']:
                        data["nodes"].append({"id": next_url, "group": 1})

                    if next_url in memo: # in memo break directly
                        in_memo = True
                        break
                    if next_url not in visited:
                        try: #  avoid error: [Errno 11001] getaddrinfo failed
                            page = wiki_page(next_url)
                            visited.append(next_url)
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
                if in_memo:
                    break
        except:
            print (sports_words[i])
            skip = True
            continue

        # if timeout or error, give up this link and continue the next one
        if skip:
            unreachable += 1
            continue
        # if luckily a cache hit, update distribution and memo. Notice here visited doesn't contain the cached url we are resorting to.
        if in_memo:
            distri[i] = (len(visited) + 1) + memo[next_url]
            for j, page in enumerate(visited):
                memo[page] = (len(visited) - j) + memo[next_url] # distance to the last url + distance from last url to phylosophy
        # if unfortunately a cache miss. Notice here visited contains the phylisophy page.
        else:
            distri[i] = len(visited)
            for j, page in enumerate(visited):
                memo[page] = len(visited) - (j + 1) # the previous visited pages has larger distance to phylosophy
        res[sports_words[i]] = distri[i]

    # summary printout
    print ("res: \n", res)
    print ("data: \n", data)

    print ("memo: ", memo)
    print ("distribution: ", distri)
    print("unreachable: ", unreachable)
    print ( "reachable rate: " + str((PAGE_CNT - unreachable)/float(PAGE_CNT)))

    data = json.dumps(data)
    with open("/Users/jiahan/Documents/5100/info5100-project3/jsons/" + INTERESTED + ".json", 'w') as f:
        f.write(data)

    # draw the density distribution (Distance to philosophy v.s. # of pages)
    distance_list = list(distri.values())
    density = defaultdict(int)
    for v in distance_list:
        density[v] += 1
    x_min, x_max = min(distance_list), max(distance_list) # get min max of a axis values
    x_axis = list(range(x_min, x_max + 1, 1))
    y_axis = []
    for dis in x_axis: # fill y axis values
        if dis not in density:
            y_axis.append(0)
        else:
            y_axis.append(density[dis])
    plt.bar(x_axis, y_axis, align="center")
    plt.title("Distance to philosophy v.s. # of pages")
    plt.xlabel('Distance to philosophy')
    plt.ylabel('# of pages')
    plt.savefig("distribution") # save before show()
    plt.show()

if __name__ == "__main__":
    main()

############## side notes
# soup.find method return type <class 'bs4.element.Tag'>. findall method return type <class 'bs4.element.ResultSet'>
