import argparse
import datetime
import fileinput
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
    -z/--zenodo: A Zenodo API Key for modifying/creating Zenodo entries.
'''

# Replace with live server and live server key
# DO NOT STORE KEY ON GITHUB
# TEST settings for Sandbox
zenodo_url = "https://zenodo.org"

# Record metadata
# Should import release notes from git repo, for now will need to cut and paste
sasview_data = {
'metadata': {
    'title': 'SasView version ',
    'description': ' release',
    'related_identifiers': [{'identifier': 'https://github.com/SasView/sasview/releases/tag/v',
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
sasmodels_data = {
'metadata': {
    'title': 'SasModels version ',
    'description': ' release',
    'related_identifiers': [{'identifier': 'https://github.com/SasView/sasmodels/releases/tag/v',
                        'relation': 'isAlternateIdentifier', 'scheme': 'url'}],
    'contributors': [],
    'creators': [],
    'license': 'BSD-3-Clause',
    'upload_type': 'software',
    'access_right': 'open',
    'communities': [{'identifier': 'ecfunded'}, {'identifier': 'zenodo'}],
    'prereserve_doi': 'true'
    }
}
sasdata_data = {
'metadata': {
    'title': 'SasData version ',
    'description': ' release',
    'related_identifiers': [{'identifier': 'https://github.com/SasView/sasdata/releases/tag/v',
                        'relation': 'isAlternateIdentifier', 'scheme': 'url'}],
    'contributors': [],
    'creators': [],
    'license': 'BSD-3-Clause',
    'upload_type': 'software',
    'access_right': 'open',
    'communities': [{'identifier': 'ecfunded'}, {'identifier': 'zenodo'}],
    'prereserve_doi': 'true'
    }
}

version_template = \
"""try:
    from ._version import __version__
except ImportError:
    __version__ = "{0}"

__release_date__ = "{1}"
__build__ = "GIT_COMMIT"

__all__ = ["__build__", "__release_date__", "__version__"]
"""
acknowledgement_template = \
'''__DOI__ = "{0}"
__RELEASE_MANAGER__ = "{1}"
__ACKNOWLEDGEMENT__ = "This work benefited from the use of the SasView application, originally developed " \\
                      "under NSF Award DMR - 0520547. SasView also contains code developed with funding" \\
                      " from the EU Horizon 2020 programme under the SINE2020 project Grant No 654000."
