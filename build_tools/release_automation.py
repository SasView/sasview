import argparse
import datetime
import json
import logging
import os
import subprocess
import sys
from csv import DictReader
from pathlib import Path

import requests

from sas.system import legal

USAGE = '''This script should be run from one directory above the base sasview directory. This script also requires both
 sasmodels and sasdata repositories to be in the same directory as the sasview repository.

Usage: `python sasview/build_tools/release_automation.py [opts]`

Options include:
    -v/--sasview_version: The sasview version for the upcoming release in x.y.z(a|b)(0-9) format. **required**
    -s/--sasmodels_version: The sasmodels version for the upcoming release in x.y.z(a|b)(0-9) format. **required**
    -d/--sasdata_version: The sasdata version for the upcoming release in x.y.z(a|b)(0-9) format. **required**
    -z/--zenodo: The Zenodo api key for modifying/creating Zenodo entries.
    -u/--username: Your Github username for fetching the repositories.
    -p/--password: Your Github password for fetching the repositories.
    -l/--sasview_list: A comma-delimited list of sasview issue numbers closed for this release.
    -m/--sasmodels_list: A comma-delimited list of sasmodels issue numbers closed for this release.
    -n/--sasdata_list: A comma-delimited list of sasdata issue numbers closed for this release.
'''

# Replace with live server and live server key
# DO NOT STORE KEY ON GITHUB
# TEST settings for Sandbox
zenodo_url = "https://zenodo.org"

# Record metadata
# Should import release notes from git repo, for now will need to cut and paste
sasview_data = {
'metadata': {
    'title': 'SasView version 6.1.2',
    'description': '6.1.2 release',
    'related_identifiers': [{'identifier': 'https://github.com/SasView/sasview/releases/tag/v6.1.1',
                        'relation': 'isAlternateIdentifier', 'scheme': 'url'}],
    'contributors': [],
    'creators': [],
    'grants': [{'id': '10.13039/501100000780::654000'}],
    'license': 'BSD-3-Clause',
    'upload_type': 'software',
    'access_right': 'open',
    'communities': [{'identifier': 'ecfunded'}, {'identifier': 'zenodo'}],
    'prereserve_doi': 'true'
    }
}

CURRENT_PATH = Path('.').resolve()
SASVIEW_PATH = CURRENT_PATH / 'sasview'
SASDATA_PATH = CURRENT_PATH / 'sasdata'
SASMODELS_PATH = CURRENT_PATH / 'sasmodels'
for path in [SASMODELS_PATH, SASDATA_PATH, SASVIEW_PATH]:
    if not path.exists():
        missing_repo = path.parts[-1]
        msg = f"""The {missing_repo} repository does not exist relative to the run path of release_automation.py.
        Please ensure you are running this script from the directory all sub packages are in.
        Usage:
            `python ./sasview/release_automation.py [options]
        """
        logging.error(msg)
CONTRIBUTORS_FILE = SASVIEW_PATH / 'build_tools' / 'contributors.tsv'


class SplitArgs(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values.split(','))


def sort_records(records: list[dict]):
    records.sort(key=lambda r: r['name'])

    # Move the release manager(s) so they are at the front of the list.
    filtered_release_managers = [r for r in records if r['release_manager']]
    for record in reversed(filtered_release_managers):
        # Go backwards through the list to ensure the release managers remain in alphabetical order when appending to the beginning of the contributors list
        records.remove(record)
        records.insert(0, record)

