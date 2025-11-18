#!/bin/bash
# Sync main branch from development, excluding test files
# Usage: bash scripts/sync_main_branch.sh

set -e

echo "[*] Syncing main branch from development..."
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "[-] Error: Not in a git repository"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "[*] Current branch: $CURRENT_BRANCH"

# Switch to development branch
echo "[*] Switching to development branch..."
git checkout development 2>/dev/null || {
    echo "[-] Error: development branch does not exist"
    echo "[*] Creating development branch from current branch..."
    git checkout -b development
}

# Pull latest changes from development remote
if git remote | grep -q origin-dev; then
    echo "[*] Pulling latest changes from origin-dev/development..."
    git pull origin-dev development 2>/dev/null || echo "[!] No remote changes or remote not configured"
fi

# Create or switch to main branch
echo "[*] Creating/updating main branch..."
if git show-ref --verify --quiet refs/heads/main; then
    echo "[*] Main branch exists, switching to it..."
    git checkout main
    echo "[*] Merging development into main..."
    git merge development --no-edit --no-ff
else
    echo "[*] Main branch does not exist, creating from development..."
    git checkout -b main
fi

# Remove development-only files from main
echo ""
echo "[*] Removing development-only files from main branch..."

# List of files/directories to remove for production
REMOVE_FILES=(
    "tests/"
    "scripts/"
    "docs/"
    "GUIDE/"
    "examples/"
    "pytest.ini"
    "tests/README.md"
    ".cursor/"
)

REMOVED_ANY=false

for item in "${REMOVE_FILES[@]}"; do
    if [ -e "$item" ] || [ -d "$item" ]; then
        echo "  [-] Removing: $item"
        rm -rf "$item"
        REMOVED_ANY=true
    fi
done

# Remove plan files
find . -name "*.plan.md" -type f -not -path "./.git/*" | while read -r file; do
    echo "  [-] Removing: $file"
    rm -f "$file"
    REMOVED_ANY=true
done

# Stage all changes
git add -A

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo ""
    echo "[+] No changes to commit (files already removed)"
else
    echo ""
    echo "[*] Committing changes..."
    git commit -m "chore: remove development files for production release

- Removed tests/ directory
- Removed scripts/ directory  
- Removed docs/ directory
- Removed GUIDE/ directory
- Removed examples/ directory
- Removed pytest.ini
- Removed test documentation
- Removed planning documents"
    echo "[+] Changes committed"
fi

echo ""
echo "[+] Main branch synced and cleaned"
echo "[*] Current branch: $(git branch --show-current)"
echo ""
echo "[*] Next steps:"
echo "    1. Review changes: git log --oneline -5"
echo "    2. Push to production remote: git push origin-prod main"
echo "    3. Push tags (if any): git push origin-prod --tags"
echo "    4. Switch back to development: git checkout development"

