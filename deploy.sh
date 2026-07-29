#!/bin/bash
set -e

# Get current script directory (bfmg/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "🔨 Generating Liquid Glass site from Markdown content..."
python3 "$SCRIPT_DIR/generate_liquid_site.py"

echo "🚀 Deploying to Cloudflare Pages (project: bfmg)..."
npx wrangler pages deploy "$SCRIPT_DIR" --project-name=bfmg

echo "✅ Site generated and deployed to Cloudflare Pages successfully!"
