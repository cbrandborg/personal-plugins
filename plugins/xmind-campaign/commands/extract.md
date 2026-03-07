---
name: extract
description: Extract an XMind file and prepare it for DnD campaign import. Runs extract_xmind.py, saves JSON to _extracted/, and displays a summary of what was found.
argument-hint: "[path to .xmind file]"
allowed-tools: [Read, Write, Bash, Glob, AskUserQuestion]
---

# Extract XMind File

Extract the contents of an XMind file into structured JSON for campaign import.

## Steps

1. **Get the XMind file path**
   - If the user provided a path as an argument, use it directly
   - Otherwise ask: "What is the path to the .xmind file?"
   - Verify the file exists and has a `.xmind` extension

2. **Determine output directory**
   - Set output dir to `_extracted/` in the same folder as the `.xmind` file
   - Example: `/path/to/campaign/MyMap.xmind` → `/path/to/campaign/_extracted/`

3. **Run extraction**
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/extract_xmind.py" "[xmind_path]" "[output_dir]"
   ```

4. **Read and summarise results**
   - Read `_extracted/full_tree.json` — report total top-level branches found
   - Read `_extracted/summary_report.txt` — report how many summary subtrees were found
   - List each `branch_XX.json` with its node count and notes character count from the script output

5. **Flag summary subtrees**
   - If summary subtrees > 0, display a prominent warning:
     ```
     ⚠ WARNING: X summary subtree(s) found — these often contain stat blocks, dialogue, and encounter details. They MUST be covered during generate.
     ```

6. **Load settings for vault path**
   - Read `~/.claude/xmind-campaign.local.md` if it exists
   - If a campaign matching the `.xmind` filename or directory is found, show the stored vault path and ask to confirm or change it
   - Otherwise ask: "What is the path to the Obsidian vault for this campaign? (e.g. /Users/priv/Documents/private-obsidian/DnD/Campaign Name)"
   - Save to settings file

7. **Report**
   Display:
   ```
   Extraction complete.
   Branches: X
   Total nodes with notes: X
   Summary subtrees: X (see _extracted/summary_report.txt)
   Vault: [path]

   Next steps:
   - Run /xmind-campaign:audit-tree to review the node tree before generating
   - Or run /xmind-campaign:generate to start creating vault files
   ```

## Error Handling

- If the file does not exist: tell the user and stop
- If Python is not available: tell the user `python3` is required
- If `content.json` is not found in the ZIP: the file may be corrupt or not a valid XMind — tell the user
