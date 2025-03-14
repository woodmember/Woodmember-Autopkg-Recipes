#!/usr/bin/env python
#
# Copyright 2025 Woodmember
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""See docstring for IOSVersionProcessor class"""

import json
import ssl
import os
import urllib.request
from autopkglib import Processor, ProcessorError

__all__ = ["IOSVersionProcessor"]

class IOSVersionProcessor(Processor):
    """Gets the latest iOS version number for a specified major version from MacAdmins feed."""
    
    input_variables = {
        "IOS_MAJOR_VERSION": {
            "required": True,
            "description": "The major version of iOS (e.g., 17, 18).",
        },
        "FEED_URL": {
            "required": False,
            "description": "URL to the MacAdmins iOS feed.",
            "default": "https://sofafeed.macadmins.io/v1/ios_data_feed.json",
        },
        "IGNORE_SSL_VERIFICATION": {
            "required": False,
            "description": "Set to True to bypass SSL certificate verification (less secure).",
            "default": False,
        },
    }
    
    output_variables = {
        "ios_version": {
            "description": "The latest version number of the specified iOS major version.",
        },
        "ios_build": {
            "description": "The build number of the latest iOS version.",
        },
        "ios_release_date": {
            "description": "The release date of the latest iOS version.",
        },
    }
    
    description = __doc__
    
    def main(self):
        """Main process"""
        
        # Get the input variables
        major_version = str(self.env.get("IOS_MAJOR_VERSION"))
        feed_url = self.env.get("FEED_URL")
        ignore_ssl = self.env.get("IGNORE_SSL_VERIFICATION", False)
        
        self.output(f"Getting latest version for iOS {major_version}")
        
        try:
            # Set up the request
            request = urllib.request.Request(feed_url)
            request.add_header("User-Agent", "AutoPkg/1.0")
            
            # Configure SSL context
            if ignore_ssl:
                self.output("WARNING: SSL certificate verification disabled")
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                response = urllib.request.urlopen(request, context=ctx)
            else:
                # Try to use macOS SSL certificates if available
                try:
                    # Check if the macOS certificates are available and create context
                    ssl_context = ssl.create_default_context()
                    # Try to locate the macOS certificates
                    cert_file = '/etc/ssl/cert.pem'  # Common location on macOS
                    if os.path.exists(cert_file):
                        ssl_context.load_verify_locations(cert_file)
                    
                    response = urllib.request.urlopen(request, context=ssl_context)
                except ssl.SSLCertVerificationError:
                    self.output("SSL verification failed. Try setting IGNORE_SSL_VERIFICATION=True if needed.")
                    raise
            
            data = json.loads(response.read())
            
            # Process the JSON data according to its structure
            # Find the OS version that matches the major version
            found = False
            for os_version_data in data.get("OSVersions", []):
                if os_version_data.get("OSVersion") == major_version:
                    found = True
                    # Get data from the "Latest" object
                    latest_data = os_version_data.get("Latest", {})
                    
                    # Set output variables
                    self.env["ios_version"] = latest_data.get("ProductVersion", "")
                    self.env["ios_build"] = latest_data.get("Build", "")
                    self.env["ios_release_date"] = latest_data.get("ReleaseDate", "")
                    
                    self.output(f"Found iOS {major_version} latest version: {self.env['ios_version']}")
                    self.output(f"Build number: {self.env['ios_build']}")
                    self.output(f"Release date: {self.env['ios_release_date']}")
                    break
            
            if not found:
                raise ProcessorError(f"No iOS {major_version} versions found in the feed")
            
        except Exception as e:
            raise ProcessorError(f"Error getting iOS version: {e}")

if __name__ == "__main__":
    PROCESSOR = IOSVersionProcessor()
    PROCESSOR.execute_shell()
