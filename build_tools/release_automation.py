import requests
import argparse
import json
import datetime
import sys
import os

#Replace with live server and live server key
#DO NOT STORE KEY ON GITHUB
#TEST settings for Sandbox
zenodo_url = "https://zenodo.org"

#Record metadata
#Should import release notes from git repo, for now will need to cut and paste
sasview_data = {
    'metadata': {
    'title': 'SasView version 5.0.5',
    'description': '5.0.5 release',
    'related_identifiers': [{'identifier': 'https://github.com/SasView/sasview/releases/tag/v5.0.5',
                        'relation': 'isAlternateIdentifier', 'scheme': 'url'}],
    'contributors': [
        {'name': 'Anuchitanukul, Atijit', 'affiliation': 'STFC - Rutherford Appleton Laboratory', 'type':'Researcher'},
        {'name': 'Corona, Patrick', 'affiliation': 'University of California Santa Barbara', 'type':'Researcher'},
        {'name': 'Fragneto, Giovanna', 'affiliation': 'Institut Laue-Langevin', 'type':'Supervisor'},
        {'name': 'Fultz, Brent', 'affiliation': 'California Institute of Technology', 'type':'WorkPackageLeader'},
        {'name': 'Juhas, Pavol', 'affiliation': 'Brookhaven National Laboratory', 'type':'Researcher'},
        {'name': 'Knudsen, Mikkel', 'affiliation': 'University of Copenhagen', 'type':'Researcher'},
        {'name': 'Gilbert, Peter', 'affiliation': 'National Institute of Standards and Technology', 'type': 'Researcher'},
        {'name': 'Krueger, Susan', 'affiliation': 'National Institute of Standards and Technology', 'type': 'Researcher'},
        {'name': 'Markvardsen, Anders', 'affiliation': 'STFC - Rutherford Appleton Laboratory', 'type':'Supervisor'},
        {'name': 'McKerns, Mike', 'affiliation': 'California Institute of Technology', 'type':'Researcher'},
        {'name': 'Mothander, Karolina', 'affiliation': 'Lund University', 'type':'Researcher'},
        {'name': 'Narayanan, Theyencheri', 'affiliation': 'European Synchrotron Radiation Facility', 'type':'Researcher'},
        {'name': 'Parsons, Drew', 'affiliation': 'University of Cagliari and the Debian Project', 'type':'DataManager'},
        {'name': 'Porcar, Lionel', 'affiliation': 'Institut Laue-Langevin', 'type':'Researcher'},
        {'name': 'Pozzo, Lilo', 'affiliation': 'University of Washington', 'type':'Researcher'},
        {'name': 'Rakitin, Maksim', 'affiliation': 'Brookhaven National Laboratory','type':'DataManager'},
        {'name': 'Rennie, Adrian', 'affiliation': 'Uppsala University', 'type':'Researcher'},
        {'name': 'Rod, Thomas Holm', 'affiliation': 'European Spallation Source ERIC', 'type':'WorkPackageLeader'},
        {'name': 'Taylor, Jonathan', 'affiliation': 'European Spallation Source ERIC', 'type':'Other'},
        {'name': 'Teixeira, Susana', 'affiliation': 'National Institute of Standards and Technology', 'type': 'Researcher'},
        {'name': 'Udby, Linda', 'affiliation': 'Niels Bohr Institute', 'type':'Other'},
        {'name': 'Weigandt, Katie', 'affiliation':'National Institute of Standards and Technology','type':'Researcher'},
    ],

    'creators': [
        {'affiliation': 'Oak Ridge National Laboratory', 'name': 'Doucet, Mathieu', 'orcid': '0000-0002-5560-6478'},
        {'name': 'Cho, Jae Hie','affiliation': 'University of Tennessee Knoxville'},
        {'name': 'Alina, Gervaise','affiliation': 'University of Tennessee Knoxville'},
        {'name': 'Attala, Ziggy', 'affiliation': 'STFC - Rutherford Appleton Laboratory'},
        {'name': 'Bakker, Jurrian','affiliation': 'Technical Unviersity Delft'},
        {'name': 'Bouwman, Wim','affiliation': 'Technical Univeristy Deflt' },
        {'name': 'Bourne, Robert', 'affiliation': 'STFC - Rutherford Appleton Laboratory'},
        {'name': 'Butler, Paul','affiliation': 'National Institute of Standards and Technology', 'orcid': '0000-0002-5978-4714'},
        {'name': 'Cadwallader-Jones, Iestyn','affiliation': 'Institut Laue-Langevin'},
        {'name': 'Campbell, Kieran','affiliation': 'University of Oxford'},
        {'name': 'Cooper-Benun, Torin', 'affiliation': 'STFC - Rutherford Appleton Laboratory'},
        {'name': 'Durniak, Celine','affiliation': 'European Spallation Source ERIC' },
        {'name': 'Forster, Laura','affiliation': 'Diamond Light Source'},
        {'name': 'Gilbert, Peter','affiliation': 'National Institute of Standards and Technology', 'orcid': '0000-0003-1707-7517'},
        {'name': 'Gonzalez, Miguel','affiliation': 'Institut Laue-Langevin', 'orcid': '0000-0002-3478-0215'},
        {'name': 'Heenan, Richard','affiliation': 'STFC - Rutherford Appleton Laboratory','orcid': '0000-0002-7729-1454'},
        {'name': 'Jackson, Andrew','affiliation': 'European Spallation Source ERIC', 'orcid': '0000-0002-6296-0336'},
        {'name': 'King, Stephen','affiliation': 'STFC - Rutherford Appleton Laboratory', 'orcid': '0000-0003-3386-9151'},
        {'name': 'Kienzle, Paul','affiliation': 'National Institute of Standards and Technology'},
        {'name': 'Krzywon, Jeff','affiliation': 'National Institute of Standards and Technology'},
        {'name': 'Maranville, Brian', 'affiliation': 'National Institute of Standards and Technology', 'orcid': '0000-0002-6105-8789'},
        {'name': 'Martinez, Nicolas','affiliation': 'Institut Laue-Langevin'},
        {'name': 'Murphy, Ryan', 'affiliation': 'National Institute of Standards and Technology', 'orcid': '0000-0002-4080-7525'},
        {'name': 'Nielsen, Torben','affiliation': 'European Spallation Source ERIC'},
        {'name': "O'Driscoll, Lewis",'affiliation': 'STFC - Rutherford Appleton Laboratory'},
        {'name': 'Potrzebowski, Wojciech','affiliation': 'European Spallation Source ERIC', 'orcid': '0000-0002-7789-6779'},
        {'name': "Prescott, Stuart",'affiliation': 'University of New South Wales and the Debian Project', 'orcid': '0000-0001-5639-9688'},
        {'name': 'Ferraz Leal, Ricardo','affiliation': 'Oak Ridge National Laboratory'},
        {'name': 'Rozyczko, Piotr','affiliation': 'European Spallation Source ERIC', 'orcid' : '0000-0002-2359-1013' },
        {'name': 'Snow, Tim','affiliation': 'Diamond Light Source','orcid': '0000-0001-7146-6885'},
        {'name': 'Washington, Adam','affiliation': 'STFC - Rutherford Appleton Laboratory'},
        {'name': 'Wilkins, Lucas','affiliation': 'STFC - Rutherford Appleton Laboratory'},
        {'name': 'Wolf, Caitlyn','affiliation': 'National Institute of Standards and Technology'}
        ],
    'grants': [{'id': '10.13039/501100000780::654000'}],
    'license': 'BSD-3-Clause',
    'upload_type': 'software',
    'access_right': 'open',
    'communities': [{'identifier': 'ecfunded'}, {'identifier': 'zenodo'}],
    'prereserve_doi': 'true'
    }
}

