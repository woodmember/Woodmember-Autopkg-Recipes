# DDPMDownloader AutoPkg Processor

## Overview

DDPMDownloader is a custom AutoPkg processor designed to retrieve the latest Dell Display and Peripheral Manager (DDPM) macOS download URL using Homebrew’s public API, and optionally download the package using a curl request with a Mozilla user-agent.

This avoids issues with Dell's CDN restrictions (HTTP 403) when downloading directly without proper headers.

---

## How It Works

1. Queries the Homebrew Cask JSON API:
   https://formulae.brew.sh/api/cask/ddpm.json

2. Extracts the current download URL for DDPM

3. Outputs:
   - `ddpm_url` — resolved download URL
   - `ddpm_filename` — name of the zip file
   - `ddpm_filepath` — full local path

