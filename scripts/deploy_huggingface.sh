#!/bin/bash
# ===========================================
# HuggingFace Spaces Deployment Script
# ===========================================

set -e

echo "🤗 HuggingFace Spaces Deployment"
echo "================================"
echo ""

# Check if huggingface-cli is installed
if ! command -v huggingface-cli &> /dev/null; then
    echo "Installing huggingface_hub..."
    pip install huggingface_hub --quiet
fi

# Get HF username
read -p "Enter your HuggingFace username: " HF_USERNAME
read -p "Enter Space name (default: ai-animal-tracking): " SPACE_NAME
SPACE_NAME=${SPACE_NAME:-ai-animal-tracking}

echo ""
echo "Creating Space: $HF_USERNAME/$SPACE_NAME"
echo ""

# Create temporary directory for deployment
DEPLOY_DIR="/tmp/hf_deploy_$$"
mkdir -p "$DEPLOY_DIR"

# Copy HuggingFace files
cp -r huggingface/* "$DEPLOY_DIR/"
cp yolov8n.pt "$DEPLOY_DIR/" 2>/dev/null || echo "Note: yolov8n.pt will be downloaded on first run"

echo "Files to deploy:"
ls -la "$DEPLOY_DIR"

echo ""
echo "To deploy manually:"
echo "1. Login to HuggingFace: huggingface-cli login"
echo "2. Create a new Space at: https://huggingface.co/new-space"
echo "3. Select 'Docker' as SDK"
echo "4. Upload files from: $DEPLOY_DIR"
echo ""
echo "Or use git:"
echo "  git clone https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"
echo "  cp -r $DEPLOY_DIR/* $SPACE_NAME/"
echo "  cd $SPACE_NAME && git add . && git commit -m 'Deploy' && git push"
echo ""

read -p "Do you want to deploy now? (y/n): " DEPLOY_NOW

if [ "$DEPLOY_NOW" = "y" ]; then
    echo ""
    echo "Logging into HuggingFace..."
    huggingface-cli login
    
    echo ""
    echo "Creating and uploading to Space..."
    huggingface-cli upload-folder "$DEPLOY_DIR" "spaces/$HF_USERNAME/$SPACE_NAME" --repo-type space
    
    echo ""
    echo "✅ Deployment complete!"
    echo "🌐 View your Space at: https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"
fi

# Cleanup
rm -rf "$DEPLOY_DIR"
