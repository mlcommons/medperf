# This script should be run from the medperf too directory, ie the parent directory to where this file is
# sh tutorials_scripts/tutorials_cleanup.sh

# Remove medperf_tutorial directory created by tutorials
echo "Removing medperf_tutorial directory from tutorials..."
rm -rf medperf_tutorial

# Cleanup local server database
echo "Reseting local server database..."
cd server
sh reset_db.sh

# Clean up test storage

echo "Removing local storage from tutorials..."
for dir in ~/.medperf/*
do
    if [ -d "$dir" ]
        then
            rm -rf "$dir"/localhost_8000
        fi
done

# Also delete demo directory
rm -rf ~/.medperf/demo