class SplitArgs(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values.split(','))

def generate_zenodo(sasview_data, zenodo_api_key):
    """
    Generating zenodo record
    :return:
    """
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
    return newDOI

version_template = \
"""
__version__ = "%s"
__release_date__ = "%i"
__build__ = "GIT_COMMIT"
"""

zenodo_template = '__DOI__ = "%s"'

def update_sasview_metadata(version, doi):
    """
    Update version and zenodo DOI
    """

    system_directory = "sasview/src/sas/system"
    version_filename = os.path.join(system_directory, "version.py")
    zenodo_filename = os.path.join(system_directory, "zenodo.py")

    year = datetime.datetime.now().year

    with open(version_filename, 'w') as file:
        file.write(version_template % (version, year))

    with open(zenodo_filename, 'w') as file:
        file.write(zenodo_template % doi)

def update_sasmodels_init(version):
    """

    :param version:
    :return:
    """
    init_file = os.path.join('sasmodels', 'sasmodels', '__init__.py')
    output_lines = []
    with open(init_file, 'r') as f:
        for line in f.readlines():
            if line[:11] == '__version__':
                output_lines.append('__version__ = \"' + version + '\"\n')
            else:
                output_lines.append(line)
    with open(init_file, 'w') as f:
        f.writelines(output_lines)

