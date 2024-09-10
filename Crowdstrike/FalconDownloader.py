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
import subprocess
import plistlib

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
            "default": "1",
        },
    }
    output_variables = {
        "falcon_agent_path": {
            "description": "Path to the downloaded Falcon agent."
        }
    }

    def curl_cmd(self, url, headers=None, data=None, method="GET"):
        cmd = ["/usr/bin/curl", "-s", "-v"]
        if method == "POST":
            cmd.extend(["-X", "POST"])
        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])
        if data:
            cmd.extend(["-d", data])
        cmd.append(url)
        return cmd

    def run_curl(self, cmd):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout.decode(), stderr.decode()

    def main(self):
        client_id = self.env["client_id"]
        client_secret = self.env["client_secret"]
        version = self.env.get("version", "1")

        b64creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

        # Determine base URL
        base_url = "https://api.crowdstrike.com"
        token_cmd = self.curl_cmd(f"{base_url}/oauth2/token", method="POST", data=f"client_id={client_id}&client_secret={client_secret}")
        _, token_stderr = self.run_curl(token_cmd)
        
        for line in token_stderr.splitlines():
            if "Location:" in line:
                base_url = line.split()[2].strip().rsplit("/", 2)[0]
                break
        
        if not base_url:
            base_url = "https://api.crowdstrike.com"

        self.output(f"Using base URL: {base_url}")

        # API endpoints
        oauth_token = f"{base_url}/oauth2/token"
        oauth_revoke = f"{base_url}/oauth2/revoke"
        sensor_list = f"{base_url}/sensors/combined/installers/v2?offset={version}&limit=1&filter=platform%3A%22mac%22"
        sensor_dl = f"{base_url}/sensors/entities/download-installer/v2"

        # Get bearer token
        token_cmd = self.curl_cmd(oauth_token, method="POST", data=f"client_id={client_id}&client_secret={client_secret}")
        token_stdout, _ = self.run_curl(token_cmd)
        token_data = json.loads(token_stdout)
        bearer = token_data.get("access_token")
        
        if not bearer:
            raise ProcessorError("Failed to obtain bearer token")

        # Get sensor info
        sensor_cmd = self.curl_cmd(sensor_list, headers={"Authorization": f"Bearer {bearer}"})
        sensor_stdout, _ = self.run_curl(sensor_cmd)
        sensor_data = json.loads(sensor_stdout)

        if not sensor_data.get("resources"):
            raise ProcessorError("No sensor data found in the API response")

        sensor_name = sensor_data["resources"][0]["name"]
        sensor_sha = sensor_data["resources"][0]["sha256"]

        # Download the sensor
        download_cmd = self.curl_cmd(f"{sensor_dl}?id={sensor_sha}", headers={"Authorization": f"Bearer {bearer}"})
        download_stdout, _ = self.run_curl(download_cmd)

        # Save the downloaded file to the recipe cache dir
        download_path = os.path.join(self.env["RECIPE_CACHE_DIR"], sensor_name)
        with open(download_path, "wb") as file:
            file.write(download_stdout.encode())

        # Revoke the bearer token
        revoke_cmd = self.curl_cmd(oauth_revoke, method="POST", headers={
            "Authorization": f"Basic {b64creds}",
            "Content-Type": "application/x-www-form-urlencoded"
        }, data=f"token={bearer}")
        self.run_curl(revoke_cmd)

        # Set output variable
        self.env["falcon_agent_path"] = download_path
        self.output(f"Downloaded Falcon agent to: {download_path}")

if __name__ == "__main__":
    processor = FalconDownloader()
    processor.execute_shell()
