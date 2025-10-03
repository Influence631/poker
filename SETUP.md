# Setup Guide for Poker Learning Game

## Quick Start (Without LLM)

The game works perfectly fine without LLM features. You'll still get:
- Full poker gameplay
- Basic answer evaluation
- Pot odds, outs, and win odds questions

```bash
pip install rich
python main.py
```

## Full Setup (With LLM Features)

For the complete educational experience with AI tutor:

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `rich`: For beautiful terminal UI
- `anthropic`: For LLM-powered evaluation

### 2. Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key

### 3. Set Environment Variable

**Windows (Command Prompt):**
```cmd
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Permanent Setup (Windows):**
1. Search "Environment Variables" in Start Menu
2. Click "Edit system environment variables"
3. Click "Environment Variables" button
4. Under "User variables", click "New"
5. Variable name: `ANTHROPIC_API_KEY`
6. Variable value: Your API key
7. Click OK on all dialogs

**Permanent Setup (Linux/Mac):**
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 4. Run the Game

```bash
python main.py
```

## What You Get With LLM

When ANTHROPIC_API_KEY is set:
- ✅ AI evaluates your reasoning, not just numbers
- ✅ You can explain your thinking (e.g., "5 because opponent has flush")
- ✅ Interactive poker tutor to ask questions
- ✅ Two-stage evaluation (evaluator + judge) for accuracy
- ✅ Detailed feedback on strategic thinking

Without the API key:
- ✅ Game still works normally
- ⚠️ Shows "LLM evaluation not available" message
- ⚠️ Falls back to basic number-only evaluation

## Troubleshooting

### "anthropic module not found"
```bash
pip install anthropic
```

### "ANTHROPIC_API_KEY not set"
Make sure you:
1. Set the environment variable correctly
2. Restart your terminal after setting it
3. Check it's set: `echo %ANTHROPIC_API_KEY%` (Windows) or `echo $ANTHROPIC_API_KEY` (Linux/Mac)

### "LLM evaluation error"
- Check your internet connection
- Verify API key is valid at https://console.anthropic.com/
- Check you have API credits available

## Features Comparison

| Feature | Without LLM | With LLM |
|---------|-------------|----------|
| Poker gameplay | ✅ | ✅ |
| Pot odds questions | ✅ | ✅ |
| Outs counting | ✅ | ✅ |
| Win odds calculation | ✅ | ✅ |
| Equation answers (3+4) | ✅ | ✅ |
| Number-only evaluation | ✅ | ✅ |
| Reasoning evaluation | ❌ | ✅ |
| Strategic feedback | ❌ | ✅ |
| Interactive tutor chat | ❌ | ✅ |
| Opponent hand consideration | ❌ | ✅ |

## Cost

LLM evaluation uses Claude 3.5 Sonnet:
- ~$3 per million input tokens
- ~$15 per million output tokens
- Typical question evaluation: ~500 tokens total
- Cost per evaluation: ~$0.01
- Playing for an hour: ~$0.20-0.50

The game will work perfectly fine without LLM if you prefer!
