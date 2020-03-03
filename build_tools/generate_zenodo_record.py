import requests
import sys
import json

#Replace with live server and live server key
#DO NOT STORE KEY ON GITHUB
#TEST settings for Sandbox
zenodo_url = "https://sandbox.zenodo.org"
zenodo_api_key = "rdNmQU4ogrtYQKp5jd7238DnigkPu51aMKHa8yFttYtp3GgsxOW8MCfL8Exp"

#Record metadata
#Should import release notes from git repo, for now will need to cut and paste
sasview_data = {
    'metadata': {
    'title': 'SasView version 5.0.1',
    'description': '5.0.1 release',
    'related_identifiers': [{'identifier': 'https://github.com/SasView/sasview/releases/tag/v5.0.1',
                        'relation': 'isAlternateIdentifier', 'scheme': 'url'}],
    'contributors': [
        {'name': 'Anuchitanukul, Atijit', 'affiliation': 'STFC - Rutherford Appleton Laboratory', 'type':'Researcher'},
        {'name': 'Corona, Patrick', 'affiliation': 'University of California Santa Barbara', 'type':'Researcher'},
        {'name': 'Fragneto, Giovanna', 'affiliation': 'Institut Laue-Langevin', 'type':'Supervisor'},
        {'name': 'Fultz, Brent', 'affiliation': 'California Institute of Technology', 'type':'WorkPackageLeader'},
        {'name': 'Juhas, Pavol', 'affiliation': 'Brookhaven National Laboratory', 'type':'Researcher'},
        {'name': 'Knudsen, Mikkel', 'affiliation': 'University of Copenhagen', 'type':'Researcher'},
        {'name': 'Markvardsen, Anders', 'affiliation': 'STFC - Rutherford Appleton Laboratory', 'type':'Supervisor'},
        {'name': 'McKerns, Mike', 'affiliation': 'California Institute of Technology', 'type':'Researcher'},
        {'name': 'Narayanan, Theyencheri', 'affiliation': 'European Synchrotron Radiation Facility', 'type':'Researcher'},
        {'name': 'Parsons, Drew', 'affiliation': 'University of New South Wales', 'type':'DataManager'},
        {'name': 'Porcar, Lionel', 'affiliation': 'Institut Laue-Langevin', 'type':'Researcher'},
        {'name': 'Pozzo, Lilo', 'affiliation': 'University of Washington', 'type':'Researcher'},
        {'name': 'Rakitin, Maksim', 'affiliation': 'Brookhaven National Laboratory','type':'DataManager'},
        {'name': 'Rennie, Adrian', 'affiliation': 'Uppsala University', 'type':'Researcher'},
        {'name': 'Rod, Thomas Holm', 'affiliation': 'Data Management and Software Centre, European Spallation Source ERIC', 'type':'WorkPackageLeader'},
        {'name': 'Taylor, Jonathan', 'affiliation': 'Data Management and Software Centre, European Spallation Source ERIC', 'type':'ContactPerson'},
        {'name': 'Udby, Linda', 'affiliation': 'Niels Bohr Institute', 'type':'ContactPerson'},
        {'name': 'Weigandt, Katie', 'affiliation':'University of Washington','type':'Researcher'},
    ],

    'creators': [
        {'affiliation': 'Oak Ridge National Laboratory', 'name': 'Doucet, Mathieu', 'orcid': '0000-0002-5560-6478'},
        {'name': 'Cho, Jae Hie','affiliation': 'University of Tennessee Knoxville'},
        {'name': 'Alina, Gervaise','affiliation': 'University of Tennessee Knoxville'},
        {'name': 'Attala, Ziggy', 'affiliation': 'STFC - Rutherford Appleton Laboratory'},
        {'name': 'Bakker, Jurrian','affiliation': 'Technical Unviersity Delft'},
        {'name': 'Bouwman, Wim','affiliation': 'Technical Univeristy Deflt' },
        {'name': 'Butler, Paul','affiliation': 'National Institute of Standards and Technology'},
        {'name': 'Campbell, Kieran','affiliation': 'University of Oxford'},
        {'name': 'Cooper-Benun, Torin', 'affiliation': 'STFC - Rutherford Appleton Laboratory'},
        {'name': 'Durniak, Celine','affiliation': 'Data Management and Software Centre, ,European Spallation Source' },
        {'name': 'Forster, Laura','affiliation': 'Diamond Light Source'},
        {'name': 'Gonzales, Miguel','affiliation': 'Institut Laue-Langevin'},
        {'name': 'Heenan, Richard','affiliation': 'STFC - Rutherford Appleton Laboratory',},
        {'name': 'Jackson, Andrew','affiliation': 'European Spallation Source', 'orcid': '0000-0002-6296-0336'},
        {'name': 'King, Stephen','affiliation': 'STFC - Rutherford Appleton Laboratory', 'orcid': '0000-0003-3386-9151'},
        {'name': 'Kienzle, Paul','affiliation': 'National Institute of Standards and Technology'},
        {'name': 'Krzywon, Jeff','affiliation': 'National Institute of Standards and Technology'},
        {'name': 'Nielsen, Torben','affiliation': 'Data Management and Software Centre, European Spallation Source'},
        {'name': "O'Driscoll, Lewis",'affiliation': 'STFC - Rutherford Appleton Laboratory'},
        {'name': 'Potrzebowski, Wojciech','affiliation': 'Data Management and Software Centre, European Spallation Source ERIC', 'orcid': '0000-0002-7789-6779'},
        {'name': "Prescott, Stewart",'affiliation': 'University of New South Wales'},
        {'name': 'Ferraz Leal, Ricardo','affiliation': 'Oak Ridge National Laboratory'},
        {'name': 'Rozycko, Piotr','affiliation': 'Data Management and Software Centre, European Spallation Source ERIC' },
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
