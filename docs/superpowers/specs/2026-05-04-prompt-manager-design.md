# Prompt Manager — Design Spec

## Overview

A desktop app for editing, managing, and bookmarking AI prompts. Built with Python + PySide2, packaged as a compact standalone executable.

## Tech Stack

- **GUI:** PySide2 (Qt for Python, LGPL licensed)
- **Language:** Python 3
- **Storage:** Local JSON files (`prompts_history.json`, `prompts_bookmarks.json`)
- **AI Integration:** DeepSeek API (`deepseek-v4-flash` default model)
- **Packaging:** PyInstaller (minimal bundle, exclude unused Qt modules)

## Layout

Three-column layout (QSplitter with draggable dividers):

```
┌────────────┬──────────────────────────┬──────────────┐
│  History   │       Editor             │  Bookmarks   │
│            │                          │              │
│  Search    │  [Large text area]       │  [tag]       │
│  ────────  │                          │  preview...  │
│  item 1    │                          │  [Copy]      │
│  item 2    │  [Format] [Optimize]     │  ──────────  │
│  item 3    │  [⭐ Bookmark]           │  item 1      │
│            │                          │  item 2      │
└────────────┴──────────────────────────┴──────────────┘
```

- Left panel: ~20% width, search + scrollable history list
- Center panel: ~60% width, editor + action buttons
- Right panel: ~20% width, bookmark list with copy buttons
- All panels resizable via QSplitter

## Data Model

### prompts_history.json

```json
[
  {
    "id": "20260504-143022-a3f2",
    "content": "You are a professional translator...",
    "created_at": "2026-05-04T14:30:22"
  }
]
```

### prompts_bookmarks.json

```json
[
  {
    "id": "bkm-20260504-150530",
    "content": "You are a senior code reviewer...",
    "source_history_id": "20260504-143022-a3f2",
    "tags": ["code", "review"],
    "created_at": "2026-05-04T15:05:30"
  }
]
```

Storage location: `%APPDATA%/prompt-manager/` (resolved at runtime via `os.environ`).

## Features

### Editor (Center Panel)

- QPlainTextEdit with monospace font
- Auto-save to history on focus loss or before AI actions
- Character count in status bar

### AI Actions

- **Format Cleanup (整理格式):** Send current content to DeepSeek with a system prompt instructing it to fix typos, missing punctuation, extra spaces/newlines, and bracket matching. Result replaces editor content. The original content is preserved in history before replacement.
- **Optimize Prompt (优化提示词):** Send current content to DeepSeek with a system prompt instructing it to enhance prompt quality (clarity, structure, specificity). Result replaces editor content. The original content is preserved in history before replacement.
- Both actions show a loading indicator and handle API errors gracefully (show error message, keep original content).

### History Panel (Left)

- Scrollable list showing timestamp + first line preview
- Click an item to load its content into the editor
- Right-click to delete
- Search/filter by keyword

### Bookmarks Panel (Right)

- Scrollable list showing tags + content preview
- Each item has a [Copy] button that copies content to clipboard
- Right-click to remove bookmark
- Adding a bookmark prompts for optional tags (comma-separated)

### Settings Dialog

- DeepSeek API Key (password field with show/hide toggle)
- API Base URL (default: `https://api.deepseek.com`)
- Model selection (default: `deepseek-v4-flash`)
- Test Connection button
- OK/Cancel with validation

## API Integration

- System prompt for format cleanup: "You are a text formatter. Fix the following prompt text: correct typos, add missing punctuation and brackets, remove extra spaces and line breaks. Output ONLY the corrected text, no explanations."
- System prompt for optimization: "You are a prompt engineering expert. Improve the following prompt to make it clearer, more specific, and more effective. Output ONLY the improved prompt, no explanations."
- Timeout: 30 seconds
- Error handling: show error dialog on network failure, API error, or timeout; preserve original text in editor

## Packaging

- PyInstaller with `--onedir` or `--onefile`
- Exclude unused Qt modules (QtWebEngine, QtQml, QtQuick, etc.)
- Only include: QtCore, QtGui, QtWidgets
- Target: < 50MB final package
- Use `--exclude-module` to strip unnecessary standard library modules

## Out of Scope

- Cloud sync
- Multiple users / login
- Markdown rendering
- Import/export (beyond the JSON files themselves)
- Plugin system
