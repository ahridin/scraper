from exceptions import InvalidURLException, InvalidRequestException, InvalidInputException
import requester
import fixer
import regex
from node import Node
from my_queue import Queue
import urllib3
from bs4 import BeautifulSoup
from requests.models import Response
import zipfile
from zipfile import BadZipFile
import io
import re
import sys
from urllib.parse import urlparse
import gatherer
import os.path

encodings = ['utf-8', 'latin-1', 'windows-1250', 'ascii']
regex = regex.get()
sys.setrecursionlimit(10000)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Crawler(object):
    def __init__(self, test=None, limit=float('inf'), train=False):
        self.nodes = {}
        self.siblings = {}
        self.visited = set()
        self.hashes = set()
        self.crawled = set()
        self.streams = {}
        self.counter = 1
        self.host = None
        self.important = {}
        self.limit = limit
        self.queue = Queue()
        self.path = None
        self.train = train
        if test:
            self.host = requester.host(test)
            self.nodes[test] = Node(test, None)

    def crawl(self, page, recurse=True):
        if not requester.validate(page):
            raise InvalidURLException('Cannot crawl page of invalid url: ' + str(page))
        if self.host is None:
            self.host = requester.host(page)
            self.visit(self.host, None, self.host)
            if page != self.host:
                self.visit(page, self.nodes[self.host], self.host)
            if self.train:
                domain, top = requester.remove_top(self.host)
                self.path = os.path.join('C:\\Users\\pharvie\\Desktop\\Training', domain)
        request = requester.request(page)
        self.crawled.add(page)
        print('Crawling',  page)
        if request:
            self.counter += 1
            try:
                soup = BeautifulSoup(request.text, 'html.parser')
            except NotImplementedError:
                print('The following page caused an error in the soup', str(page))
            else:
                if soup:
                    splitext = self.check_text_urls(soup)
                    if splitext:
                        self.parse_text(splitext, page)
                    self.check_ref_urls(soup, page)
                    while recurse and self.counter < self.limit and not self.queue.empty():
                        self.crawl(self.queue.dequeue())

    def check_ref_urls(self, soup, parent):
        if soup:
            for a in soup.find_all('a', href=True):
                url = a.get('href')
                if not re.search(regex['invalid'], url) and url != '':
                    url = self.visit(url, self.nodes[parent], self.host)
                    if url:
                        self.check(url)
                        if requester.internal(url, self.host) and not re.search(regex['m3u'], url):
                            self.siblings[url] = len(self.nodes[url].siblings())
                            print('%s had %s siblings when added to the queue' % (url, self.siblings[url]))
                            self.queue.enqueue(url)

    def check_text_urls(self, soup):
        for br in soup.find_all('br'):
            br.append('\n')
        for div in soup.find_all('div'):
            div.append('\n')
        if soup.text:
            original = soup.text.splitlines()
            splitext = list(filter(lambda x: not re.match(regex['whitespace'], x), original))
            return splitext

    def parse_text(self, splitext, parent):
        m3us = set()
        counter = 0
        self.important[self.nodes[parent]] = False
        for x in range(1, len(splitext)):
            url = splitext[x].strip()
            if re.search(regex['ext'], splitext[x-1]) and not re.search(regex['ext'], splitext[x]):
                if not self.important[self.nodes[parent]]:
                    self.important[self.nodes[parent]] = True
                if re.search(regex['streams'], url, re.IGNORECASE) or re.search(regex['m3u'], url, re.IGNORECASE):
                    #url = self.visit(url, self.nodes[parent], parent)
                    if url is None:
                        continue
                    prepared_host = requester.prepare(requester.host(url))
                    if re.search(regex['m3u'], url) and prepared_host not in m3us:
                        request = requester.request(url)
                        m3us.add(prepared_host)
                        if request:
                            if request.url != url:
                                self.visit(request.url, self.nodes[parent], parent)
                            self.extract_file(request)
                    elif re.search(regex['streams'], url) and prepared_host not in self.streams:
                        if prepared_host not in self.streams:
                            self.streams[prepared_host] = set()
                        self.streams[prepared_host].add(self.host)
                        counter += 1

            elif requester.validate(url):
                prepared_host = requester.prepare(requester.host(url))
                url = self.visit(url, self.nodes[parent], self.host)
                if url:
                    if (not requester.internal(url, self.host) and prepared_host not in m3us) or requester.internal(url, self.host):
                        m3us.add(prepared_host)
                        self.check(url)

    def check(self, url, override=False):
        if not requester.validate(url):
            raise InvalidURLException('Cannot check for m3u files of the following url: ' + str(url))
        p = urlparse(url)
        s = p.path + p.query
        if re.search(regex['m3u'], s) or (re.search(regex['dl'], s) and not re.search(regex['ndl'], s)) \
                or re.search(regex['zip'], s) or re.search(regex['raw'], s) or override:
            request = requester.request(url)
            if request:
                #self.visit(request.url, self.nodes[url].parent(), self.host)
                self.extract_file(request)
            else:
                self.important[self.nodes[url]] = False

    def extract_file(self, request):
        file_type = requester.get_format(request)
        if file_type == 'm3u':
            splitext = request.text.splitlines()
            if splitext:
                self.parse_text(splitext, parent=request.url)
        elif file_type == 'zip':
            self.unzip(request)
        elif file_type == 'html':
            url = self.visit(request.url, self.nodes[request.url].parent(), self.host)
            if url:
                self.crawl(url, recurse=False)

    def unzip(self, request):
        if request is None or not isinstance(request, Response):
            raise InvalidRequestException('Cannot unzip invalid request')
        try:
            z = zipfile.ZipFile(io.BytesIO(request.content))
        except BadZipFile:
            pass
        else:
            for info in z.infolist():
                if re.search(regex['m3u'], info.filename):
                    f = z.read(info.filename)
                    hashnum = requester.hash_content(f)
                    if hashnum not in self.hashes:
                        self.hashes.add(hashnum)
                        for e in encodings:
                            try:
                                splitext = f.decode(e).splitlines()
                            except UnicodeDecodeError:
                                pass
                            else:
                                if splitext:
                                    self.parse_text(splitext, parent=request.url)
                                    break

    def visit(self, url, parent, host):
        if url is None or not isinstance(url, str):
            raise InvalidInputException('Cannot visit invalid url ' + str(url))
        if url in self.nodes:
            return None
        fixed_url = fixer.phish(fixer.partial(url, host))
        if not requester.validate(fixed_url):
            return None
        fixed_url = fixer.reduce(fixer.expand(fixed_url))
        if url != fixed_url:
            if fixed_url in self.nodes:
                return None
        self.nodes[fixed_url] = Node(fixed_url, parent)
        return fixed_url

    def get_streams(self):
        return self.streams

    def eliminate(self):
        print('In eliminate')
        for node in self.important:
            if self.important[node]:
                for parent in node.parents():
                    self.important[parent] = True
        if self.train:
            for node in self.important:
                if not self.important[node] and node.data() in self.crawled and requester.internal(node.data(), self.host):
                    print('The following url is to be eliminated', node.data())
                    string = node.data() + '\n' + str(node.depth())
                    gatherer.add_to_path(self.path, 'neg', node.data(), string)

            for node in self.important:
                if self.important[node] and node.data() in self.crawled and requester.internal(node.data(), self.host):
                    print('The following url is to be spared', node.data())
                    string = node.data() + '\n' + str(node.depth())
                    gatherer.add_to_path(self.path, 'pos', node.data(), string)





crawler = Crawler()
crawler.check('https://manifest.theplatform.com/m/NnzsPC/RUWLKQv5KFEs,X6KmsUDGB3Zc,7kIQQG932Vs0,xjobRXgWDiTT,WKkGR3EWxlMj,8lwm3xhvMJTR,pQvCoP7rBsmZ/1.m3u8?sid=ab3a616e-eee2-4ee7-bb35-88d669ab1753&policy=121497524&date=1530214354279&ip=209.23.210.2&schema=1.1&cid=444f6ba4-9541-485e-82e4-caaa1e6120b8&host=nbchls-prod.nbcuni.com&manifest=M3U&switch=HLSOriginSecure&aam_segments=8129897%2C4739140%2C4738083%2C4741378%2C6677178%2C9299480%2C5877943&_fw_h_referer=www.nbc.com&siteSectionId=nbc_tveverywhere_vod_hub&fallbackSiteSectionId=1676939&player=PDK+6+-+NBC.com+Instance+of%3A+rational-player-production&sig=d5176c942926049bbf0edf4887109523902c2cbdd83f9b976f9f24616fe98cf4')