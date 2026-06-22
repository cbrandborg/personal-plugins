PYTHON := env_var_or_default("PYTHON", "python3.13")

default:
    @just --list

# Register and immediately vendor one skill or a skill collection.
# Example: just add-skill mattpocock/skills skills/productivity mattpocock-productivity
add-skill source path plugin *FLAGS:
    {{PYTHON}} scripts/skills.py add {{source}} --path {{path}} --plugin {{plugin}} {{FLAGS}}

# Import an individual skill straight from a skills.sh page. Its source path is
# discovered from the backing Git repository.
add-skills-sh source plugin *FLAGS:
    {{PYTHON}} scripts/skills.py add {{source}} --plugin {{plugin}} {{FLAGS}}

# Check or apply updates for all registered upstream sources.
sync-skills *FLAGS:
    {{PYTHON}} scripts/skills.py sync {{FLAGS}}

# Alias for teams that prefer an explicit update verb.
update-skills *FLAGS:
    {{PYTHON}} scripts/skills.py sync --apply {{FLAGS}}

validate:
    {{PYTHON}} scripts/skills.py validate

test:
    {{PYTHON}} -m unittest discover -s tests -v

ci: validate test
