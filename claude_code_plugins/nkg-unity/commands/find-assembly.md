---
allowed-tools: Bash(find:*), Bash(grep:*), Bash(ls:*)
argument-hint: [assembly-name-or-alias]
description: Find Unity assembly files using smart name matching and aliases
---

# Unity Assembly Finder

Intelligently find Unity C# assembly files based on names, aliases, or partial matches.

## Parameters
- `$1`: Assembly name, alias, or partial name to search for

## Common Unity Assembly Aliases
- **main/primary/game/runtime** → `Assembly-CSharp`
- **editor/edit/editor-scripts** → `Assembly-CSharp-Editor`
- **firstpass/preimport/pre-import** → `Assembly-CSharp-firstpass`
- **editor-firstpass/editor-preimport** → `Assembly-CSharp-Editor-firstpass`

## Search Results:
Available assembly files: !`find . -name "*.csproj" -type f`

Matching assemblies for "$1": !`find . -name "*$1*.csproj" -type f | head -5`

## Fuzzy Search Results:
Case-insensitive matches: !`find . -iname "*$1*.csproj" -type f | head -5`

## Best Match Algorithm:
1. Exact file name match
2. Alias resolution to standard Unity assemblies
3. Case-insensitive partial matching
4. Common Unity naming patterns

Report the most likely assembly file for compilation.