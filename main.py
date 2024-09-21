#import necessary libraries
import json
import requests
from bs4 import BeautifulSoup
import random
import unittest

import time

class GithubCrawler:
    #initializing class with necessary variables
    def __init__(self, proxies=[], keywords=[], type=[]):
        self.proxies = proxies
        self.keywords = keywords
        self.type = type
        self.output = None
    #method to get proxies,keywords, type from json file
    def get_proxies(self,input_file):
        #try - except block
        try:
            #open a file to check if data exist and to get the data
            with open(input_file) as file:
                data = json.load(file)
                if 'proxies' in data:
                    proxies = data['proxies']
                else:
                    proxies = []
                if 'keywords' in data:
                    keywords = data['keywords']
                else:
                    keywords = []
                if 'type' in data:
                    type = data['type']
                else:
                    type = []
        # Print an error message if there is an error with json file
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return [],[],[]

        return proxies,keywords,type
    # method to make a search on github by keywords

    def search(self):
        # initializing proxies,keywords,type
        self.proxies, self.keywords, self.type = self.get_proxies('input_data.json')

        print(self.proxies)
        print(self.keywords)
        print(self.type)
        # creating a keywords combination that will be used in search
        search_keywords = "+".join(self.keywords)

        # Select a random proxy from the list
        selected_proxy = random.choice(self.proxies)
        print(selected_proxy)
        # creating a url that will be used for search
        search_url = f"https://github.com/search?q={search_keywords}&type={self.type}"
        proxy_dict = {
            "http": selected_proxy,
            "https": selected_proxy
        }
        return self.search_url(search_url,proxy_dict, search_keywords)

    def search_url(self,search_url,proxy_dict,search_keywords):

        # try-except block
        try:
            # creating the connection to github via proxy
            response = requests.get(search_url,proxies=proxy_dict,timeout=60)
            if response.status_code == 200:
                # Extract data  from the search results
                data = response.json()['payload']['results']
                urls = []
                for search_result in data:
                    # get each result urls according to search type
                    if self.type == 'Repositories':
                        search_result_url = f"https://github.com/{search_result['hl_name']}"
                        #getting the owner of the repository (Only for 'Repositories' Type)
                        owner = search_result['repo']['repository']['owner_login']
                        language_stats = self.search_extra(search_result_url,proxy_dict)
                    if self.type == 'Issues':
                        search_result_url = f"https://github.com/{search_result['repo']['repository']['owner_login']}/{search_result['repo']['repository']['name']}/issues/{search_result['number']}"
                    if self.type == 'Wikis':

                        title = '-'.join(list(search_result['title'].split(' ')))
                        search_result_url = f"https://github.com/{search_result['repo']['repository']['owner_login']}/{search_result['repo']['repository']['name']}/wiki/{title}"
                    # check if owner and language stats were scrapped to set proper search result
                    if owner and language_stats:
                        urls.append({'url':search_result_url,'extra':{'owner':owner,'lauguage_stats':language_stats}})
                    else:
                        urls.append({'url': search_result_url})

                else:
                    print(f"Failed to fetch search results for keywords: {search_keywords}")
                # Migrating output to json format
                self.output = json.dumps(urls)

        except requests.RequestException as e:
            print(f"Error making the request: {e}")
        return self.output

    def search_extra(self,search_result_url,proxy_dict):
        try:
            # creating connection to the repository to get extra data like language stats
            repo_response = requests.get(search_result_url, proxies=proxy_dict, timeout=60)
            if repo_response.status_code == 200:
                # parsing html to get language stats
                soup = BeautifulSoup(repo_response.text, "html.parser")
                layout = soup.find('div', class_="Layout-sidebar")
                div = list(layout.find_all('div', class_="BorderGrid-row"))
                ul = div[-1].find('ul')

                li = list(ul.find_all('li'))
                language_stats = []
                for i in li:
                    span = list(i.find_all('span'))
                    span_list = []
                    for j in span:
                        span_list.append(j.get_text(strip=True))
                    language_stats.append(tuple(span_list))
                language_stats = dict(language_stats)
        except requests.RequestException as e:
            print(f"Error making the request: {e}")
        return language_stats


class TestGithubCrawler(unittest.TestCase):

    def setUp(self):
        # Initialize an instance of GithubCrawler for testing
        self.crawler = GithubCrawler()

    def test_search(self):
        # Set up test data and input file
        test_proxies = ["34.82.224.175:33333"]
        test_keywords = ["python", "unittest"]
        test_type = "Repositories"  # Set the type as needed

        # Create a test input JSON file with the above data
        input_data = {
            "proxies": test_proxies,
            "keywords": test_keywords,
            "type": test_type
        }
        with open("test_input_data.json", "w") as file:
            json.dump(input_data, file)

        # Call the search method with the test input data
        self.crawler.search()

        # Check if the crawler's output is not None
        self.assertIsNotNone(self.crawler.output)

        # Parse the JSON output
        output_data = json.loads(self.crawler.output)

        # Ensure that the output data is in the expected format
        self.assertIsInstance(output_data, list)




if __name__ == "__main__":
    #crating class instance
    a  = GithubCrawler()
    #making a search
    a.search()
    # printing the results of the search
    print(a.output)
    # testing the github crawler
    unittest.main()