'''

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
            `python ./sasview/build_tools/release_automation.py [options]
        """
        logging.error(msg)
SASVIEW_CONTRIBUTORS_FILE = SASVIEW_PATH / 'build_tools' / 'contributors.tsv'
SASDATA_CONTRIBUTORS_FILE = SASDATA_PATH / 'contributors.tsv'
SASMODELS_CONTRIBUTORS_FILE = SASMODELS_PATH / 'build_tools' / 'contributors.tsv'


class SplitArgs(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values.split(','))


def sort_records(records: list[dict]) -> None:
    """Sort a list of contributors in alphabetical order and move the release manager(s) to the start of the list.
    This sorting is performed directly on the list, so no return is necessary.

    :param records: A list of contributor dictionaries with key word: value mappings.
    """
    records.sort(key=lambda r: r['name'])

    # Move the release manager(s) so they are at the front of the list.
    filtered_release_managers = [r for r in records if r['release_manager']]
    for record in reversed(filtered_release_managers):
        # Go backwards through the list to ensure the release managers remain in alphabetical order when appending to the beginning of the contributors list
        records.remove(record)
        records.insert(0, record)


def generate_zenodo_data(zenodo_data: dict, version: str, contributors_file: Path) -> None:
    """Update the zenodo data for a repo, using the latest version and contributors list.

    The defined contributor types and difference between creators are defined in
    https://help.zenodo.org/docs/deposit/describe-records/contributors/.

    :param zenodo_data: A zenodo data dictionary for a single repo.
    :param version: The version of the repo.
    :param contributors_file: The path to the contributors file for the repo.
    """
    zenodo_data['metadata']['title'] = zenodo_data['metadata']['title'] + version
    zenodo_data['metadata']['description'] = version + zenodo_data['metadata']['description']
    zenodo_data['metadata']['related_identifiers'][0]['identifier'] = (
        zenodo_data)['metadata']['related_identifiers'][0]['identifier'] + version
    contributors = []
    creators = []
    with open(contributors_file) as f:
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
    if contributors:
        # Overwrite existing contributors and use the TSV file list (if available)
        zenodo_data['metadata']['contributors'] = contributors
        zenodo_data['metadata']['creators'] = creators


def generate_zenodo(meta_data: dict, zenodo_api_key: str) -> str:
    """Generate the zenodo record using the meta_data provided.

    :param meta_data: A zenodo data dictionary for a repo.
    :param zenodo_api_key: A Zenodo API key with write access to the SasView Zenodo community.
    :return: A DOI for the generated zenodo record.
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
                  params={'access_token': zenodo_api_key}, data=json.dumps(meta_data),
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


def update_sasview_metadata(version: str, doi: str, release_manager: str) -> None:
    """Update metadata in the SasView repo related to an upcoming release.

    :param version: The version of the release.
    :param doi: The DOI of the release.
    :param release_manager: The name of the release manager to be displayed in the citation GUI.
    """

    build_tools_directory = SASVIEW_PATH / 'build_tools'
    installers_directory = SASVIEW_PATH / 'installers'
    flatpak_directory = build_tools_directory / 'application_metadata'
    system_directory = SASVIEW_PATH / "src" / "sas" / "system"
    version_filename = system_directory /"version.py"
    citation_filename = system_directory / "citation.py"
    iss_file = installers_directory / 'installer.iss'
    flatpak_manifest = flatpak_directory / 'org.sasview.sasview.metainfo.xml'

    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    year = now.year

    # Update the version in version.py
    with open(version_filename, 'w') as file:
        file.write(version_template.format(version, year))

    # Update the citation information
    with open(citation_filename, 'w') as file:
        file.write(acknowledgement_template.format(doi, release_manager))

    # Update the Pyinstall config with the version and the year
    for line in fileinput.input(iss_file, inplace=True):
        if line.startswith('#define MyAppVersion'):
            print(f'#define MyAppVersion "{version}"', end='\r')
        elif line.startswith('#define MyAppPublisher'):
            print(f'#define MyAppPublisher "(c) 2009 - {year}, UTK, UMD, NIST, ORNL, ISIS, ESS, ILL, ANSTO, BAM, TU Delft, and DLS"', end='\r')
        else:
            print(line, end='')

    # Update the flatpak manifest with the version and date
    for line in fileinput.input(flatpak_manifest, inplace=True):
        if line.strip().startswith('<release '):
            print(f'    <release version="{version}" date="{date}"></release>', end='\r')
        else:
            print(line, end='')


def update_sasmodels_metadata(version, doi, release_manager):
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


def update_sasdata_metadata(version, doi, release_manager):
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


def parse_args():
    parser = argparse.ArgumentParser('Script to automate release process')
    parser.add_argument('-v', '--sasview_version', required=True)
    parser.add_argument('-s', '--sasmodels_version', required=True)
    parser.add_argument('-d', '--sasdata_version', required=True)
    parser.add_argument('-z', '--zenodo', default=False)
    return parser.parse_args()


def main(args=None):
    if not args:
        args = parse_args()

    sasview_version = args.sasview_version
    sasmodels_version = args.sasmodels_version
    sasdata_version = args.sasdata_version

    # Generate a list of contributors using a file, if that file exists, otherwise use the pre-defined list given here.
    if SASVIEW_CONTRIBUTORS_FILE.exists():
        generate_zenodo_data(sasview_data, sasview_version, SASVIEW_CONTRIBUTORS_FILE)
    if SASDATA_CONTRIBUTORS_FILE.exists():
        generate_zenodo_data(sasdata_data, sasdata_version, SASDATA_CONTRIBUTORS_FILE)
    if SASMODELS_CONTRIBUTORS_FILE.exists():
        generate_zenodo_data(sasmodels_data, sasmodels_version, SASMODELS_CONTRIBUTORS_FILE)

    release_manager = sasview_data['metadata']['creators'][0]['name'] if len(sasview_data['metadata']['contributors']) > 0 else ''

    # Generates zenodo doi if zenodo api key is provided ...
    new_sasview_doi = new_sasdata_doi = new_sasmodels_doi = ''
    if args.zenodo:
        zenodo_api_key = args.zenodo
        # ... but only if a version is given for the specific package
        if sasview_version:
            new_sasview_doi = generate_zenodo(sasview_data, zenodo_api_key)
        if sasmodels_version:
            new_sasmodels_doi = generate_zenodo(sasmodels_data, zenodo_api_key)
        if sasdata_version:
            new_sasdata_doi = generate_zenodo(sasdata_data, zenodo_api_key)

    # Regardless of previous checks and changes, apply changes to all packages (especially for the copyright year)
    update_sasview_metadata(sasview_version, new_sasview_doi, release_manager)
    update_sasmodels_metadata(sasmodels_version, new_sasmodels_doi, release_manager)
    update_sasdata_metadata(sasdata_version, new_sasdata_doi, release_manager)

    # Pull the license from a know location
    license_line = legal.copyright + "\r"
    update_file(SASMODELS_PATH / 'LICENSE.txt', license_line, 0)
    update_file(SASDATA_PATH / 'LICENSE.TXT', license_line, 0)
    update_file(SASVIEW_PATH / 'installers' / 'license.txt', license_line, -1)
    update_credits(SASVIEW_PATH / "src" / "sas" / "system" / "credits.html")


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
