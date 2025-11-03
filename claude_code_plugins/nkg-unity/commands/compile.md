---
allowed-tools: Bash(dotnet build:*), Bash(dotnet:*), Bash(find:*), Bash(grep:*), Read, Edit, Write, Glob
argument-hint: [assembly-name-or-alias]
description: Compile Unity C# assembly with intelligent name matching and auto-fix errors
---

# Unity Assembly Compiler

You are to compile the specified Unity C# assembly using `dotnet build` and automatically fix any compilation errors that occur.

## Parameters
- `$1`: The name, alias, or partial name of the Unity assembly/project to compile
- `$ARGUMENTS`: All arguments passed to the command

## Your Task

1. **Smart Assembly Discovery**: Use intelligent matching to find the correct project file
2. **Execute compilation**: Run dotnet build on the found project
3. **Analyze errors**: Parse compilation errors and categorize them
4. **Apply fixes**: Automatically fix common compilation errors
5. **Rebuild**: Run compilation again to verify fixes

## Smart Assembly Name Matching

### Common Unity Assembly Aliases
- **main/primary/game/runtime** → `Assembly-CSharp`
- **editor/edit/editor-scripts** → `Assembly-CSharp-Editor`
- **firstpass/preimport/pre-import** → `Assembly-CSharp-firstpass`
- **editor-firstpass/editor-preimport** → `Assembly-CSharp-Editor-firstpass`

### Assembly Discovery Process
1. **Direct Match**: Try exact match with assembly name
2. **Alias Resolution**: Map common aliases to actual assembly names
3. **Fuzzy Matching**: Search for partial matches in available projects
4. **Unity Standards**: Check for standard Unity assembly naming patterns

### Available Projects Analysis:
Available C# projects: !`find . -name "*.csproj" -type f | head -10`

### Project Name Detection:
Assembly name patterns detected: !`find . -name "*.csproj" -type f | sed 's/.*\///g' | sed 's/\.csproj$//g' | head -10`

## Error Analysis and Fix Strategy

If the build fails, analyze the errors and apply these fixes systematically:

### CS0103: Name does not exist in current context
- Add missing `using` statements at the top of the file
- Common Unity namespaces: `UnityEngine`, `UnityEngine.UI`, `System.Collections.Generic`, `System.Linq`

### CS0246: Type or namespace name could not be found
- Add appropriate using directives
- Check for typos in type names
- Add missing assembly references if needed

### CS0117: Member does not exist
- Fix property/method name typos
- Check Unity API changes and deprecations
- Use correct Unity API methods

### CS1061: Extension method not found
- Add `using System.Linq;` for LINQ methods
- Check for correct method signatures

### CS0029: Cannot implicitly convert type
- Add explicit type casting
- Fix variable type declarations
- Use correct Unity component types

### CS1503: Argument mismatch
- Fix method parameter types
- Add missing arguments
- Correct parameter order

## Implementation Steps

### Step 1: Initial Compilation
Execute the build command and capture the output. Check if compilation succeeded or failed.

### Step 2: Error Parsing
Parse the build output to extract:
- Error codes (CSxxxx)
- File paths and line numbers
- Error descriptions
- Method/property names causing issues

### Step 3: Apply Fixes
For each error, apply the appropriate fix strategy:
1. Read the problematic file
2. Apply the fix based on error type
3. Save the changes
4. Document what was changed

### Step 4: Verification
Re-run the compilation to verify:
- All errors are resolved
- No new errors were introduced
- Build succeeds completely

### Step 5: Reporting
Provide a comprehensive report including:
- Initial error count
- Fixes applied
- Final build status
- Any remaining manual fixes needed

## Current Build Status:
Current dotnet build result: !`dotnet build "$1" --verbosity normal`

## Assembly Discovery Results:
Found potential assemblies: !`find . -name "*.csproj" -type f | grep -i "$1" | head -5`

## Best Match Analysis:
The best matching assembly is determined by:
1. Exact name matches to `$1`
2. Common Unity assembly aliases
3. Fuzzy string matching
4. Unity naming conventions

## Safety Measures
- Always create backups before modifying files
- Use conservative fix approaches
- Validate changes don't break existing functionality
- Provide clear explanations of all modifications

Execute the compilation and fix process now using the best-matching assembly.