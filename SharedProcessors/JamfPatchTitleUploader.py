#!/usr/local/autopkg/python
"""
JamfPatchTitleUploader processor for AutoPKG
Manages Jamf patch titles through the v2 API
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import base64
import ssl
from autopkglib import Processor, ProcessorError

__all__ = ["JamfPatchTitleUploader"]


class JamfPatchTitleUploader(Processor):
    """AutoPKG processor to manage Jamf patch titles"""
    
    description = "Creates or updates patch titles in Jamf Pro via the v2 API"
    
    input_variables = {
        "jamf_patch_title_url": {
            "required": True,
            "description": "URL to the Jamf Pro server (e.g., https://company.jamfcloud.com)"
        },
        "patch_softwaretitle": {
            "required": False,
            "description": "Name of the software title to search for (defaults to %NAME%)"
        },
        "version": {
            "required": True,
            "description": "Version number for the new patch"
        },
        "update_lower_version": {
            "required": False,
            "description": "Allow updating to a lower version number (default: False)"
        },
        "jamfpatchtitleuser": {
            "required": False,
            "description": "Username for Jamf API authentication (will try to read from com.github.autopkg plist if not provided)"
        },
        "jamfpatchtitlepassword": {
            "required": False,
            "description": "Password for Jamf API authentication (will try to read from com.github.autopkg plist if not provided)"
        }
    }
    
    output_variables = {
        "jamf_patch_result": {
            "description": "Dictionary containing results of the patch operation"
        },
        "jamf_patch_new_patch_id": {
            "description": "ID of the newly created patch"
        },
        "jamf_patch_software_title_id": {
            "description": "ID of the software title that was updated"
        }
    }
    
    def get_credentials(self):
        """Get API credentials from input variables or AutoPKG preferences"""
        username = self.env.get("jamfpatchtitleuser")
        password = self.env.get("jamfpatchtitlepassword")
        
        if not username or not password:
            try:
                from Foundation import CFPreferencesCopyAppValue
                username = CFPreferencesCopyAppValue("jamfpatchtitleuser", "com.github.autopkg")
                password = CFPreferencesCopyAppValue("jamfpatchtitlepassword", "com.github.autopkg")
            except ImportError:
                pass
        
        if not username or not password:
            raise ProcessorError("Missing jamfpatchtitleuser or jamfpatchtitlepassword. "
                               "Set them in the recipe or in com.github.autopkg preferences.")
        
        return username, password
    
    def create_ssl_context(self):
        """Create SSL context for HTTPS requests"""
        # Create SSL context that doesn't verify certificates (like curl's -k flag)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context
    
    def get_auth_token(self, jamf_patch_title_url, username, password):
        """Get authentication token from Jamf API"""
        token_url = f"{jamf_patch_title_url}/v2/auth/tokens"
        
        try:
            # Create basic auth header
            credentials = f"{username}:{password}"
            encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('ascii')
            
            req = urllib.request.Request(
                token_url,
                method='POST',
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': f'Basic {encoded_credentials}'
                }
            )
            
            ssl_context = self.create_ssl_context()
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                response_data = response.read().decode('utf-8')
                token_data = json.loads(response_data)
                return token_data.get('token')
                
        except urllib.error.HTTPError as e:
            raise ProcessorError(f"Failed to get authentication token: HTTP {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise ProcessorError(f"Failed to get authentication token: {e.reason}")
        except json.JSONDecodeError:
            raise ProcessorError("Invalid JSON response when getting auth token")
    
    def invalidate_token(self, jamf_patch_title_url, token):
        """Invalidate the authentication token"""
        try:
            invalidate_url = f"{jamf_patch_title_url}/v2/auth/invalidate-token"
            req = urllib.request.Request(
                invalidate_url,
                method='POST',
                headers={'Authorization': f'Bearer {token}'}
            )
            ssl_context = self.create_ssl_context()
            urllib.request.urlopen(req, timeout=30, context=ssl_context)
        except (urllib.error.HTTPError, urllib.error.URLError):
            # Don't fail the whole process if token invalidation fails
            self.output("Warning: Failed to invalidate auth token")
    
    def get_software_titles(self, jamf_patch_title_url, token):
        """Get all software titles from Jamf"""
        url = f"{jamf_patch_title_url}/v2/softwaretitles"
        
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )
            
            ssl_context = self.create_ssl_context()
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            raise ProcessorError(f"Failed to get software titles: HTTP {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise ProcessorError(f"Failed to get software titles: {e.reason}")
        except json.JSONDecodeError:
            raise ProcessorError("Invalid JSON response when getting software titles")
    
    def find_software_title_id(self, software_titles, title_name):
        """Find software title ID by name"""
        for title in software_titles:
            if title.get('name', '').lower() == title_name.lower():
                return title.get('softwareTitleId')
        
        raise ProcessorError(f"Software title '{title_name}' not found in Jamf")
    
    def get_software_title_details(self, jamf_patch_title_url, token, software_title_id):
        """Get detailed information about a software title including patches"""
        url = f"{jamf_patch_title_url}/v2/softwaretitles/{software_title_id}"
        
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )
            
            ssl_context = self.create_ssl_context()
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            raise ProcessorError(f"Failed to get software title details: HTTP {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise ProcessorError(f"Failed to get software title details: {e.reason}")
        except json.JSONDecodeError:
            raise ProcessorError("Invalid JSON response when getting software title details")
    
    def find_latest_patch_id(self, title_details):
        """Find the patch ID with absoluteOrderId: 0"""
        patches = title_details.get('patches', [])
        
        for patch in patches:
            if patch.get('absoluteOrderId') == 0:
                return patch.get('patchId')
        
        raise ProcessorError("No patch found with absoluteOrderId: 0")
    
    def compare_versions(self, version1, version2):
        """
        Compare two version strings
        Returns: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        def normalize_version(v):
            """Convert version string to list of integers for comparison"""
            # Remove any non-numeric suffixes like 'beta', 'rc', etc.
            import re
            # Split on dots and take only numeric parts
            parts = []
            for part in str(v).split('.'):
                # Extract numeric part from each component
                numeric_part = re.match(r'(\d+)', part)
                if numeric_part:
                    parts.append(int(numeric_part.group(1)))
                else:
                    parts.append(0)
            return parts
        
        v1_parts = normalize_version(version1)
        v2_parts = normalize_version(version2)
        
        # Pad the shorter version with zeros
        max_length = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_length - len(v1_parts)))
        v2_parts.extend([0] * (max_length - len(v2_parts)))
        
        # Compare each part
        for i in range(max_length):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        
        return 0
    
    def check_version_exists(self, title_details, version):
        """Check if a version already exists in the patches"""
        patches = title_details.get('patches', [])
        
        for patch in patches:
            if patch.get('version') == version:
                return True
        
        return False
    
    def get_current_patch_version(self, title_details):
        """Get the current version from the software title"""
        return title_details.get('currentVersion')
    
    def should_proceed_with_update(self, title_details, new_version, update_lower_version):
        """
        Determine if we should proceed with the update based on version comparison
        Returns: (should_proceed, reason)
        """
        # Check if the exact version already exists
        if self.check_version_exists(title_details, new_version):
            return False, f"Version {new_version} already exists in patch title"
        
        # Get current version from patch title
        current_version = self.get_current_patch_version(title_details)
        
        if not current_version:
            # No current version set, proceed
            return True, "No current version found, proceeding with update"
        
        # Compare versions
        comparison = self.compare_versions(new_version, current_version)
        
        if comparison == 0:
            # Versions are equal (shouldn't happen due to exact check above, but just in case)
            return False, f"Version {new_version} is the same as current version {current_version}"
        elif comparison < 0:
            # New version is lower than current
            if update_lower_version:
                return True, f"Proceeding with lower version {new_version} (update_lower_version=True)"
            else:
                return False, f"Version {new_version} is lower than current version {current_version}"
        else:
            # New version is higher than current, proceed
            return True, f"Version {new_version} is higher than current version {current_version}"
    
    def clone_patch(self, jamf_patch_title_url, token, patch_id, version):
        """Clone an existing patch with a new version"""
        url = f"{jamf_patch_title_url}/v2/patches/{patch_id}/clone"
        payload = {"version": version}
        
        try:
            data = json.dumps(payload).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=data,
                method='POST',
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )
            
            ssl_context = self.create_ssl_context()
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                response_data = response.read().decode('utf-8')
                clone_data = json.loads(response_data)
                return clone_data.get('patchId')
                
        except urllib.error.HTTPError as e:
            raise ProcessorError(f"Failed to clone patch: HTTP {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise ProcessorError(f"Failed to clone patch: {e.reason}")
        except json.JSONDecodeError:
            raise ProcessorError("Invalid JSON response when cloning patch")
    
    def enable_patch(self, jamf_patch_title_url, token, patch_id):
        """Enable a patch by setting enabled: true"""
        url = f"{jamf_patch_title_url}/v2/patches/{patch_id}"
        payload = {"enabled": True}
        
        try:
            data = json.dumps(payload).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=data,
                method='PUT',
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )
            
            ssl_context = self.create_ssl_context()
            urllib.request.urlopen(req, timeout=30, context=ssl_context)
                
        except urllib.error.HTTPError as e:
            raise ProcessorError(f"Failed to enable patch: HTTP {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise ProcessorError(f"Failed to enable patch: {e.reason}")
    
    def update_software_title_version(self, jamf_patch_title_url, token, software_title_id, version):
        """Update the currentVersion of a software title"""
        url = f"{jamf_patch_title_url}/v2/softwaretitles/{software_title_id}"
        payload = {"currentVersion": version}
        
        try:
            data = json.dumps(payload).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=data,
                method='PUT',
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {token}'
                }
            )
            
            ssl_context = self.create_ssl_context()
            urllib.request.urlopen(req, timeout=30, context=ssl_context)
                
        except urllib.error.HTTPError as e:
            raise ProcessorError(f"Failed to update software title version: HTTP {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            raise ProcessorError(f"Failed to update software title version: {e.reason}")
    
    def main(self):
        """Main processor execution"""
        jamf_patch_title_url = self.env.get("jamf_patch_title_url").rstrip('/')
        patch_softwaretitle = self.env.get("patch_softwaretitle", self.env.get("NAME"))
        version = self.env.get("version")
        update_lower_version = self.env.get("update_lower_version", False)
        
        if not patch_softwaretitle:
            raise ProcessorError("patch_softwaretitle not specified and %NAME% variable not available")
        
        # Convert string 'true'/'false' to boolean if needed
        if isinstance(update_lower_version, str):
            update_lower_version = update_lower_version.lower() in ('true', '1', 'yes')
        
        # Get credentials
        username, password = self.get_credentials()
        
        # Get authentication token
        self.output(f"Getting authentication token for {jamf_patch_title_url}")
        token = self.get_auth_token(jamf_patch_title_url, username, password)
        
        try:
            # Step 1: Get all software titles
            self.output("Getting software titles...")
            software_titles = self.get_software_titles(jamf_patch_title_url, token)
            
            # Step 2: Find software title ID by name
            self.output(f"Searching for software title: {patch_softwaretitle}")
            software_title_id = self.find_software_title_id(software_titles, patch_softwaretitle)
            self.output(f"Found software title ID: {software_title_id}")
            
            # Step 3: Get software title details and patches
            self.output("Getting software title details...")
            title_details = self.get_software_title_details(jamf_patch_title_url, token, software_title_id)
            
            # Check if we should proceed with the update
            current_version = self.get_current_patch_version(title_details)
            self.output(f"Current patch title version: {current_version}")
            self.output(f"Package version: {version}")
            self.output(f"Update lower version setting: {update_lower_version}")
            
            should_proceed, reason = self.should_proceed_with_update(title_details, version, update_lower_version)
            
            if not should_proceed:
                self.output(f"Skipping update: {reason}")
                
                # Set output variables for skipped update
                result = {
                    "success": True,
                    "software_title_id": software_title_id,
                    "new_patch_id": None,
                    "version": version,
                    "current_version": current_version,
                    "software_title": patch_softwaretitle,
                    "skipped": True,
                    "reason": reason
                }
                
                self.env["jamf_patch_result"] = result
                self.env["jamf_patch_new_patch_id"] = None
                self.env["jamf_patch_software_title_id"] = software_title_id
                return
            
            self.output(f"Proceeding with update: {reason}")
            
            # Step 4: Find the latest patch ID (absoluteOrderId: 0)
            self.output("Finding latest patch...")
            latest_patch_id = self.find_latest_patch_id(title_details)
            self.output(f"Found latest patch ID: {latest_patch_id}")
            
            # Step 5: Clone the patch with new version
            self.output(f"Cloning patch with version {version}...")
            new_patch_id = self.clone_patch(jamf_patch_title_url, token, latest_patch_id, version)
            self.output(f"Created new patch ID: {new_patch_id}")
            
            # Enable the new patch
            self.output("Enabling new patch...")
            self.enable_patch(jamf_patch_title_url, token, new_patch_id)
            
            # Step 6: Update software title current version
            self.output(f"Updating software title current version to {version}...")
            self.update_software_title_version(jamf_patch_title_url, token, software_title_id, version)
            
            # Set output variables
            result = {
                "success": True,
                "software_title_id": software_title_id,
                "new_patch_id": new_patch_id,
                "version": version,
                "previous_version": current_version,
                "software_title": patch_softwaretitle,
                "skipped": False
            }
            
            self.env["jamf_patch_result"] = result
            self.env["jamf_patch_new_patch_id"] = new_patch_id
            self.env["jamf_patch_software_title_id"] = software_title_id
            
            self.output(f"Successfully updated patch title for {patch_softwaretitle} from {current_version} to {version}")
            
        finally:
            # Always try to invalidate the token
            self.invalidate_token(jamf_patch_title_url, token)


if __name__ == "__main__":
    processor = JamfPatchTitleUploader()
    processor.execute_shell()
