#################################
##### Name: Jiahong Xu      #####
##### Uniqname: jiahongx    #####
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import time

BASE_URL = "https://www.nps.gov"
CACHE_FILE_NAME = "cache.jason"

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

CACHE_DICT = load_cache()

def make_url_request_using_cache(url, cache):
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

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
    def __init__(self, category = "", name = "", address = "", zipcode = "", phone = ""):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        info_str = self.name+' ('+self.category+'): '+self.address+" "+self.zipcode
        return(info_str)
    


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
    url_dict = {}
    response_text = make_url_request_using_cache(BASE_URL, CACHE_DICT)
    soup = BeautifulSoup(response_text, 'html.parser')

    state_list_parent = soup.find('ul', class_='dropdown-menu SearchBar-keywordSearch')
    state_list_lis = state_list_parent.find_all('li', recursive=False)

    for state in state_list_lis:
        state_info = state.find("a")
        state_url = state_info["href"]
        state_name = state_info.text.strip().lower()
        url_dict[state_name] = BASE_URL + state_url

    save_cache(CACHE_DICT)
    return url_dict
 

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
    response_text = make_url_request_using_cache(site_url, CACHE_DICT)
    soup = BeautifulSoup(response_text, 'html.parser')

    # category
    cat_info = soup.find('span', class_ = 'Hero-designation')
    if cat_info is not None:
        category = cat_info.text.strip()
    else:
        category = ""
    # name
    n_info = soup.find('a', class_ = 'Hero-title')
    if n_info is not None:
        name = n_info.text.strip()
    else:
        name = ""

    footer = soup.find('div', class_ = "ParkFooter-contact")
    # address
    city_info = footer.find('span', itemprop = 'addressLocality')
    if city_info is not None:
        city = city_info.text.strip()
    else: 
        city = ""
    state_info = footer.find('span', itemprop = 'addressRegion')
    if state_info is not None:
        state = state_info.text.strip()
    else:
        state = ""
    if state and city:
        address = city + ", "+ state
    elif city: address = city
    elif state: address = state
    else: address = ""
    # zipcode 
    zipcode_info = footer.find('span', itemprop = 'postalCode')
    if zipcode_info is not None:
        zipcode = zipcode_info.text.strip()
    else: 
        zipcode = ""
    # phone
    p_info = footer.find('span', class_ = 'tel')
    if p_info is not None:
        phone = p_info.text.strip()
    else:
        phone = ""

    save_cache(CACHE_DICT)
    return NationalSite(category=category, name=name, address=address, zipcode=zipcode, phone=phone)


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
    response_text = make_url_request_using_cache(state_url, CACHE_DICT)
    soup = BeautifulSoup(response_text, 'html.parser')

    parks_ul = soup.find('ul', id = "list_parks")
    list_lis = parks_ul.find_all('li', class_ = "clearfix")
    ns_instances_list = []
    for li in list_lis:
        site_url = BASE_URL+li.find('a')['href']
        ns = get_site_instance(site_url)
        ns_instances_list.append(ns)

    save_cache(CACHE_DICT)
    return ns_instances_list


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
    zipcode = site_object.zipcode
    if not zipcode:
        return {}
    else:
        API_URL = 'http://mapquestapi.com/search/v2/radius?key='+\
        secrets.API_KEY+'&origin='+zipcode+\
        '&radius=10&maxMatches=10&ambiguities=ignore&outFormat=json'

        response_text = make_url_request_using_cache(API_URL, CACHE_DICT)
        Results_Dictionary = json.loads(response_text)
        for result in Results_Dictionary['searchResults']:
            info = result['fields']
            name = info['name']
            category = info['group_sic_code_name']
            address = info['address']
            city = info['city']
            if not category: category = 'no category'
            if not address: address = 'no address'
            if not city: city = 'no city'
            info_str = '- '+name+' ('+category+'): '+address+', '+city
            print(info_str)

        save_cache(CACHE_DICT)
        return Results_Dictionary

    
def main():
    #CACHE_DICT = load_cache()
    #print(secrets.API_KEY)
    state_url_dict = build_state_url_dict()
    input_state_name = True

    while True:
        if input_state_name:   
            state_name = input("Enter a state name (eg. Michigan or michigan) or \"exit\": ")
            state_name = state_name.strip().lower()
            if state_name == "exit":
                break
            elif state_name in state_url_dict:
                state_url = state_url_dict[state_name]
                sites_list = get_sites_for_state(state_url)
                reminder_str = 'List of national sites in '+ state_name.capitalize()
                print('-'*len(reminder_str))
                print(reminder_str)
                print('-'*len(reminder_str))
                for i in range(len(sites_list)):
                    ns = sites_list[i]
                    print('['+str(i+1)+'] '+ns.info())
            else: 
                print("[ERROR] Enter proper state name.")
                continue
        input_state_name = False 
        print("-"*50)
        number_input = input('Choose a number for detail search or \"exit\" or \"back\": ')
        if number_input =='exit':
            break
        elif number_input == 'back':
            input_state_name = True
            continue
        elif number_input.isnumeric()== False:
            print("[ERROR] Enter \"exit\" or \"back\" or a number.")
            continue
        else:
            number_input = int(number_input)
            if number_input>len(sites_list) or number_input <= 0:
                print("[ERROR] Enter a valid number.")
                continue
            else:
                ns = sites_list[number_input-1]
                reminder_str = 'Places near '+ ns.name
                print("-"*len(reminder_str))
                print(reminder_str)
                print("-"*len(reminder_str))
                get_nearby_places(ns)


if __name__ == "__main__":
    main()