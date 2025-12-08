#!/bin/bash

# Script to rename all files and folders by replacing spaces with hyphens
# Usage: ./rename-spaces.sh <directory>

TARGET_DIR="$1"

if [ -z "$TARGET_DIR" ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

cd "$TARGET_DIR" || exit 1

# First rename files (depth-first to avoid issues with nested directories)
find . -depth -name "* *" | while read -r file; do
    dir=$(dirname "$file")
    base=$(basename "$file")
    new_name=$(echo "$base" | sed 's/ /-/g')

    if [ "$base" != "$new_name" ]; then
        mv "$dir/$base" "$dir/$new_name"
        echo "Renamed: $file -> $dir/$new_name"
    fi
done

echo "Done!"
