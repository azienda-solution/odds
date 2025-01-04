#!/bin/bash

# Define the trash folder
TRASH_FOLDER="trash"

# Create the trash folder if it doesn't exist
mkdir -p "$TRASH_FOLDER"

# Function to process a file
process_file() {
    local file="$1"
    local line_count
    local creation_date
    local move_date
    local base_name
    local new_name

    # Count the number of lines in the file
    line_count=$(wc -l < "$file")

    # Check if the line count exceeds 200,000
    if (( line_count > 200000 )); then
        # Get the file's creation date
        creation_date=$(stat -c %w "$file" 2>/dev/null || stat -f %B "$file")
        if [[ "$creation_date" == "-" || -z "$creation_date" ]]; then
            creation_date="unknown"
        else
            creation_date=$(date -d @"$creation_date" +%Y-%m-%d)
        fi

        # Get the current move date
        move_date=$(date +%Y-%m-%d)

        # Get the file's base name
        base_name=$(basename "$file")

        # Create the new name for the file
        new_name="${base_name%.txt}_${creation_date}_${move_date}.txt"

        # Move the file to the trash folder with the new name
        mv "$file" "$TRASH_FOLDER/$new_name"
        echo "Moved $file to $TRASH_FOLDER/$new_name"
    else
        echo "$file does not exceed 200,000 lines."
    fi
}

# Loop through all files provided as arguments
for file in "$@"; do
    if [[ -f "$file" ]]; then
        process_file "$file"
    else
        echo "$file is not a valid file."
    fi
done
