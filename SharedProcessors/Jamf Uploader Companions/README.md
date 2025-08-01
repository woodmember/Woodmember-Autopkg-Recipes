# JamfPatchTitleUploader Setup Guide

## Prerequisites

#### - The software title must already exist in Jamf.
You will still need to create the Patch Title, its components, and the first patch version in Title Editor. 
As this processor is only cloning the previously created patch version in Title Editor, you still need to do the groundwork.
  
#### - You need appropriate API permissions in Jamfs Title Editor

#### - The existing patch structure will be used as a template

## Setting Up Credentials

You will need to first create a API user in your Patch Title Settings. Once created you need to add both the username and password of this new api user to your AutoPKG config. 

Do this by following the steps below:

Add your Jamf API credentials to the AutoPKG preferences:

```
# Set the username
defaults write com.github.autopkg jamfpatchtitleuser "your_jamf_username"

# Set the password
defaults write com.github.autopkg jamfpatchtitlepassword "your_jamf_password"
```

You can verify they're set by:
```
defaults read com.github.autopkg jamfpatchtitleuser

defaults read com.github.autopkg jamfpatchtitlepassword
```

## Using in Recipes

### Required Input Variables:
- `jamf_patch_title_url`: Your Jamf Pro server URL
- `version`: Version number for the new patch. Set this to your %version% varible

### Optional Input Variables:
- `patch_softwaretitle`: Name of the software title (defaults to %NAME% if not specified). Use if your Patch Title differs from the default name of what you are packaging
- `update_lower_version`: Allow updating to a lower version number (default: False)
- `jamfpatchtitleuser`: Username (if not set in preferences)
- `jamfpatchtitlepassword`: Password (if not set in preferences)

### Output Variables:
- `jamf_patch_result`: Dictionary with operation results
- `jamf_patch_new_patch_id`: ID of the newly created patch
- `jamf_patch_software_title_id`: ID of the software title

## Example Usage in Recipes

### Basic Usage (using %NAME% default):
```xml
<dict>
    <key>Processor</key>
    <string>JamfPatchTitleUploader</string>
    <key>Arguments</key>
    <dict>
        <key>jamf_patch_title_url</key>
        <string>https://yourcompanyid.appcatalog.jamfcloud.com</string>
        <key>version</key>
        <string>%version%</string>
        <!-- patch_softwaretitle will default to %NAME% -->
    </dict>
</dict>
```

### Custom Software Title Name:
```xml
<dict>
    <key>Processor</key>
    <string>JamfPatchTitleUploader</string>
    <key>Arguments</key>
    <dict>
        <key>jamf_patch_title_url</key>
        <string>https://yourcompanyid.appcatalog.jamfcloud.com</string>
        <key>patch_softwaretitle</key>
        <string>Monitor Control</string>
        <key>version</key>
        <string>%version%</string>
    </dict>
</dict>
```

### Allow Lower Version Updates:
```xml
<dict>
    <key>Processor</key>
    <string>JamfPatchTitleUploader</string>
    <key>Arguments</key>
    <dict>
        <key>jamf_patch_title_url</key>
        <string>https://yourcompanyid.appcatalog.jamfcloud.com/string>
        <key>version</key>
        <string>%version%</string>
        <key>update_lower_version</key>
        <true/>
    </dict>
</dict>
```

## What the Processor Does

1. **Authenticates** with Jamf using token-based auth
2. **Searches** for the specified software title by name (defaults to %NAME%)
3. **Compares versions** using intelligent version comparison:
   - Checks if the exact version already exists (skips if found)
   - Compares new version with current patch title version
   - By default, skips if new version is lower than current version
   - Respects `update_lower_version` flag to allow downgrade updates
4. **Skips processing** if version check fails (preventing duplicates/downgrades)
5. **Finds** the latest patch (absoluteOrderId: 0) if proceeding
6. **Clones** that patch with the new version number
7. **Enables** the newly created patch
8. **Updates** the software title's current version
9. **Cleans up** by invalidating the auth token

## Version Comparison Logic

### Default Behavior (update_lower_version = False):
- **Version 1.8.1 → 1.8.2**: ✅ Proceeds (higher version)
- **Version 1.8.1 → 1.8.1**: ❌ Skips (same version)
- **Version 1.8.1 → 1.8.0**: ❌ Skips (lower version)
- **Version 1.8.1 → 1.7.9**: ❌ Skips (lower version)

### With update_lower_version = True:
- **Version 1.8.1 → 1.8.2**: ✅ Proceeds (higher version)
- **Version 1.8.1 → 1.8.1**: ❌ Skips (same version)
- **Version 1.8.1 → 1.8.0**: ✅ Proceeds (lower version allowed)
- **Version 1.8.1 → 1.7.9**: ✅ Proceeds (lower version allowed)

## Integration with Existing Workflows

This processor is designed to work alongside your existing AutoPKG workflows. You can use it after your normal download/package processors to automatically update Jamf patch titles when new versions are detected.

Its advised you run this processor just before your run JamfPatchUploader processor in your recipe.

## What This Processor Can Not Do!

#### 1. Create a Patch Title

You will still need to create the Patch Title, its components, and the first patch version in Title Editor. 
As this processor is only cloning the previously created patch version in Title Editor, you still need to do the groundwork.

#### 2. Won't Update Minimum Operating System Version

If an application’s minimum operating system supported changes, you will need to manually update this via Title Editor. 
Once done for the latest patch version, the cloning function will copy this for future versions.
