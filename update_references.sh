#!/bin/bash
set -e

# --- Configuration ---
ADK_PYTHON_REPO="https://github.com/google/adk-python.git"
ADK_SAMPLES_REPO="https://github.com/google/adk-samples.git"
ADK_SAMPLES_SUBDIR="python"

# --- Function to update adk-python (Full Repo) ---
update_adk_python() {
    DIR_NAME="adk-python"
    echo "🔄 Updating $DIR_NAME from $ADK_PYTHON_REPO..."

    if [ -d "$DIR_NAME" ]; then
        echo "   Removing existing $DIR_NAME..."
        rm -rf "$DIR_NAME"
    fi

    # Shallow clone
    git clone --depth 1 "$ADK_PYTHON_REPO" "$DIR_NAME"

    # Remove .git to detach from version control
    rm -rf "$DIR_NAME/.git"
    
    echo "✅ $DIR_NAME updated."
}

# --- Function to update adk-samples (Subdirectory only) ---
update_adk_samples() {
    DIR_NAME="adk-samples"
    TEMP_DIR="adk-samples-temp"
    
    echo "🔄 Updating $DIR_NAME (subdirectory: $ADK_SAMPLES_SUBDIR) from $ADK_SAMPLES_REPO..."

    if [ -d "$DIR_NAME" ]; then
        echo "   Removing existing $DIR_NAME..."
        rm -rf "$DIR_NAME"
    fi
    
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi

    # Sparse clone to minimize download
    echo "   Fetching specific folder..."
    git clone --depth 1 --filter=blob:none --sparse "$ADK_SAMPLES_REPO" "$TEMP_DIR"
    
    # Configure sparse checkout to only populate the python directory
    pushd "$TEMP_DIR" > /dev/null
    git sparse-checkout set "$ADK_SAMPLES_SUBDIR"
    popd > /dev/null

    # Move the content of the specific subdirectory to be the main adk-samples dir
    mv "$TEMP_DIR/$ADK_SAMPLES_SUBDIR" "$DIR_NAME"

    # Cleanup temp directory
    rm -rf "$TEMP_DIR"
    
    echo "✅ $DIR_NAME updated."
}

# --- Execution ---
echo "🚀 Starting reference update..."
update_adk_python
update_adk_samples
echo "✨ All references updated successfully!"
