#################################
##### Name: Hexin Zhang
##### Uniqname: hexinz
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import time
CACHE_FILE_NAME = 'cacheSite_Scrape.json'

def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache, params=None, type='text'):
    if (url in cache.keys()):  # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        if params is None:
            response = requests.get(url)
        else:
            response = requests.get(url, params=params)
        if type == 'json':
            cache[url] = response.json()
        else:
            cache[url] = response.text
        save_cache(cache)
        return cache[url]

CACHE_DICT = load_cache()

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category=None, name=None, address=None, zipcode=None, phone=None):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return self.name + ' ('+str(self.category)+'): ' +  str(self.address) + ' ' + str(self.zipcode)


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    url = 'https://www.nps.gov/index.htm'
    page = make_url_request_using_cache(url, CACHE_DICT)
    soup = BeautifulSoup(page, 'html.parser')
    dropdown_menu = soup.find_all('ul', class_="dropdown-menu SearchBar-keywordSearch")
    hyperlinks = dropdown_menu[0].find_all('a')
    result_dict = {}
    for i in hyperlinks:
        result_dict[i.text.lower()] = 'https://www.nps.gov' + i.get('href')
    return result_dict
       

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    page = make_url_request_using_cache(site_url, CACHE_DICT)
    soup = BeautifulSoup(page, 'html.parser')
    site_name = soup.find_all('a', class_="Hero-title")
    site_category = soup.find_all('span', class_="Hero-designation")
    if site_category != []:
        site_category = site_category[0].text
    site_adr = soup.find_all('p', class_="adr")
    if site_adr != []:
        site_adr = str(site_adr[0].find_all('span', itemprop="addressLocality")[0].text.strip()) + ', ' + \
                       str(site_adr[0].find_all('span', itemprop="addressRegion")[0].text.strip())
    else:
        site_adr = ''
    site_zipcode = soup.find_all('span', itemprop="postalCode")
    if site_zipcode != []:
        site_zipcode = site_zipcode[0].text.strip()
    else:
        site_zipcode = ''
    site_phone = soup.find_all('span', class_="tel")
    if site_phone != []:
        site_phone = site_phone[0].text.strip()
    else:
        site_phone = ''
    national_site = NationalSite(
        name=site_name[0].text,
        category=site_category,
        address=site_adr,
        zipcode=site_zipcode,
        phone=site_phone
    )
    return national_site


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    result_sites = []
    url_text = make_url_request_using_cache(state_url, CACHE_DICT)
    soup = BeautifulSoup(url_text, 'html.parser')
    sites = soup.find_all('li', class_='clearfix')
    for site in sites[:-1]:
        hyperlinks = 'https://www.nps.gov' + site.find_all('a')[0].get('href') + 'index.htm'
        result_sites.append(get_site_instance(hyperlinks))
    return result_sites


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    params = {'key': secrets.API_KEY, 'origin': site_object.zipcode, 'radius': 10, 'maxMatches': 10,
              'ambiguities': "ignore", 'outFormat': 'json'}
    url = 'http://www.mapquestapi.com/search/v2/radius'
    url_text = make_url_request_using_cache(url=url, cache=CACHE_DICT, params=params, type='json')
    # response = requests.get(url, params=params).json()
    return url_text

if __name__ == "__main__":
    IsFirstStep = 1
    result_list = []
    if CACHE_DICT == {}:
        print("Fetching")
    else:
        print('Using cache')
    while True:
        if IsFirstStep == 1:
            state = input('Enter a state name (e.g. Michigan, michigan) or "exit": ').lower()
            if state == 'exit':
                break
            state_url_dict = build_state_url_dict()
            if state not in state_url_dict:
                print('[Error] Enter proper state name')
                continue
            else:
                IsFirstStep = 0
                result_list = get_sites_for_state(state_url_dict[state])
                print('-' * 34)
                print('List of national sites in ' + state)
                print('-' * 34)
                for num, result in enumerate(result_list):
                    print('[' + str(num + 1) + '] ' + result.info())
        elif IsFirstStep == 0:
            state = input('Choose the number for detail search or "exit" or "back": ').lower()
            if state == 'exit':
                break
            elif state == 'back':
                IsFirstStep = 1
            else:
                result_dict = {}
                if state.isdigit():
                    if 1 <= int(state) <= len(result_list):
                        IsFirstStep = 1
                        result_dict = get_nearby_places(result_list[int(state)-1])
                        print('-' * 34)
                        print('Places near ' + result_list[int(state)-1].name)
                        print('-' * 34)
                        for item in result_dict['searchResults']:
                            category = item['fields'].get('group_sic_code_name_ext','no category')
                            address = item['fields'].get('address', 'no address')
                            city = item['fields'].get('city', 'no city')
                            if category == '':
                                category = 'no category'
                            if address == '':
                                address = 'no address'
                            if city == '':
                                city = 'no city'
                            print('- ' + item.get('name') + ' ('+category+'): ' + address + ', ' + city)
                    else:
                        print('[Error] Invalid input')
                        continue
                else:
                    print('[Error] Invalid input')
                    continue