def update_file(license_file, license_line, line_to_update):
    """

    :return:
    """
    with open(license_file, 'r') as f:
        output_lines = f.readlines()
        output_lines[line_to_update] = license_line
    with open(license_file, 'w') as f:
        f.writelines(output_lines)


def update_acknowledgement_widget():
    """

    :return:
    """
    pass


def prepare_release_notes(issues_list, repository, username, password):
    """
    Retrieving information from github and creating issue list for release notes
    :return:
    """
    issue_titles = []
    for issue in issues_list:
        #WARNING: One can try running with auth but there is limitted number of requests
        response = requests.get('https://api.github.com/repos/SasView/' + repository + '/issues/' + issue,
                                auth=(username, password))
        title = response.json()['title']
        issue_title = f"#{issue}, {title}"
        issue_titles.append(issue_title)
    return issue_titles

if __name__ == "__main__":
    """
    Setups init and license files
    Generates zenodo doi and writes to the init file
    Templates release notes
    """

    parser = argparse.ArgumentParser('Script to automate release process')
    parser.add_argument('-v', '--sasview_version', required=True)
    parser.add_argument('-s', '--sasmodels_version', required=True)
    parser.add_argument('-z', '--zenodo', default=False)
    parser.add_argument('-u', '--username', default=False)
    parser.add_argument('-p', '--password', default=False)
    parser.add_argument('-l', '--sasview_list', default=False, action=SplitArgs)
    parser.add_argument('-m', '--sasmodels_list', default=False, action=SplitArgs)
    args = parser.parse_args()

    sasview_version = args.sasview_version
    sasmodels_version = args.sasmodels_version
    sasview_data['metadata']['title'] = 'SasView version '+ sasview_version
    sasview_data['metadata']['description'] = sasview_version + ' release'
    sasview_data['metadata']['related_identifiers'][0]['identifier'] = \
        'https://github.com/SasView/sasview/releases/tag/v' + sasview_version

    # Generates zenodo doi if zenodo api key is provided
    new_doi = ''
    if args.zenodo:
        zenodo_api_key = args.zenodo
        new_doi = generate_zenodo(sasview_data, zenodo_api_key)

    update_sasview_metadata(sasview_version, new_doi)
    update_sasmodels_init(sasmodels_version)

    year = datetime.datetime.now().year
    license_line = 'Copyright (c) 2009-' + str(year) + ', SasView Developers\n\n'
    license_file = os.path.join('sasview', 'LICENSE.txt')
    update_file(license_file, license_line, 0)
    license_file = os.path.join('sasmodels', 'LICENSE.txt')
    update_file(license_file, license_line, 0)
    license_line = 'Copyright (c) 2009-' + str(year) + ' UTK, UMD, ESS, NIST, ORNL, ISIS, ILL, DLS, DUT, BAM\n'
    license_file = os.path.join('sasview', 'installers', 'license.txt')
    update_file(license_file, license_line, -1)

    sasview_issues_list = args.sasview_list
    sasmodels_issues_list = args.sasmodels_list

    #Release notes template is generated if github credentials are provided
    if args.username and args.password:
        username = args.username
        password = args.password

        sasview_issues = prepare_release_notes(sasview_issues_list, 'sasview', username, password)
        sasmodels_issues = prepare_release_notes(sasmodels_issues_list, 'sasmodels', username, password)

        print('Copy text bellow to  /sasview/docs/sphinx-docs/source/user/RELEASE.rst and adapt accordingly')
        for issue_title in sasview_issues:
            print(f'Fixes sasview {issue_title}')

        for issue_title in sasmodels_issues:
            print(f'Fixes sasmodels {issue_title}')
