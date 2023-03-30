import subprocess
from autopkglib import Processor, ProcessorError

__all__ = ["FalconVersioner"]

class FalconVersioner(Processor):
    description = "Gets the version of a Falcon app using its Info.plist."
    input_variables = {
        "agentinfo": {
            "required": True,
            "description": "Path to the Falcon app's Info.plist file.",
        }
    }
    output_variables = {
        "version": {
            "description": "The version of the Falcon app."
        }
    }

    def main(self):
        agentinfo = self.env["agentinfo"]
        if not agentinfo:
            raise ProcessorError("The 'agentinfo' input variable is not set.")
        try:
            cf_bundle_short_version_string = subprocess.check_output(["defaults", "read", agentinfo, "CFBundleShortVersionString"]).decode("utf-8").strip()
            cf_bundle_version = subprocess.check_output(["defaults", "read", agentinfo, "CFBundleVersion"]).decode("utf-8").strip().replace(".", "")
        except subprocess.CalledProcessError as e:
            raise ProcessorError(f"Failed to read version info from {agentinfo}: {e}")
        result = f"{cf_bundle_short_version_string}.{cf_bundle_version}"
        self.output("Version: {}".format(result))
        self.env["version"] = result

if __name__ == "__main__":
    processor = FalconVersioner()
    processor.execute_shell()   
