default:
    @just --list

# Register and immediately vendor one skill or a skill collection.
# Example: just add-skill mattpocock/skills skills/productivity mattpocock-productivity
add-skill source path plugin *FLAGS:
    python3 scripts/skills.py add {{source}} --path {{path}} --plugin {{plugin}} {{FLAGS}}

# Import an individual skill straight from a skills.sh page. Its source path is
# discovered from the backing Git repository.
add-skills-sh source plugin *FLAGS:
    python3 scripts/skills.py add {{source}} --plugin {{plugin}} {{FLAGS}}

# Check or apply updates for all registered upstream sources.
sync-skills *FLAGS:
    python3 scripts/skills.py sync {{FLAGS}}

validate:
    python3 scripts/skills.py validate

ci: validate
