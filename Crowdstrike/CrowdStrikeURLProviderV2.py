#!/usr/local/autopkg/python
#
# Updated CrowdStrikeURLProviderV2 processor
# Incorporates logic from the provided shell script
# Uses the original method for bearer token acquisition
# Updated sensor info acquisition to match shell script
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
import subprocess
import plistlib

from autopkglib import ProcessorError, URLGetter


__all__ = ["CrowdStrikeURLProviderV2"]


class CrowdStrikeURLProviderV2(URLGetter):

    """This processor finds the download URL for the CrowdStrike Sensor."""

    description = __doc__
    input_variables = {
        "client_id": {"required": True, "description": "CrowdStrike API Client ID."},
        "client_secret": {
            "required": True,
            "description": "CrowdStrike API Client Secret.",
        },
        "version_offset": {
            "required": False,
            "default": "1",
            "description": "Version offset. 0 for latest, 1 for N-1, 2 for N-2, etc.",
        },
        "api_base_url": {
            "required": False,
            "default": "https://api.crowdstrike.com",
            "description": "CrowdStrike API base URL.",
        },
    }
    output_variables = {
        "download_url": {"description": "Returns the url to download."},
        "version": {"description": "Returns the version of the package to download."},
        "access_token": {
            "description": "Authorization Bearer Token required to interact with the CrowdStrike API."
        },
    }

    def get_access_token(self, base_url, client_id, client_secret):
        token_url = f"{base_url}/oauth2/token"
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

            # Load the JSON response
            json_data = json.loads(response_token)
            access_token = json_data["access_token"]
            self.output(f"Access Token: {access_token}", verbose_level=3)
            return access_token

        except:
            raise ProcessorError("Failed to acquire the bearer authentication token!")

    def get_sensor_info(self, base_url, access_token, version_offset):
        sensor_list_url = f"{base_url}/sensors/combined/installers/v2?offset={version_offset}&limit=1&filter=platform%3A%22mac%22"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {access_token}",
        }

        try:
            # Use curl command similar to the shell script
            curl_cmd = [
                "curl",
                "-s",
                "-X", "GET",
                sensor_list_url,
                "-H", f"accept: {headers['accept']}",
                "-H", f"authorization: {headers['authorization']}"
            ]
            
            process = subprocess.Popen(curl_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise ProcessorError(f"curl command failed: {stderr.decode()}")

            # Parse the JSON response
            json_data = json.loads(stdout.decode())
            
            # Extract sensor information using plistlib, similar to the shell script
            sensor_name = plistlib.loads(json_data["resources"][0]["name"].encode())
            sensor_sha256 = plistlib.loads(json_data["resources"][0]["sha256"].encode())
            sensor_version = plistlib.loads(json_data["resources"][0]["version"].encode())

            return {
                "name": sensor_name,
                "sha256": sensor_sha256,
                "version": sensor_version
            }

        except Exception as e:
            raise ProcessorError(f"Failed to acquire sensor information: {str(e)}")

    def main(self):
        client_id = self.env.get("client_id")
        client_secret = self.env.get("client_secret")
        version_offset = self.env.get("version_offset", "1")
        base_url = self.env.get("api_base_url", "https://api.crowdstrike.com")

        if not client_id or client_id == "%CLIENT_ID%":
            raise ProcessorError("The input variable 'client_id' was not set!")
        if not client_secret or client_secret == "%CLIENT_SECRET%":
            raise ProcessorError("The input variable 'client_secret' was not set!")

        self.output(f"Using API base URL: {base_url}", verbose_level=2)

        access_token = self.get_access_token(base_url, client_id, client_secret)

        sensor_info = self.get_sensor_info(base_url, access_token, version_offset)
        
        sensor_name = sensor_info["name"]
        sensor_sha256 = sensor_info["sha256"]
        sensor_version = sensor_info["version"]

        download_url = f"{base_url}/sensors/entities/download-installer/v2?id={sensor_sha256}"

        self.env["access_token"] = access_token
        self.env["version"] = f"{sensor_version}.0"
        self.env["download_url"] = download_url

        self.output(f"Sensor version that will be downloaded: {self.env['version']}", verbose_level=1)
        self.output(f"Sensor name: {sensor_name}", verbose_level=1)
        self.output(f"Download URL: {download_url}", verbose_level=2)

if __name__ == "__main__":
    processor = CrowdStrikeURLProviderV2()
    processor.execute_shell()
