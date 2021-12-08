import overpy
import pandas as pd
import osmapi as osm
from time import perf_counter
from time import sleep
import random
import requests
from bs4 import BeautifulSoup
import overpass
import traceback


api = overpy.Overpass()
api2 = osm.OsmApi()
api3 = overpass.API()



# NOTE: This script could be optimized heavily. There are too many recursive API calls, however
#       I'm unsure if its possible to query the OSM API for tagged nodes within a radius of a
#       user-defined polygon. Because of this, we instead collect every individual node
#       that make up waterfront perimeters and ping every 10 nodes for nearby houses.

class WaterfrontPropertyLocator:

    def __init__(self, loc):
        self.loc = loc


    def get_nodes(self):

        state_loc = self.loc
        town_loc = self.loc

        start = perf_counter()


        '''
        Get a coordinates (lat, lon) for nodes tracing the boundary of all bodies of water 
        found from area 
                    (either state-level or by radius from selected town center)
        '''

        def get_water_from_state():

            result = api.query(f"""
                         [out:json];
                         area
                             ["name:en"="{state_loc}"];
                         out body;

                         relation
                             [water=lake]
                             (area);
                         out body qt;
                         """)

            bodies = []

            for x in result.relations:
                name = x.tags.get('name')
                # print(f'Grabbing {name}...')
                id = x.id
                members = [x.ref for x in x.members if x.role == 'outer']
                # extracts outer 'way' references for each body of water in radius
                #       (often >1 way per relation)
                details = {'name': name, 'id': id, 'members': members}
                bodies.append(details)
            for x in result.ways:
                name = x.tags.get('name')
                id = x.id
                members = x.id # 1 ref ID per way
                details = {'name': name, 'id': id, 'members': members}
                bodies.append(details)

            bodies = pd.DataFrame(bodies)
            bodies.to_excel(f'wf_data/{self.loc}_water.xlsx')
            return bodies


        water_bodies = get_water_from_state()  # or get_water_from_town()

        lat_lons = []
        '''
        Get all node coords for each node comprising a way (that comprises a relation - i.e. 'a body of water')
        '''
        # list of list of Way Ref IDs (for each body of water returned by get_water()
        member_ways = water_bodies['members']
        flat_members = [y for x in member_ways for y in (x if isinstance(x, list) else [x])] # flatten list
        for k, v in enumerate(flat_members):
            current = perf_counter()
            print(f'Grabbing way # {v} ({k} of {len(flat_members)})...')
            print(f'Current Runtime: {int(current - start)} seconds')
            for retry in range(3):
                try:
                    query = f'way({v});'
                    result = api3.get(query, verbosity='geom')
                    geom = result.features[0].geometry['coordinates']
                    for x in geom: # putting lat, lon coordinates in correct order
                        lat = x[1]
                        lon = x[0]
                        pair = lat, lon
                        lat_lons.append(pair)
                except Exception:
                    traceback.print_exc()


        lat_lons = pd.DataFrame(lat_lons) # add coordinate data to our list
        lat_lons.to_csv(f'wf_data/wf_boundary_coords_{self.loc}.csv')
        stop = perf_counter()
        elapsed = int(stop - start)
        print(f'Finished extracting all nodes for {self.loc} in {elapsed} seconds ({elapsed / 60} minutes).')
        return lat_lons


    def get_wf(self, slice):

        start = perf_counter()
        coords = pd.read_csv(f'wf_data/wf_boundary_coords_{self.loc}.csv')
        coords = coords['0'].astype(str) + ',' + coords['1'].astype(str)
        q_slice = int(len(coords)/4) # quarter of data set
        half_slice = q_slice * 2
        three_q = q_slice * 3
        if slice == 1:
            coords = coords[:q_slice] # 1
            print(f'Extracting {slice} out of 4 total coordinate lists.')
        if slice == 2:
            coords = coords[q_slice:half_slice] # 2
            print(f'Extracting {slice} out of 4 total coordinate lists.')
        if slice == 3:
            coords = coords[half_slice:three_q] # 3
            print(f'Extracting {slice} out of 4 total coordinate lists.')
        if slice == 4:
            coords = coords[three_q:]  # 4
            print(f'Extracting {slice} out of 4 total coordinate lists.')
        address = [] # append all addresses within radius of nodes

        for k, v in enumerate(coords):
            try:  # RADIUS OF 200 METERS (FROM EACH BOUNDARY NODE)
                n = 10
                if (k % n == 0):  # query every nth row
                    result = api.query(f"""
                              [out:json];
                              way(around:200, {v})["building"]["addr:housenumber"]["addr:street"]; 
                              out center;
                      """
                                       )
                    print(f'Requesting coordinate # {k} of {len(coords)}: {v}...')
                    result = result.ways
                    for x in result:
                        house_number = x.tags.get('addr:housenumber')
                        street = x.tags.get('addr:street')
                        bldg_id = x.id
                        details = {'house number': house_number, 'street': street, 'bldg_id': bldg_id}
                        address.append(details)
                        sleep(round(random.uniform(0, 0.2), 3))  # zzz...
                if (k % 20 == 0 and k > 1):  # progress report every 20 rows
                    if address:  # if address list isn't empty
                        address = [dict(t) for t in {tuple(d.items()) for d in address}]  # removing duplicate dicts
                        num = len([ele for ele in address if isinstance(ele, dict)])  # number of dictionaries in list
                        print(f'{num} addresses found')
                    else:
                        print('No addresses pulled yet...')
            except overpy.exception.OverpassTooManyRequests:
                print('Exceeded request limit, taking a rest...')
                sleep(2)  # ...zzz
            except overpy.exception.OverpassGatewayTimeout:
                print('Exceeding acceptable server load, taking a longer rest...')
                sleep(5)
        address = pd.DataFrame(address)
        address = address.drop_duplicates(subset=['bldg_id'])
        if slice == 1:
            address.to_excel(f'wf_data/{self.loc}_wf_address_inc1.xlsx')
        if slice == 2:
            address.to_excel(f'wf_data/{self.loc}_wf_address_inc2.xlsx')
        if slice == 3:
            address.to_excel(f'wf_data/{self.loc}_wf_address_inc3.xlsx')
        if slice == 4:
            address.to_excel(f'wf_data/{self.loc}_wf_address_inc4.xlsx')
        stop = perf_counter()
        print(f'Total run time for {len(coords)} nodes: {stop - start} seconds ({int((stop - start)/60)} minutes). ')
        return address

    def get_full_address(self):
        df1 = pd.read_excel(f'wf_data/{self.loc}_wf_address_inc1.xlsx', engine='openpyxl')
        df2 = pd.read_excel(f'wf_data/{self.loc}_wf_address_inc2.xlsx', engine='openpyxl')
        df3 = pd.read_excel(f'wf_data/{self.loc}_wf_address_inc3.xlsx', engine='openpyxl')
        df4 = pd.read_excel(f'wf_data/{self.loc}_wf_address_inc4.xlsx', engine='openpyxl')
        df = pd.concat([df1, df2, df3, df4])

        df = df.drop_duplicates(subset=['bldg_id']).reset_index()
        df['number_and_street'] = df['house number'].astype(str) + ' ' +  df['street']
        headers = {
            'authority': 'www.openstreetmap.org',
            'sec-ch-ua': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
            'accept': '*/*',
            'x-csrf-token': 'hAAyg/5iQPIIOwEQDsA9HKHe8Ib7MvnB4iiBg9wvIeqfEcy6gIUwYILnALwGr1LZsXpi++AdGPO/+W45xJ0VGQ==',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://www.openstreetmap.org/search?query=20%20Coveside%20Lane',
            'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'cookie': '_osm_session=709868dd092f3d11f20b9e337837c6e0;'
        }
        details = []
        for index, row in df.iterrows():
            url = 'https://www.openstreetmap.org/geocoder/search_osm_nominatim?query={}'.format(row['number_and_street'].replace(" ", "+"))
            response = requests.get(url, headers=headers).text
            soup = BeautifulSoup(response, 'lxml')
            print(f'{index} of {len(df)}')
            print(row['number_and_street'].replace(" ", "+"))
            current_id = str(row['bldg_id'])
            found = 0

            for x in soup.find_all('li', class_='list-group-item'): # searches 1st page for match
                entry = x.find('a', class_='set_position')
                if entry.get('data-id') == current_id:
                    full_address = entry.get('data-name')
                    full_address = full_address.replace(",", "", 1)
                    details.append(full_address)
                    found += 1
                    print(full_address)
                else:
                    pass
            if found < 1:       # if location not found on first page, request 'More results' (2nd page)
                more = soup.find('div', class_='search_more').a.get('href')
                url2 = f'https://www.openstreetmap.org/{more}' # more results href link
                response2 = requests.get(url2, headers=headers).text
                soup2 = BeautifulSoup(response2, 'lxml')
                for x in soup2.find_all('li', class_='list-group-item'):
                    entry = x.find('a', class_='set_position')
                    if entry.get('data-id') == current_id:
                        full_address = entry.get('data-name')
                        full_address = full_address.replace(",", "", 1)
                        details.append(full_address)
                        found += 1
                        print(full_address)
                    else:
                        pass
                if found < 1: # if location not found on second page, request 3rd page
                    more = soup2.find('div', class_='search_more').a.get('href')
                    url3 = f'https://www.openstreetmap.org/{more}'  # more results href link (3rd page)
                    response3 = requests.get(url3, headers=headers).text
                    soup3 = BeautifulSoup(response3, 'lxml')
                    for x in soup3.find_all('li', class_='list-group-item'):
                        entry = x.find('a', class_='set_position')
                        if entry.get('data-id') == current_id:
                            full_address = entry.get('data-name')
                            full_address = full_address.replace(",", "", 1)
                            details.append(full_address)
                            found += 1
                            print(full_address)
                        else:
                            pass
                else:
                    pass
            else:
                pass



        details = pd.DataFrame(details)
        details.to_excel(f'wf_data/{self.loc}_full_addresses.xlsx')
        return details  #





















