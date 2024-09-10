#!/usr/local/autopkg/python
#
# Copyright 2023 Woodmember
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

import os
import json
import base64
from autopkglib import Processor, ProcessorError
import requests

__all__ = ["FalconDownloader"]

class FalconDownloader(Processor):
    description = "Downloads the latest Falcon agent from CrowdStrike API."
    input_variables = {
        "client_id": {
            "required": True,
            "description": "CrowdStrike API client ID.",
        },
        "client_secret": {
            "required": True,
            "description": "CrowdStrike API client secret.",
        },
        "version": {
            "required": False,
            "description": "Version to download. 0 for latest, 1 for N-1, etc.",
            "default": "0",
        },
    }
    output_variables = {
        "falcon_agent_path": {
            "description": "Path to the downloaded Falcon agent."
        }
    }

    def main(self):
        client_id = self.env["client_id"]
        client_secret = self.env["client_secret"]
        version = self.env.get("version", "0")

        # Base URL and endpoints
        base_url = "https://api.crowdstrike.com"
        oauth_token = f"{base_url}/oauth2/token"
        oauth_revoke = f"{base_url}/oauth2/revoke"
        sensor_list = f"{base_url}/sensors/combined/installers/v2?offset={version}&limit=1&filter=platform%3A%22mac%22"
        sensor_dl = f"{base_url}/sensors/entities/download-installer/v2"

        # Get bearer token
        token_response = requests.post(oauth_token, data={
            "client_id": client_id,
            "client_secret": client_secret
        })
        token_response.raise_for_status()
        bearer = token_response.json()["access_token"]

        # Get sensor info
        headers = {"Authorization": f"Bearer {bearer}"}
        sensor_response = requests.get(sensor_list, headers=headers)
        sensor_response.raise_for_status()
        sensor_data = sensor_response.json()

        sensor_name = sensor_data["resources"][0]["name"]
        sensor_sha = sensor_data["resources"][0]["sha256"]

        # Download the sensor
        download_response = requests.get(f"{sensor_dl}?id={sensor_sha}", headers=headers)
        download_response.raise_for_status()

        # Save the downloaded file to the recipe cache dir
        download_path = os.path.join(self.env["RECIPE_CACHE_DIR"], sensor_name)
        with open(download_path, "wb") as file:
            file.write(download_response.content)

        # Revoke the bearer token
        b64creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        revoke_headers = {
            "Authorization": f"Basic {b64creds}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        revoke_data = {"token": bearer}
        requests.post(oauth_revoke, headers=revoke_headers, data=revoke_data)

        # Set output variable
        self.env["falcon_agent_path"] = download_path
        self.output(f"Downloaded Falcon agent to: {download_path}")

if __name__ == "__main__":
    processor = FalconDownloader()
    processor.execute_shell()
