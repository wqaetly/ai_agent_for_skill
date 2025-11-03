---
allowed-tools: Bash(git status), Bash(git diff), Bash(git add .), Bash(git commit -m:*), Bash(git rebase), Bash(git push), Bash(git log --oneline -5)
description: Execute git rebase, commit, and push in sequence
---

# Git Rebase, Commit, and Push

You are to execute git rebase, git commit, and git push in sequence to update and push changes to the remote repository.

## Your Task

1. **Check Status**: Analyze current git status and changes
2. **Execute Rebase**: Perform git rebase to update local branch
3. **Stage and Commit**: Add all changes and commit with appropriate message
4. **Push Changes**: Push changes to remote repository

## Implementation Steps

### Step 1: Status Analysis
Check current git status and analyze what changes need to be committed:
- Check git status for untracked files and modifications
- Review git diff to understand the changes
- Check recent commit history for commit message style

### Step 2: Git Rebase
Execute git rebase to update the local branch with the latest changes from the remote:
- Perform rebase operation
- Handle any rebase conflicts if they occur
- Ensure the branch is up to date

### Step 3: Stage and Commit
Stage all changes and create an appropriate commit:
- Add all changes to staging area
- Generate a meaningful commit message based on the changes
- Create the commit with proper formatting

### Step 4: Push Changes
Push the committed changes to the remote repository:
- Push the updated branch to remote
- Verify the push was successful

## Current Git Status:
Current git status: !`git status`

## Recent Changes:
Current git diff: !`git diff --staged`
Unstaged changes: !`git diff`

## Recent Commit History:
Recent commits for message style: !`git log --oneline -5`

## Execution Sequence:

1. First, check current git status and changes
2. Execute git rebase to update local branch
3. Stage all changes with `git add .`
4. Commit changes with appropriate message
5. Push changes to remote repository

## Safety Measures
- Always check git status before performing operations
- Handle rebase conflicts gracefully if they occur
- Ensure commit messages follow the repository's style
- Verify push operation completes successfully

Execute the git rebase, commit, and push sequence now.