#!/usr/bin/env bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}     Reel Craft Engine - Universal Skill Installer     ${NC}"
echo -e "${BLUE}======================================================${NC}"

# Detect targets
GEMINI_SKILLS_DIR="$HOME/.gemini/config/skills"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
CODEX_SKILLS_DIR="$HOME/.codex/skills"
CURSOR_RULES_DIR="$HOME/.cursor/rules"

SKILL_NAME="reel-craft-engine"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}[*] Installing dependencies via pip...${NC}"
if command -v pip3 &> /dev/null; then
    pip3 install -r "$SOURCE_DIR/requirements.txt" --break-system-packages --quiet 2>/dev/null || pip3 install -r "$SOURCE_DIR/requirements.txt" --quiet
    echo -e "${GREEN}[✓] Python dependencies installed.${NC}"
elif command -v pip &> /dev/null; then
    pip install -r "$SOURCE_DIR/requirements.txt" --break-system-packages --quiet 2>/dev/null || pip install -r "$SOURCE_DIR/requirements.txt" --quiet
    echo -e "${GREEN}[✓] Python dependencies installed.${NC}"
else
    echo -e "${YELLOW}[!] pip not found. Ensure required Python packages are installed.${NC}"
fi

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}[!] Warning: ffmpeg is not installed on system PATH. Please install ffmpeg for video rendering.${NC}"
else
    echo -e "${GREEN}[✓] ffmpeg detected.${NC}"
fi

# Install to Antigravity / Gemini CLI
echo -e "${YELLOW}[*] Deploying to Google Antigravity (~/.gemini/config/skills)...${NC}"
mkdir -p "$GEMINI_SKILLS_DIR"
if [ "$SOURCE_DIR" != "$GEMINI_SKILLS_DIR/$SKILL_NAME" ]; then
    rm -rf "$GEMINI_SKILLS_DIR/$SKILL_NAME"
    cp -r "$SOURCE_DIR" "$GEMINI_SKILLS_DIR/$SKILL_NAME"
fi
echo -e "${GREEN}[✓] Deployed to Antigravity CLI.${NC}"

# Deploy to Claude Code
if [ -d "$HOME/.claude" ] || [ "$1" == "--all" ]; then
    echo -e "${YELLOW}[*] Deploying to Claude Code (~/.claude/skills)...${NC}"
    mkdir -p "$CLAUDE_SKILLS_DIR"
    rm -rf "$CLAUDE_SKILLS_DIR/$SKILL_NAME"
    cp -r "$SOURCE_DIR" "$CLAUDE_SKILLS_DIR/$SKILL_NAME"
    echo -e "${GREEN}[✓] Deployed to Claude Code.${NC}"
fi

# Deploy to Codex / Cursor
if [ -d "$HOME/.cursor" ] || [ "$1" == "--all" ]; then
    echo -e "${YELLOW}[*] Deploying configuration to Cursor...${NC}"
    mkdir -p "$CURSOR_RULES_DIR"
    cp "$SOURCE_DIR/SKILL.md" "$CURSOR_RULES_DIR/reel-craft-engine.md"
    echo -e "${GREEN}[✓] Deployed to Cursor rules.${NC}"
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}🎉 Reel Craft Engine installed successfully!${NC}"
echo -e "You can now invoke this skill in your AI prompts:"
echo -e "${YELLOW}'Use reel-craft-engine to turn audio.mp3 into an ultra_fast reel'${NC}"
echo -e "${BLUE}======================================================${NC}"
