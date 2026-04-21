#!/usr/local/autopkg/python

from autopkglib import Processor, ProcessorError
import subprocess
import json
import os

__all__ = ["DDPMDownloader"]


class DDPMDownloader(Processor):
    description = "Fetch Dell DDPM URL from Homebrew API and optionally download it with curl."
    input_variables = {
        "download": {
            "required": False,
            "description": "Set to True to download the file (default: True)",
        }
    }
    output_variables = {
        "ddpm_url": {
            "description": "Resolved DDPM download URL",
        },
        "ddpm_filename": {
            "description": "Filename of the downloaded zip",
        },
        "ddpm_filepath": {
            "description": "Full path to downloaded file",
        },
    }

    def main(self):

        download_flag = self.env.get("download", True)

        # Use AutoPkg cache directory
        cache_dir = self.env.get("RECIPE_CACHE_DIR")
        if not cache_dir:
            raise ProcessorError("RECIPE_CACHE_DIR not set")

        download_dir = os.path.join(cache_dir, "downloads")
        os.makedirs(download_dir, exist_ok=True)

        # Step 1: Fetch Homebrew JSON
        brew_api = "https://formulae.brew.sh/api/cask/ddpm.json"

        try:
            output = subprocess.check_output(
                ["/usr/bin/curl", "-s", brew_api]
            )
            data = json.loads(output)
        except Exception as e:
            raise ProcessorError(f"Failed to fetch Homebrew JSON: {e}")

        # Step 2: Extract URL
        try:
            url = data["url"]
        except KeyError:
            raise ProcessorError("Could not find URL in Homebrew JSON")

        self.output(f"Found URL: {url}")
        self.env["ddpm_url"] = url

        # Step 3: Extract filename
        filename = url.split("/")[-1]
        filepath = os.path.join(download_dir, filename)

        self.env["ddpm_filename"] = filename
        self.env["ddpm_filepath"] = filepath

        self.output(f"Filename: {filename}")
        self.output(f"Path: {filepath}")

        # Step 4: Optional download
        if not download_flag:
            self.output("Download disabled — exiting early")
            return

        self.output("Downloading with curl + Mozilla user-agent...")

        curl_cmd = [
            "/usr/bin/curl",
            "-L",
            "-A",
            "Mozilla/5.0",
            url,
            "--output",
            filepath,
        ]

        try:
            subprocess.check_call(curl_cmd)
        except subprocess.CalledProcessError as e:
            raise ProcessorError(f"Download failed: {e}")

        self.output("Download complete")


if __name__ == "__main__":
    processor = DDPMDownloader()
    processor.execute_shell()