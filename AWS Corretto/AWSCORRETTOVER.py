#!/usr/local/autopkg/python
#
# Copyright 2024 Daniel Woodcock (Woodmember) 
# Based on the work of Zack Thompson (MLBZ521)
# Extracts a version string compatible with Jamf patch management.
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

import plistlib
from autopkglib import Processor, ProcessorError

__all__ = ["AWSCORRETTOVER"]

class AWSCORRETTOVER(Processor):
    """This processor finds the AWS Corretto version in a package using CFBundleVersion.
    """

    description = __doc__
    input_variables = {
        "plist": {
            "required": True,
            "description": "The plist file that will be searched.",
        }
    }
    output_variables = {
        "version": {
            "description": "Returns the AWS Corretto version found."
        }
    }

    def main(self):
        # Define the plist file.
        plist = self.env.get("plist")

        try:
            with open(plist, "rb") as file:
                plist_contents = plistlib.load(file)
        except Exception as error:
            raise ProcessorError("Unable to load the specified plist file.") from error

        # Get the version from CFBundleVersion
        version = plist_contents.get("CFBundleVersion")
        
        if version:
            self.env["version"] = version
            self.output(f"version: {self.env['version']}")
        else:
            raise ProcessorError("Unable to determine the AWS Corretto version from CFBundleVersion.")

if __name__ == "__main__":
    PROCESSOR = AWSCORRETTOVER()
    PROCESSOR.execute_shell()
