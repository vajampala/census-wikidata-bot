import pywikibot, json, os, requests, argparse, logging, time, json, sys
import mwparserfromhell, datetime, math
from pywikibot.data import api
from pywikibot import pagegenerators

#get values from CENSUS API.  Return response from first year with valid response starting with
#current year and ending with 2013
def get_census_values(api_url, get_var, for_var, api_key, year=datetime.datetime.today().year):
    try:
        year = datetime.datetime.today().year
        while year >= 2013:
            payload = {'get': get_var, 'for': for_var, 'key': api_key}
            r = requests.get(api_url.replace('XXXX', str(year)), params=payload)
            if r.status_code == 200:
                return r.json()
            else:
                logging.info('No API Results for year: {}'.format(year))
                year = year - 1
        else:
            return
    except requests.exceptions.RequestException as e:
        logging.error('General Exception: {}'.format(e))
    except IOError as err:
        logging.error('IOError: {}'.format(err))

def search_for_page_items(template, infobox_keys):
    template_values = {}
    for item, item_keys in infobox_keys.items():
        #print('infobox val: {}'.format(item_keys))
        for key in item_keys:
            #print('search for this key: {}'.format(key))
            if template.has(key):
                template_values[item] = str(template.get(key).value)
                break
    return template_values
            
#sort items by population (exluding PR and DC)
def population_rank_sort(pop_list):
    non_states = []
    for i, val in enumerate(pop_list):
        if val[2] in ['11', '72']:
            non_states.append(pop_list.pop(i))
    pop_list = sorted(pop_list, key=lambda x: int(x[1]), reverse=True)
    ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4]) 
    for i,val in enumerate(pop_list):
        val.append(ordinal(i+1))
    pop_list.extend(non_states)
    return pop_list

def update_page_items(page, api_values, page_values):
    for key, val in template_values.items():
        #print('k: {},v: {}'.format(key,val))
        pos = int(key.split(' - ')[1])
        print('KEY: {}'.format(key.split(' - ')[0]))
        if key == 'total_pop - 1':
            print('ORIG VALUE: {}'.format(val[:val.find('<ref')].replace('\n','')))
            print('REFERENCE: {}'.format(val[val.find('<ref'):].replace('\n','')))
        else: 
            print('ORIG VALUE: {}'.format(val.replace('\n','')))
        print('NEW VALUE: {}'.format(api_values[pos]))
        #page.text = text.replace(val, api_values[pos])
        #add reference!!!!!!!!!
        #page.save(u'Updating population estimate and associated population rank (when applicable)\
        #        with latest value from Census Bureau')

if __name__ == '__main__':
    get_var = 'GEONAME,POP'
    for_var = 'state:*'
    api_url = 'http://api.census.gov/data/XXXX/pep/population'
    api_key = os.environ['CENSUS']
    infobox_keys = {'total_pop - 1': ['population_total', '2010Pop', '2000Pop', 'population_estimate'],
            'rank - 3': ['PopRank']
            }
    site = pywikibot.Site('en', 'wikipedia') 
    repo = site.data_repository()
    
    metric_values = get_census_values(api_url, get_var, for_var, api_key)
    #metric_values.append(['User:Sasan-CDS/sandbox', '2302030'])
    #metric_values = [['User:Sasan-CDS/sandbox', '2302030']]
    #get list of pages from template, for each item in 
    if metric_values:
        #remove header
        metric_values.pop(0)
        metric_values = population_rank_sort(metric_values)

        print('Number of items in API Response: {}'.format(len(metric_values)))
        for i, val in enumerate(metric_values):
            key = val[0].split(',')[0]
            print('[STATE: {}]'.format(key))
            if key in ['Kansas', 'North Carolina', 'Georgia']:
                key = key + ', United States'
            elif key == 'Washington':
                key = 'Washington (state)'
            page = pywikibot.Page(site, key)
            if page.exists():
                if page.isRedirectPage():
                    page = page.getRedirectTarget()
                text = page.get(get_redirect=True)
                code = mwparserfromhell.parse(text)
                template_values = {}
                for template in code.filter_templates():
                    if template_values:
                        break
                    else:
                        template_values = search_for_page_items(template, infobox_keys)
                if template_values:
                    update_page_items(page, val, template_values)
                else:
                    print('No value found for this page!!!')
            else:
                print('NO RESULTS FOR: {}'.format(key))
    else:
        sys.exit('NO RESULTS FROM THE CENSUS API FOR ANY YEARS.  EXAMINE FOR OTHER ISSUES!')