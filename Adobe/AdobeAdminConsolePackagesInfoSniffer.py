#!/usr/local/autopkg/python
# pylint: disable = invalid-name
'''
Copyright (c) 2022, dataJAR Ltd.  All rights reserved.
     Redistribution and use in source and binary forms, with or without
     modification, are permitted provided that the following conditions are met:
             * Redistributions of source code must retain the above copyright
               notice, this list of conditions and the following disclaimer.
             * Redistributions in binary form must reproduce the above copyright
               notice, this list of conditions and the following disclaimer in the
               documentation and/or other materials provided with the distribution.
             * Neither data JAR Ltd nor the names of its contributors may be used to
               endorse or promote products derived from this software without specific
               prior written permission.
     THIS SOFTWARE IS PROVIDED BY DATA JAR LTD 'AS IS' AND ANY
     EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
     WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
     DISCLAIMED. IN NO EVENT SHALL DATA JAR LTD BE LIABLE FOR ANY
     DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
     (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
     LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
     ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
     (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
     SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
SUPPORT FOR THIS PROGRAM
    This program is distributed 'as is' by DATA JAR LTD.
    For more information or support, please utilise the following resources:
            http://www.datajar.co.uk

DESCRIPTION:

Captures key Adobe CC product Varibles needed for PKG creation. Based on the work of DATA JAR. Info on the source project can be found here: https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20Admin%20Console%20Packages/AdobeAdminConsolePackagesPkgInfoCreator.py

Ensure you shout the orginal publisher a beer when ever you have the chance.

This is a striped down version of the orginal project that removes all but that info gathering part of the processor. This also adds the  "aacp_packages_path" as a input varible. Allowing the admin to choose where they keep their Adobe CC Admin .ZIPS/ downloads.

'''

# Standard Imports
import json
import os
import re
import xml
from xml.etree import ElementTree


# AutoPkg imports
# pylint: disable = import-error
from autopkglib import (Processor,
                        ProcessorError)


# Define class
__all__ = ['AdobeAdminConsolePackagesInfoSniffer']
__version__ = ['1.0']


