#!/usr/local/autopkg/python
#
# Fork Of MLBZ521 CrowdStrikeURLProvider.py
# Updated to V2 of the api
# All Credit belongs to MLBZ521
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
    version of the supplied Policy ID."""

    description = __doc__
    input_variables = {
        "client_id": {"required": True, "description": "CrowdStrike API Client ID."},
        "client_secret": {
            "required": True,
            "description": "CrowdStrike API Client Secret.",
        },
        "policy_id": {
            "required": True,
            "description": "CrowdStrike Policy ID to get the assigned Sensor version.",
        },
        "api_region_url": {
            "required": False,
            "default": "https://api.crowdstrike.com",
            "description": (
                "CrowdStrike Region your instance is associated with."
                "Default region:  https://api.crowdstrike.com"
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
        client_id = self.env.get("client_id")
        client_secret = self.env.get("client_secret")
        policy_id = self.env.get("policy_id")
        api_region_url = self.env.get("api_region_url", "https://api.crowdstrike.com")

        token_url = f"{api_region_url}/oauth2/token"
        policy_url = f"{api_region_url}/policy/combined/sensor-update/v2?filter=platform_name%3A'Mac'"
        installer_url = f"{api_region_url}/sensors/combined/installers/v2?filter=platform%3A%22mac%22"

        # Verify the input variables were provided
        if not client_id or client_id == "%CLIENT_ID%":
            raise ProcessorError("The input variable 'client_id' was not set!")
        if not client_secret or client_secret == "%CLIENT_SECRET%":
            raise ProcessorError("The input variable 'client_secret' was not set!")
        if not policy_id or policy_id == "%POLICY_ID%":
            raise ProcessorError("The input variable 'policy_id' was not set!")

        # Build the headers
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Build the required curl switches
        curl_opts = [
            "--url",
            f"{token_url}",
            "--request",
            "POST",
            "--data",
            f"client_id={client_id}&client_secret={client_secret}"
        ]

        try:
            # Initialize the curl_cmd, add the curl options, and execute curl
            curl_cmd = self.prepare_curl_cmd()
            self.add_curl_headers(curl_cmd, headers)
            curl_cmd.extend(curl_opts)
            response_token = self.download_with_curl(curl_cmd)

        except:
            raise ProcessorError("Failed to authenticate with the CrowdStrike API!")

        try:
            # Load the JSON response
            json_data = json.loads(response_token)
            access_token = json_data["access_token"]
            self.output(f"Access Token:  {access_token}", verbose_level=3)

        except:
            raise ProcessorError("Failed to acquire the bearer authentication token!")

        try:

            auth_headers = {
                "accept": "application/json",
                "authorization": f"bearer {access_token}",
            }

            # Execute curl
            response_policies = self.download(url=policy_url, headers=auth_headers)

            # Load the JSON response
            json_data = json.loads(response_policies)

        except:
            raise ProcessorError("Failed to get the Sensor Update Policies!")

        try:

            # Loop through the policies to find the desired policy id
            for policy in json_data["resources"]:

                if policy.get("id") == policy_id:

                    # Get the build assigned to the policy
                    build = policy.get("settings")["build"]

            build_version = build.split("|", 1)[0]
            self.output(
                f"Build version for matching Policy:  {build_version}", verbose_level=1)

        except:
            raise ProcessorError("Failed to match a Sensor Update Policy!")

        try:
            # Execute curl
            response_installers = self.download(url=installer_url, headers=auth_headers)

            # Load the JSON response
            json_data = json.loads(response_installers)

        except:
            raise ProcessorError("Failed to acquire list of installers!")

        try:
            # Loop through the installers to to find the desired build
            for installer in json_data["resources"]:

                # The build is the last string of digits of the version string
                if installer.get("version").split(".")[-1] == build_version:
                    version = installer.get("version")
                    sha256 = installer.get("sha256")

        except:
            raise ProcessorError(
                "Failed to match an available sensor version to the Policy assigned build version!")

        try:
            download_url = f"{api_region_url}/sensors/entities/download-installer/v2?id={sha256}"

            self.env["access_token"] = access_token
            # This version is appended to match the _actual_ CFBundleShortVersionString
            self.env["version"] = f"{version}.0"
            self.env["download_url"] = download_url

            self.output(
                f"Sensor version that will be downloaded: {self.env['version']}", verbose_level=1)
            self.output(f"Download URL:  {download_url}", verbose_level=3)

        except:
            raise ProcessorError("Something went wrong assigning environment variables!")


if __name__ == "__main__":
    processor = CrowdStrikeURLProviderV2()
    processor.execute_shell()