def generate_sasview_data() -> dict:
    """Read in a known file and parse it for the information required to populate the list of participants used
    in the zenodo record generation. The defined contributor types and difference between creators are defined in
    https://help.zenodo.org/docs/deposit/describe-records/contributors/.

    :return: A dictionary with a lists of creators and contributors."""
    if CONTRIBUTORS_FILE.exists():
        contributors = []
        creators = []
        with open(CONTRIBUTORS_FILE) as f:
            reader = DictReader(f, delimiter="\t")
            for row in reader:
                record = {"name": row["Name"], "affiliation": row["Affiliation"]}
                if 'ORCID' in row:
                    record['orcid'] = row['ORCID']
                if 'ReleaseManager' in row:
                    record['release_manager'] = row['ReleaseManager'] == 'x'
                else:
                    record['release_manager'] = False
                if row['Creator']:
                    creators.append(record)
                elif row['Producer']:
                    record['type'] = 'Producer'
                    contributors.append(record)
                else:
                    record['type'] = 'Other'
                    contributors.append(record)
        sort_records(creators)
        sort_records(contributors)
        return {"creators": creators, "contributors": contributors}
    else:
        return {}


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
"""__version__ = "%s"
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
    with open(init_file) as f:
        for line in f.readlines():
            if line[:11] == '__version__':
                output_lines.append('__version__ = \"' + version + '\"\n')
            else:
                output_lines.append(line)
    with open(init_file, 'w') as f:
        f.writelines(output_lines)


def update_sasdata_init(version):
    """Modify the sasdata __init__.py file in order to update the version

    :param version:
    :return:
    """
    init_file = CURRENT_PATH / 'sasdata' / 'sasdata' / '__init__.py'
    output_lines = []
    with open(init_file) as f:
        for line in f.readlines():
            if line[:11] == '__version__':
                output_lines.append('__version__ = \"' + version + '\"\n')
            else:
                output_lines.append(line)
    with open(init_file, 'w') as f:
        f.writelines(output_lines)


def update_file(license_file: Path, license_line: str, line_to_update: int):
    """Update a specific line in a text file."""
    with open(license_file) as f:
        output_lines = f.readlines()
        output_lines[line_to_update] = license_line
    with open(license_file, 'w') as f:
        f.writelines(output_lines)


def update_credits(credits_file: Path):
    """Update the credits.html file with relevant license info"""
    subprocess.check_call(
        [
            sys.executable,
            "--minimal",
            "build_tools/release_automation.py",
            credits_file,
        ])


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
        # WARNING: One can try running with auth but there is limited number of requests
        response = requests.get('https://api.github.com/repos/SasView/' + repository + '/issues/' + issue,
                                auth=(username, password))
        if response.status_code != 200:
            return []
        title = response.json()['title']
        issue_titles.append(f"#{issue}, {title}")
    return issue_titles


def parse_args():
    parser = argparse.ArgumentParser('Script to automate release process')
    parser.add_argument('-v', '--sasview_version', required=True)
    parser.add_argument('-s', '--sasmodels_version', required=True)
    parser.add_argument('-d', '--sasdata_version', required=True)
    parser.add_argument('-z', '--zenodo', default=False)
    parser.add_argument('-u', '--username', default=False)
    parser.add_argument('-p', '--password', default=False)
    parser.add_argument('-l', '--sasview_list', default=False, action=SplitArgs)
    parser.add_argument('-m', '--sasmodels_list', default=False, action=SplitArgs)
    parser.add_argument('-n', '--sasdata_list', default=False, action=SplitArgs)
    return parser.parse_args()


def main(args=None):
    if not args:
        args = parse_args()

    sasview_version = args.sasview_version
    sasmodels_version = args.sasmodels_version
    sasdata_version = args.sasdata_version
    sasview_data['metadata']['title'] = 'SasView version ' + sasview_version
    sasview_data['metadata']['description'] = sasview_version + ' release'
    sasview_data['metadata']['related_identifiers'][0]['identifier'] = \
        'https://github.com/SasView/sasview/releases/tag/v' + sasview_version
    # Generate a list of contributors using a file, if that file exists, otherwise use the pre-defined list given here.
    contributors = generate_sasview_data()
    if contributors:
        # Overwrite existing contributors and use the TSV file list (if available)
        sasview_data['metadata']['contributors'] = contributors['contributors']
        sasview_data['metadata']['creators'] = contributors['creators']

    # Generates zenodo doi if zenodo api key is provided
    new_doi = ''
    if args.zenodo:
        zenodo_api_key = args.zenodo
        new_doi = generate_zenodo(sasview_data, zenodo_api_key)

    update_sasview_metadata(sasview_version, new_doi)
    update_sasmodels_init(sasmodels_version)
    update_sasdata_init(sasdata_version)

    # Pull the license from a know location
    license_line = legal.copyright
    update_file(SASMODELS_PATH / 'LICENSE.txt', license_line, 0)
    update_file(SASDATA_PATH / 'LICENSE.TXT', license_line, 0)
    update_file(SASVIEW_PATH / 'installers' / 'license.txt', license_line, -1)
    update_credits(SASVIEW_PATH / "src" / "sas" / "system" / "credits.html")

    sasview_issues_list = args.sasview_list
    sasmodels_issues_list = args.sasmodels_list
    sasdata_issues_list = args.sasdata_list

    # Release notes template is generated if github credentials are provided
    if args.username and args.password:
        username = args.username
        password = args.password

        sasview_issues = prepare_release_notes(sasview_issues_list, 'sasview', username, password)
        sasmodels_issues = prepare_release_notes(sasmodels_issues_list, 'sasmodels', username, password)
        sasdata_issues = prepare_release_notes(sasdata_issues_list, 'sasmodels', username, password)

        print('Copy text below to  /sasview/docs/sphinx-docs/source/user/RELEASE.rst and adapt accordingly')
        for issue_title in sasview_issues:
            print(f'Fixes sasview {issue_title}')

        for issue_title in sasmodels_issues:
            print(f'Fixes sasmodels {issue_title}')

        for issue_title in sasdata_issues:
            print(f'Fixes sasdata {issue_title}')


if __name__ == "__main__":
    """
    Setups init and license files
    Generates zenodo doi and writes to the init file
    Templates release notes
    """

    args = parse_args()
    if hasattr(args, 'help'):
        print(USAGE)
    else:
        main(args)
