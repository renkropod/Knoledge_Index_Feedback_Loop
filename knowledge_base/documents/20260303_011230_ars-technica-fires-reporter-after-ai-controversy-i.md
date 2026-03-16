---
title: Ars Technica fires reporter after AI controversy involving fabricated quotes
source: hacker_news
url: https://futurism.com/artificial-intelligence/ars-technica-fires-reporter-ai-quotes
points: 606
---

Title: Ars Technica fires reporter after AI controversy involving fabricated quotes
Points: 606, Author: danso, Comments: 380

[[Introduction to Obsidian Sync|Obsidian Sync]] offers a headless client to sync vaults without using the desktop app. Useful for CI pipelines, agents, and automated workflows. Sync the latest changes or keep files continuously up to date.
Install [[Obsidian Headless]] **(open beta)** to interact with [[Introduction to Obsidian Sync|Obsidian Sync]] from the command line without the Obsidian desktop app. Headless Sync uses the same [[Security and privacy|encryption and privacy protections]] as the desktop app, including end-to-end encryption.
> [!error] Back up your data before you start
> 1. Always back up your data before you start in case anything unexpected happens.
> 2. Do not use *both* the desktop app Sync and Headless Sync on the same device, as it can cause data conflicts. Only use one sync method per device.
Install [[Obsidian Headless|Obsidian Headless]] **(open beta)**:
npm install -g obsidian-headless
You must have an active [[Plans and storage limits|Obsidian Sync subscription]].
ob sync-setup --vault "My Vault"
# Run continuous sync (watches for changes)
List all remote vaults available to your account, including shared vaults.
List locally configured vaults and their paths.
ob sync-create-remote --name "Vault Name" [--encryption <standard|e2ee>] [--password <password>] [--region <region>]
| `--name` | Vault name (required) |
| `--encryption` | `standard` for managed encryption, `e2ee` for end-to-end encryption |
| `--password` | End-to-end encryption password (prompted if omitted) |
| `--region` | Server [[Sync regions\|region]] (automatic if omitted) |
Set up sync between a local vault and a remote vault.
ob sync-setup --vault <id-or-name> [--path <local-path>] [--password <password>] [--device-name <name>] [--config-dir <name>]
| `--vault` | Remote vault ID or name (required) |
| `--path` | Local directory (default: current directory) |
| `--password` | E2E encryption password (prompted if omitted) |
| `--device-name` | Device name shown in [[Version history\|sync version history]] |
| `--config-dir` | [[Configuration folder\|Config directory]] name (default: `.obsidian`) |
Run sync for a configured vault.
ob sync [--path <local-path>] [--continuous]
| `--path` | Local vault path (default: current directory) |
| `--continuous` | Run continuously, watching for changes |
View or change [[Sync settings and selective syncing|sync settings]] for a vault. Run with no options to display the current configuration.
ob sync-config [--path <local-path>] [options]
| Option                | Description                                                                                                                                                                                                    |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--path`      
