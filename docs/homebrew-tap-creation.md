# Homebrew Tap Repository Creation

## Quick Start

The `homebrew-open-scribe` Tap repository has been prepared locally at `/tmp/homebrew-open-scribe`.

### Step 1: Create GitHub Repository

Option A: Using GitHub CLI (recommended)
```bash
cd /tmp/homebrew-open-scribe
gh repo create jaesolshin/homebrew-open-scribe \
  --public \
  --description "Homebrew Tap for Open-Scribe" \
  --source=. \
  --remote=origin \
  --push
```

Option B: Create on GitHub.com manually
1. Go to https://github.com/new
2. Repository name: `homebrew-open-scribe`
3. Description: `Homebrew Tap for Open-Scribe`
4. Public
5. Click "Create repository"

Then push locally:
```bash
cd /tmp/homebrew-open-scribe
git remote add origin https://github.com/ysys143/homebrew-open-scribe.git
git branch -M master
git push -u origin master
```

### Step 2: Verify Installation Works

```bash
# Clean environment test
brew tap jaesolshin/homebrew-open-scribe
brew install open-scribe
scribe --help
```

### Step 3: Test with YouTube URL

```bash
scribe "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
# First run will prompt for OpenAI API Key
```

## Repository Structure

```
homebrew-open-scribe/
├── Formula/
│   └── open-scribe.rb     (Copied from open-scribe repo)
├── README.md
└── .gitignore            (optional)
```

## Maintenance

### Adding .gitignore (optional)

```bash
cat > /tmp/homebrew-open-scribe/.gitignore << 'EOF'
.DS_Store
*.swp
*.swo
*~
EOF
```

### Updating Formula for New Versions

When a new version of open-scribe is released:

1. Get the new sha256:
```bash
git archive --format=tar.gz --prefix=open-scribe-X.Y.Z/ \
  --output=/tmp/open-scribe-vX.Y.Z.tar.gz X.Y.Z
shasum -a 256 /tmp/open-scribe-vX.Y.Z.tar.gz
```

2. Update `Formula/open-scribe.rb`:
```ruby
url "https://github.com/ysys143/open-scribe/archive/refs/tags/X.Y.Z.tar.gz"
sha256 "NEW_SHA256_HERE"
```

3. Commit and push:
```bash
git add Formula/open-scribe.rb
git commit -m "Update open-scribe to vX.Y.Z"
git push
```

## User Installation

Once the Tap repository is created and pushed to GitHub:

```bash
brew tap jaesolshin/homebrew-open-scribe
brew install open-scribe
```

That's it! No additional setup needed beyond API key prompt on first run.
