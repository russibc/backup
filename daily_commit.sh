#!/usr/bin/env bash
set -euo pipefail

repo_root="/home/bioinfo/github"

# Only these two files will be considered
files=(
  "dev_utils/create_py_media_env.sh"
  "dev_utils/docker_utils.sh"
)

state_file="$repo_root/.commit_progress"
date_file="$repo_root/.last_commit_date"
log_file="$repo_root/.commit.log"

[ ! -f "$state_file" ] && echo 0 > "$state_file"
[ ! -f "$date_file" ] && echo "1970-01-01" > "$date_file"

current_index=$(cat "$state_file")
last_date=$(cat "$date_file")
today=$(date +%Y-%m-%d)
now=$(date "+%Y-%m-%d %H:%M:%S")

log() {
  echo "[$now] $1" >> "$log_file"
}

# Prevent multiple commits on the same day
if [ "$last_date" = "$today" ]; then
  log "Commit already performed today ($today)."
  exit 0
fi

# Loop until we find a file to commit
while [ "$current_index" -lt "${#files[@]}" ]; do
  next_file="${files[$current_index]}"
  repo_dir="$repo_root/$(dirname "$next_file")"
  file_name="$(basename "$next_file")"

  cd "$repo_dir"

  # Skip if tracked and unchanged
  if git ls-files --error-unmatch "$file_name" >/dev/null 2>&1; then
    if git diff --quiet "$file_name"; then
      log "$next_file already committed and unchanged, skipping."
      current_index=$((current_index + 1))
      echo "$current_index" > "$state_file"
      continue
    fi
  fi

  # Stage and commit
  git add "$file_name"

  case "$file_name" in
    create_py_media_env.sh) commit_msg="feat: add script to create python media environment" ;;
    docker_utils.sh) commit_msg="feat: add script with docker utilities" ;;
    *) commit_msg="chore: update $next_file" ;;
  esac

  if git commit -m "$commit_msg"; then
    git push
    log "✅ Committed $next_file with message: '$commit_msg'"
    echo $((current_index + 1)) > "$state_file"
    echo "$today" > "$date_file"
    exit 0  # exit after the first successful commit of the day
  else
    log "⚠️ No modifications for $next_file, skipping."
    current_index=$((current_index + 1))
    echo "$current_index" > "$state_file"
    continue
  fi
done

log "All files have already been committed."

