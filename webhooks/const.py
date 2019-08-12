"""Consts."""
VERSION = "0.1.0"
KNOWN_ISSUES = {
    "[hacs] Missing migration step for 4": "HACS version 0.13.0+ can **only** migrate from version 0.12.0+.\\n\\nTo fix this issue you need to first upgrade to version 0.12.0, then upgrade to 0.13.0\\n\\nOr you can delete all the files containing `hacs` in the `.storage` directory and restart Home Assistant **(NB!: This will delete the status of the repositories you have installed.)**"
}
