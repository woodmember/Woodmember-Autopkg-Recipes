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

"""See docstring for MacOSVersionProcessor class"""

import subprocess
import re
from autopkglib import Processor, ProcessorError

__all__ = ["MacOSVersionProcessor"]

class MacOSVersionProcessor(Processor):
    """Gets the latest version number of a specified macOS version from softwareupdate."""
    
    input_variables = {
        "MAC_VERSION": {
            "required": True,
            "description": "The marketing name of the macOS version (e.g., 'Sequoia', 'Sonoma', etc.)",
        },
        "INCLUDE_BETA": {
            "required": False,
            "description": "Whether to include beta versions (True/False).",
            "default": False,
        },
    }
    
    output_variables = {
        "version_number": {
            "description": "The latest version number of the specified macOS.",
        },
    }
    
    description = __doc__
    
    def main(self):
        """Main process"""
        
        # Get the input variables
        mac_version = self.env.get("MAC_VERSION")
        include_beta = self.env.get("INCLUDE_BETA", False)
        
        self.output(f"Getting latest version for macOS {mac_version}")
        
        try:
            # Construct the base command
            base_cmd = ["softwareupdate", "--list-full-installers"]
            
            # Add beta flag if requested
            if include_beta:
                base_cmd.append("--include-betas")
            
            # Execute the softwareupdate command
            cmd = ["/bin/bash", "-c", 
                   f"{' '.join(base_cmd)} | grep 'macOS {mac_version}' | cut -d: -f3 | cut -d, -f1 | head -1"]
            
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            (stdout, stderr) = proc.communicate()
            
            # Check for errors
            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                if "No available full installers found" in error_msg:
                    raise ProcessorError(f"No installers found for macOS {mac_version}")
                else:
                    raise ProcessorError(f"Error executing softwareupdate: {error_msg}")
            
            # Get the version number from stdout
            version_number = stdout.decode().strip()
            
            # Validate the version number format (should be like "15.0" or "15.0.1")
            if not version_number:
                raise ProcessorError(f"No version found for macOS {mac_version}")
                
            if not re.match(r'^\d+\.\d+(\.\d+)?$', version_number):
                raise ProcessorError(f"Invalid version number format: {version_number}")
            
            # Set the output variable
            self.env["version_number"] = version_number
            self.output(f"Found macOS {mac_version} version: {version_number}")
            
        except Exception as e:
            raise ProcessorError(f"Error getting macOS version: {e}")

if __name__ == "__main__":
    PROCESSOR = MacOSVersionProcessor()
    PROCESSOR.execute_shell()
