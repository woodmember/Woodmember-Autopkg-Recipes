#!/bin/bash

# Version comparison processor for AutoPkg
# Filename: VersionComparer.py

from autopkglib import Processor, ProcessorError
import os
import plistlib

__all__ = ["VersionComparer"]

class VersionComparer(Processor):
    """Compares version of current package with previously processed version."""
    input_variables = {
        "version": {
            "required": True,
            "description": "Current version being downloaded",
        },
        "version_file": {
            "required": False,
            "description": "Path to plist file storing previous version",
            "default": "",
        },
    }
    output_variables = {
        "version_changed": {
            "description": "Boolean indicating if version has changed",
        },
    }
    
    def main(self):
        version = self.env.get("version")
        version_file = self.env.get("version_file") or os.path.join(
            self.env.get("RECIPE_CACHE_DIR"),
            f"{self.env.get('NAME')}_version.plist"
        )
        
        # Default to changed unless we confirm it's the same
        version_changed = True
        
        # Check if version file exists
        if os.path.exists(version_file):
            try:
                with open(version_file, 'rb') as f:
                    version_data = plistlib.load(f)
                    previous_version = version_data.get("version", "")
                    
                    if previous_version == version:
                        self.output(f"Version {version} is the same as previous run. No need to repackage.")
                        version_changed = False
                    else:
                        self.output(f"Version changed from {previous_version} to {version}")
            except Exception as e:
                self.output(f"Error reading previous version: {e}")
        
        # Write current version to file for next time
        try:
            with open(version_file, 'wb') as f:
                plistlib.dump({"version": version}, f)
        except Exception as e:
            self.output(f"Error saving version info: {e}")
        
        self.env["version_changed"] = version_changed

if __name__ == "__main__":
    PROCESSOR = VersionComparer()
