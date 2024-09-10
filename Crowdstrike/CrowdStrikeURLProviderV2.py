#!/usr/local/autopkg/python
#
# Copyright 2023 Your Name
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

import json

from autopkglib import ProcessorError, URLGetter


__all__ = ["CrowdStrikeURLProviderV2"]


class CrowdStrikeURLProviderV2(URLGetter):

    """This processor finds the download URL for the CrowdStrike Sensor
    based on a specified version offset."""

    description = __doc__
    input_variables = {
        "CLIENT_ID": {"required": True, "description": "CrowdStrike API Client ID."},
        "CLIENT_SECRET": {
            "required": True,
            "description": "CrowdStrike API Client Secret.",
        },
        "VERSION_OFFSET": {
            "required": False,
            "default": "1",
            "description": (
                "Version offset from latest. 0 = latest, 1 = previous version, 2 = two versions back."
            ),
        },
        "API_REGION_URL": {
            "required": False,
            "default": "https://api.crowdstrike.com",
            "description": (
                "CrowdStrike Region your instance is associated with. "
                "Default region: https://api.crowdstrike.com"
            ),
        },
    }
    output_variables = {
        "download_url": {"description": "Returns the url to download."},
        "version": {"description": "Returns the version of the package to download."},
        "access_token": {
            "description": (
                "Authorization Bearer Token required to "
                "interact with the CrowdStrike API."
            )
        },
    }

    def main(self):
        # Define variables
        client_id = self.env.get("CLIENT_ID")
        client_secret = self.env.get("CLIENT_SECRET")
        version_offset = int(self.env.get("VERSION_OFFSET", "1"))
        api_region_url = self.env.get("API_REGION_URL", "https://api.crowdstrike.com")

        token_url = f"{api_region_url}/oauth2/token"
        installer_url = f"{api_region_url}/sensors/combined/installers/v2?offset={version_offset}&limit=1&filter=platform%3A%22mac%22"

        # Verify the input variables were provided
        if not client_id or client_id == "%CLIENT_ID%":
            raise ProcessorError("The input variable 'CLIENT_ID' was not set!")
        if not client_secret or client_secret == "%CLIENT_SECRET%":
            raise ProcessorError("The input variable 'CLIENT_SECRET' was not set!")

        # Get access token
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        token_data = f"client_id={client_id}&client_secret={client_secret}"

        try:
            token_response = self.download(url=token_url, headers=headers, post_data=token_data)
            token_json = json.loads(token_response)
            access_token = token_json["access_token"]
        except Exception as e:
            raise ProcessorError(f"Failed to acquire the bearer authentication token: {str(e)}")

        # Get installer information
        auth_headers = {
            "accept": "application/json",
            "authorization": f"bearer {access_token}",
        }

        try:
            installer_response = self.download(url=installer_url, headers=auth_headers)
            installer_json = json.loads(installer_response)
            
            if not installer_json.get("resources"):
                raise ProcessorError("No installer found for the specified version offset.")
            
            installer = installer_json["resources"][0]
            version = installer.get("version")
            sha256 = installer.get("sha256")
        except Exception as e:
            raise ProcessorError(f"Failed to get installer information: {str(e)}")

        # Set output variables
        download_url = f"{api_region_url}/sensors/entities/download-installer/v2?id={sha256}"
        
        self.env["access_token"] = access_token
        self.env["version"] = f"{version}.0"
        self.env["download_url"] = download_url

        self.output(f"Sensor version that will be downloaded: {self.env['version']}", verbose_level=1)
        self.output(f"Download URL: {download_url}", verbose_level=3)


if __name__ == "__main__":
    processor = CrowdStrikeURLProviderV2()
    processor.execute_shell()
