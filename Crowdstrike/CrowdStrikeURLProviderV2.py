#!/usr/local/autopkg/python
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
import urllib.parse

from autopkglib import Processor, ProcessorError, URLGetter


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
            "description": "Version offset (0 for latest, 1 for N-1, 2 for N-2). Default is 1.",
        },
        "api_region_url": {
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

    def get_bearer_token(self, api_region_url, client_id, client_secret):
        token_url = f"{api_region_url}/oauth2/token"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = f"client_id={client_id}&client_secret={client_secret}"

        try:
            token_response = self.download(token_url, headers=headers, post_data=data)
            token_json = json.loads(token_response)
            return token_json["access_token"]
        except Exception as e:
            raise ProcessorError(f"Failed to acquire bearer token: {str(e)}")

    def get_sensor_info(self, api_region_url, bearer_token, version_offset):
        sensor_list_url = (
            f"{api_region_url}/sensors/combined/installers/v2?"
            f"offset={version_offset}&limit=1&filter=platform%3A%22mac%22"
        )
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {bearer_token}",
        }

        try:
            sensor_response = self.download(sensor_list_url, headers=headers)
            self.output(f"Sensor API Response: {sensor_response}", verbose_level=3)
            sensor_json = json.loads(sensor_response)
            if not sensor_json.get("resources"):
                raise ProcessorError("No sensor resources found in the API response")
            sensor = sensor_json["resources"][0]
            return sensor["name"], sensor["version"], sensor["sha256"]
        except json.JSONDecodeError as e:
            raise ProcessorError(f"Failed to parse sensor information JSON: {str(e)}, Response: {sensor_response}")
        except Exception as e:
            raise ProcessorError(f"Failed to retrieve sensor information: {str(e)}")

    def main(self):
        client_id = self.env.get("client_id")
        client_secret = self.env.get("client_secret")
        version_offset = self.env.get("version_offset", "1")  # Default to 1 (N-1)
        api_region_url = self.env.get("api_region_url", "https://api.crowdstrike.com")

        if not client_id or client_id == "%CLIENT_ID%":
            raise ProcessorError("The input variable 'client_id' was not set!")
        if not client_secret or client_secret == "%CLIENT_SECRET%":
            raise ProcessorError("The input variable 'client_secret' was not set!")

        try:
            bearer_token = self.get_bearer_token(api_region_url, client_id, client_secret)
            self.env["access_token"] = bearer_token
            self.output(f"Bearer token acquired", verbose_level=2)

            sensor_name, sensor_version, sensor_sha256 = self.get_sensor_info(
                api_region_url, bearer_token, version_offset
            )

            download_url = (
                f"{api_region_url}/sensors/entities/download-installer/v2?"
                f"id={urllib.parse.quote(sensor_sha256)}"
            )

            self.env["version"] = sensor_version
            self.env["download_url"] = download_url

            self.output(f"Sensor version that will be downloaded: {sensor_version}", verbose_level=1)
            self.output(f"Sensor name: {sensor_name}", verbose_level=2)
            self.output(f"Download URL: {download_url}", verbose_level=2)

        except Exception as e:
            raise ProcessorError(f"Error in CrowdStrikeURLProviderV2: {str(e)}")


if __name__ == "__main__":
    processor = CrowdStrikeURLProviderV2()
    processor.execute_shell()
