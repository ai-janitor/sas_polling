# Docker Customization Guide

## For Agency Deployment

The following files are intended to be customized for your specific environment:

### Files to Customize
- `job-submission/Dockerfile`
- `job-polling/Dockerfile` 
- `gui/Dockerfile`
- `docker-compose.yml`
- `config.dev.env`

### Protection Strategy

After cloning, run these commands to protect your customizations:

```bash
# Protect Docker files from being overwritten
git update-index --skip-worktree job-submission/Dockerfile
git update-index --skip-worktree job-polling/Dockerfile  
git update-index --skip-worktree gui/Dockerfile
git update-index --skip-worktree docker-compose.yml
git update-index --skip-worktree config.dev.env

# Verify protection
git ls-files -v | grep '^S'
```

### To Update Protected Files
If you need to accept upstream changes:

```bash
# Remove protection temporarily
git update-index --no-skip-worktree job-submission/Dockerfile
git pull
# Re-apply your customizations
git update-index --skip-worktree job-submission/Dockerfile
```

### Alternative: Create Local Overrides
Consider creating:
- `docker-compose.override.yml` (automatically loaded by Docker Compose)
- `config.local.env` (load after config.dev.env)