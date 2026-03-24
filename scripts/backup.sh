#!/usr/bin/env bash
# Coinnect backup script — copies production data from ash + pushes git to all remotes
# Run: ./scripts/backup.sh
# Cron: 0 2 * * * /home/inge/coinnect/scripts/backup.sh >> /home/inge/coinnect/backups/backup.log 2>&1

set -euo pipefail

BACKUP_DIR="/home/inge/coinnect/backups"
ASH="ash"  # uses ~/.ssh/config host alias
DATE=$(date +%Y-%m-%d)
KEEP_DAYS=7

echo "=== Coinnect backup — $DATE $(date +%H:%M:%S) ==="

# 1. SQLite databases from ash
echo "[1/4] Copying databases from ash..."
mkdir -p "$BACKUP_DIR/$DATE"
for db in history.db; do
    scp -q "$ASH:/home/inge/coinnect/data/$db" "$BACKUP_DIR/$DATE/$db" 2>/dev/null && \
        echo "  ✓ $db" || echo "  ✗ $db (not found or failed)"
done

# 2. .env from ash (contains secrets — keep local only)
echo "[2/4] Copying .env from ash..."
scp -q "$ASH:/home/inge/coinnect/.env" "$BACKUP_DIR/$DATE/dot-env" 2>/dev/null && \
    echo "  ✓ .env" || echo "  ✗ .env (failed)"

# 3. Push git to all remotes
echo "[3/4] Pushing git to remotes..."
cd /home/inge/coinnect
for remote in $(git remote); do
    git push "$remote" main 2>/dev/null && \
        echo "  ✓ pushed to $remote" || echo "  ✗ failed to push to $remote"
done

# 4. Rotate old backups
echo "[4/4] Rotating backups (keeping $KEEP_DAYS days)..."
find "$BACKUP_DIR" -maxdepth 1 -type d -name "20*" -mtime +$KEEP_DAYS -exec rm -rf {} \; 2>/dev/null
REMAINING=$(find "$BACKUP_DIR" -maxdepth 1 -type d -name "20*" | wc -l)
echo "  $REMAINING backup(s) retained"

echo "=== Backup complete ==="