# Class def
class AdobeAdminConsolePackagesInfoSniffer(Processor):
    '''
       Parses generated Adobe Admin Console Packages to generate installation information.
    '''

    description = __doc__

    input_variables = {
    }

    output_variables = {
        'aacp_application_architecture_type': {
            'description': 'The architecture type for the title, either arm64 or x86_64',
        },
        'aacp_application_bundle_id': {
            'description': 'Value of the titles CFBundleIdentifier.',
        },
        'aacp_application_description': {
            'description': 'Short description of the title.',
        },
        'aacp_application_display_name': {
            'description': 'Display name of the title.',
        },
        'aacp_application_full_path': {
            'description': 'Full path to the application bundle on disk, as per Terminal etc, not Finder.',
        },
        'aacp_application_install_lang': {
            'description': 'The titles installation langauage.',
        },
        'aacp_application_json_path': {
            'description': 'Path to the tiles Application.json file.',
        },
        'aacp_application_major_version': {
            'description': 'The major version of the title.',
        },
        'aacp_application_sap_code': {
            'description': 'The titles sap code.',
        },
        'aacp_blocking_applications': {
            'description': 'Sorted set of the conflicting processes.',
        },
        'aacp_install_pkg_path': {
            'description': 'Path to the Adobe*_Install.pkg.',
        },
        'aacp_json_path': {
            'description': 'Path to AdobeAutoPkgApplicationData.json.',
        },
        'aacp_matched_json': {
            'description': ('dict from AdobeAutoPkgApplicationData.json, which matches the '
                            '"aacp_application_sap_code" and "aacp_application_major_version".'),
        },
        'aacp_option_xml_path': {
            'description': 'Path to the tiles optionXML.xml file.',
        },
        'aacp_parent_dir': {
            'description': 'Path to parent directory of this processor.',
        },
        'aacp_proxy_xml_path': {
            'description': 'Acrobat only, path to proxy.xml.',
        },
        'aacp_target_folder': {
            'description': 'The name of the folder within the pkg to check files for metadata.',
        },
        'aacp_uninstall_pkg_path': {
            'description': 'Path to the Adobe*_Uninstall.pkg.',
        },
        'additional_pkginfo': {
            'description':
                'Additonal pkginfo fields extracted from the Adobe metadata.',
        },
        'version': {
            'description': 'The titles version.',
        },
        'aacp_packages_path': {
            'description': 'Path to projects unzip folder',
        },
        'aacp_unpacked_path': {
            'description': 'Path To CC app unpacked directory',
        }
    }


    def main(self):
        '''
            Find the Adobe*_Install.pkg in the Downloads dir based on the name, raise
            if corresponding *_Uninstall.pkg is missing.
        '''

        # Progress notification
        self.output("Starting versioner process...")

        # Get set packages_path
        # self.env['aacp_packages_path'] = os.path.expanduser('~/Downloads/')
        # self.output(f"aacp_packages_path: {self.env['aacp_packages_path']}")

        # Check that packages_path exists
        if not os.path.exists(self.env['aacp_packages_path']):
            raise ProcessorError(f"ERROR: Cannot locate directory, "
                                 f"{self.env['aacp_packages_path']}... exiting...")

        # Check that packages_path is a directory
        if not os.path.isdir(self.env['aacp_packages_path']):
            raise ProcessorError(f"ERROR: {self.env['aacp_packages_path']} is a not a "
                                  "directory... exiting...")

        # Path to Adobe*_Install.pkg
        self.env['aacp_install_pkg_path'] = (os.path.join(self.env['aacp_packages_path'],
                                                          self.env['NAME'], 'Build',
                                                          self.env['NAME'] + '_Install.pkg'))

        # Check that the path exists, raise if not
        if not os.path.exists(self.env['aacp_install_pkg_path']):
            raise ProcessorError(f"ERROR: Cannot find "
                                 f"{self.env['aacp_install_pkg_path']}... exiting...")
        self.output(f"aacp_install_pkg_path: {self.env['aacp_install_pkg_path']}")

        # Path to Adobe*_Uninstall.pkg
        self.env['aacp_uninstall_pkg_path'] = (os.path.join(self.env['aacp_packages_path'],
                                                            self.env['NAME'], 'Build',
                                                            self.env['NAME'] + '_Uninstall.pkg'))

        # Process the titles optionXML.xml
        self.process_optionxml_xml()


    def process_optionxml_xml(self):
        '''
            Process the titles optionXML.xml
        '''

        # Var declaration
        self.env['aacp_application_install_lang'] = None

        # Path to titles optionXML.xml
        self.env['aacp_option_xml_path'] = os.path.join(self.env['aacp_unpacked_path'])
        if not os.path.exists(self.env['aacp_option_xml_path']):
            raise ProcessorError(f"ERROR: Cannot find {self.env['aacp_option_xml_path']}... "
                                  "exiting...")
        self.output(f"aacp_option_xml_path: {self.env['aacp_option_xml_path']}")

        # Progress notification
        self.output(f"Processing: {self.env['aacp_option_xml_path']}...")

        # Try to parse option_xml, raise if an issue
        try:
            option_xml = ElementTree.parse(self.env['aacp_option_xml_path'])
        except xml.etree.ElementTree.ParseError as err_msg:
            raise ProcessorError from err_msg

        # Check to see if HDMedia keys set
        for hd_media in option_xml.findall('.//HDMedias/HDMedia'):
            # If we have HDMedia, set vars
            if hd_media.findtext('MediaType') == 'Product':
                self.env['aacp_application_install_lang'] = hd_media.findtext('installLang')
                self.env['aacp_application_sap_code'] = hd_media.findtext('SAPCode')
                self.env['aacp_target_folder'] = hd_media.findtext('TargetFolderName')
                self.env['aacp_application_major_version'] = hd_media.findtext('baseVersion')
                self.env['version'] = hd_media.findtext('productVersion')

        # If no HDMedia is found, then self.env['aacp_application_install_lang'] will be none
        if not self.env['aacp_application_install_lang']:
            # Get vars for RIBS media
            for ribs_media in option_xml.findall('.//Medias/Media'):
                self.env['aacp_application_install_lang'] = ribs_media.findtext('installLang')
                self.env['aacp_application_sap_code'] = ribs_media.findtext('SAPCode')
                self.env['aacp_target_folder'] = ribs_media.findtext('TargetFolderName')
                self.env['aacp_application_major_version'] = ribs_media.findtext('prodVersion')
                self.env['version'] = ribs_media.findtext('prodVersion')

        # Check for Processor Architecture
        self.env['aacp_application_architecture_type'] = (
            option_xml.findtext('ProcessorArchitecture').lower())
        if not self.env['aacp_application_architecture_type'] in ['arm64', 'macuniversal', 'x64']:
            raise ProcessorError(f"architecture_type: "
                                 f"{self.env['aacp_application_architecture_type']},"
                                 f" is neither arm64, macuniversal nor x64... exiting...")
        if self.env['aacp_application_architecture_type'] == 'x64':
            self.env['aacp_application_architecture_type'] = 'x86_64'

        # Display progress
        self.output(f"aacp_application_sap_code: {self.env['aacp_application_sap_code']}")
        self.output(f"aacp_target_folder: {self.env['aacp_target_folder']}")
        self.output(f"aacp_application_architecture_type: "
                    f"{self.env['aacp_application_architecture_type']}")
        self.output(f"aacp_application_install_lang: {self.env['aacp_application_install_lang']}")
        self.output(f"aacp_application_major_version: {self.env['aacp_application_major_version']}")

        # If the we're looking at Acrobat, then we need to process things differently
        ##if self.env['aacp_application_sap_code'] == 'APRO':
          ##  self.process_apro_installer()
        ##else:
            # Set application_json_path
          ##  self.env['aacp_application_json_path'] = os.path.join(self.env['aacp_install_pkg_path'],
                                                                  ##'Contents/Resources/HD',
                                                                  ##self.env['aacp_target_folder'],
                                                                  ##'Application.json')    

        # Try to parse xml, raise if an issue
        ##try:
            ##parse_xml = ElementTree.parse(self.env['aacp_unpacked_path'])
       ## except xml.etree.ElementTree.ParseError as err_msg:
            ##raise ProcessorError from err_msg

        # Get root of xml
        ##root = parse_xml.getroot()

        # Get app_version
        ##self.env['version'] = (root.findtext
                                  ## ('./HDMedia/Property[@name=\'ProductVersion\']'))
        ##self.output(f"version: {self.env['version']}")

        # Set to []
        ##self.env['aacp_blocking_applications'] = []

if __name__ == '__main__':
    PROCESSOR = AdobeAdminConsolePackagesPkgInfoCreator()
