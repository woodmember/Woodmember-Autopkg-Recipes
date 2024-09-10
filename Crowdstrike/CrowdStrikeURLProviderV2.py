import urllib.parse
import json
from autopkglib import Processor, ProcessorError, URLGetter

class CrowdStrikeSensorURL(Processor, URLGetter):
    description = "Retrieves the download URL for the CrowdStrike Falcon sensor."
    input_variables = {
        "base_url": {
            "required": True,
            "description": "Base URL for the CrowdStrike API.",
        },
        "oauth_token": {
            "required": True,
            "description": "OAuth2 token for API authentication.",
        },
        "version_offset": {
            "required": False,
            "description": "Version offset (0 for latest, 1 for N-1, 2 for N-2)",
            "default": "0",
        },
    }
    output_variables = {
        "url": {
            "description": "Download URL for the CrowdStrike Falcon sensor.",
        },
    }

    def get_sensor_info(self, base_url, oauth_token, version_offset):
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {oauth_token}"
        }
        
        sensor_list_url = f"{base_url}/sensors/combined/installers/v2?offset={version_offset}&limit=1&filter=platform%3A%22mac%22"
        
        try:
            sensor_data = self.download(sensor_list_url, headers=headers)
            sensor_json = json.loads(sensor_data)
            
            if not sensor_json.get('resources'):
                raise ProcessorError("No sensor resources found in the API response")
            
            sensor = sensor_json['resources'][0]
            return sensor['name'], sensor['sha256']
        except Exception as e:
            raise ProcessorError(f"Error retrieving sensor information: {str(e)}")

    def main(self):
        base_url = self.env["base_url"]
        oauth_token = self.env["oauth_token"]
        version_offset = self.env.get("version_offset", "0")

        try:
            sensor_name, sensor_sha256 = self.get_sensor_info(base_url, oauth_token, version_offset)
            
            download_url = f"{base_url}/sensors/entities/download-installer/v2?id={urllib.parse.quote(sensor_sha256)}"
            
            self.env["url"] = download_url
            self.output(f"CrowdStrike Falcon sensor URL: {download_url}")
        except Exception as e:
            raise ProcessorError(f"Error generating download URL: {str(e)}")

if __name__ == "__main__":
    processor = CrowdStrikeSensorURL()
    processor.execute_shell()
