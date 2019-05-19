import requests
import sys
import json

#Replace with live server and live server key
#DO NOT STORE KEY ON GITHUB
#TEST settings for Sandbox
#zenodo_url = "https://sandbox.zenodo.org"
#zenodo_api_key = "rdNmQU4ogrtYQKp5jd7238DnigkPu51aMKHa8yFttYtp3GgsxOW8MCfL8Exp"

#LIVE SETTINGS!!!!
zenodo_url = "https://zenodo.org"
zenodo_api_key = "5tMtV602m44vZvMWV5y3gRsuOlB8iEemP7Oo8m8N56CBl1RSLU9zgljErodz"


#Record metadata
#Should import release notes from git repo, for now will need to cut and paste
sasview_data = {
    'metadata': {
    'title': 'SasView version 5.0',
    'description': '5.0 release',
    'related_identifiers': [{'identifier': 'https://github.com/SasView/sasview/releases/tag/v5.0',
                        'relation': 'isAlternateIdentifier', 'scheme': 'url'}],
    'creators': [
        {'affiliation': 'Oak Ridge National Laboratory', 'name': 'Doucet, Mathieu', 'orcid': '0000-0002-5560-6478'},
        {'name': 'Cho, Jae Hie','affiliation': 'University of Tennessee Knoxville'},
        {'name': 'Alina, Gervaise','affiliation': 'University of Tennessee Knoxville'},
        {'name': 'Bakker, Jurrian','affiliation': 'Technical Unviersity Delft'},
        {'name': 'Bouwman, Wim','affiliation': 'Technical Univeristy Deflt' },
        {'name': 'Butler, Paul','affiliation': 'National Institute of Standards and Technology'},
        {'name': 'Campbell, Kieran','affiliation': 'University of Oxford'},
        {'name': 'Cooper-Benun, Torin', 'affiliation': 'STFC - Rutherford Appleton Laboratory'},
        {'name': 'Durniak, Celine','affiliation': 'European Spallation Source' },
        {'name': 'Forster, Laura','affiliation': 'Diamond Light Source'},
        {'name': 'Gonzales, Miguel','affiliation': 'Institut Laue-Langevin'},
        {'name': 'Heenan, Richard','affiliation': 'STFC - Rutherford Appleton Laboratory',},
        {'name': 'Jackson, Andrew','affiliation': 'European Spallation Source', 'orcid': '0000-0002-6296-0336'},
        {'name': 'King, Stephen','affiliation': 'STFC - Rutherford Appleton Laboratory', 'orcid': '0000-0003-3386-9151'},
        {'name': 'Kienzle, Paul','affiliation': 'National Institute of Standards and Technology'},
        {'name': 'Krzywon, Jeff','affiliation': 'National Institute of Standards and Technology'},
        {'name': 'Nielsen, Torben','affiliation': 'European Spallation Source'},
        {'name': "O'Driscoll, Lewis",'affiliation': 'STFC - Rutherford Appleton Laboratory'},
        {'name': 'Potrzebowski, Wojciech','affiliation': 'European Spallation Source', 'orcid': '0000-0002-7789-6779'},
        {'name': 'Ferraz Leal, Ricardo','affiliation': 'Oak Ridge National Laboratory'},
        {'name': 'Rozycko, Piotr','affiliation': 'European Spallation Source' },
        {'name': 'Snow, Tim','affiliation': 'Diamond Light Source','orcid': '0000-0001-7146-6885'},
        {'name': 'Washington, Adam','affiliation': 'STFC - Rutherford Appleton Laboratory'}
        ],
    'grants': [{'id': '10.13039/501100000780::654000'}],
    'license': 'BSD-3-Clause',
    'upload_type': 'software',
    'access_right': 'open',
    'communities': [{'identifier': 'ecfunded'}, {'identifier': 'zenodo'}],
    'prereserve_doi': 'true'
    }
}


#get list of existing depositions
r = requests.get(zenodo_url+"/api/deposit/depositions",
    params={'access_token':zenodo_api_key})
if r.status_code != 200:
    print("Failure of zenodo connection check. Terminating.")
    sys.exit(1)


#create empty upload
headers = {"Content-Type": "application/json"}
r = requests.post(zenodo_url+'/api/deposit/depositions',
                   params={'access_token':zenodo_api_key}, json={},
                   headers=headers)
if r.status_code != 201:
    print("Failure of zenodo record creation. Terminating")
    sys.exit(1)
else:
    newDOI = r.json()['metadata']['prereserve_doi']['doi']
    print("Empty record created with DOI:"+newDOI)
    #print(r.json())

#populate record
deposition_id = r.json()['id']
r = requests.put(zenodo_url+'/api/deposit/depositions/%s' % deposition_id,
                  params={'access_token': zenodo_api_key}, data=json.dumps(sasview_data),
                  headers=headers)
if r.status_code != 200:
    print("Failure to set metadata on record. Terminating")
    sys.exit(1)
else:
    print("Record metadata for DOI %s updated" % newDOI)


#next, manually add necessary files from Github and press the publish button

print("Record has been created on Zenodo with DOI: "+newDOI+"\nNext:\n- Add DOI to appropriate places in SasView code\n- "
                                                            "Make GitHub release\n - Download all release files from GitHub "
                                                            "and attach to Zenodo release record.\n- Publish Zenodo record")
