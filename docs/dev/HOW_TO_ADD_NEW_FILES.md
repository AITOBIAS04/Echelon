# How to Get AI to Scan and Integrate New Files

Instead of copy-pasting code, here's how to have me automatically scan and integrate new files into your project.

## Method 1: Tell Me About New Files

Simply tell me:
- "I've added a new file at `backend/core/situation_room_engine.py` - please scan it and integrate it"
- "Check the `backend/simulation/situation-room/` folder for new files"
- "I've updated `backend/core/mission_generator.py` - review it and update imports"

I'll then:
1. Read the file(s) you mentioned
2. Check for dependencies/imports
3. Update related files as needed
4. Fix any integration issues

## Method 2: Ask Me to Scan a Directory

Say:
- "Scan `backend/simulation/situation-room/` and integrate any new files"
- "Check what files are in `backend/core/` and update imports"
- "Review the `situation-room` folder structure and integrate everything"

I'll:
1. List files in that directory
2. Read relevant files
3. Check for missing imports/dependencies
4. Update the project accordingly

## Method 3: Reference Files in Your Message

You can mention files directly:
- "The `situation_room_engine.py` file needs to be integrated"
- "I've created files in `backend/simulation/situation-room/` - integrate them"

I'll read those files and integrate them.

## Method 4: Ask Me to Find and Integrate

Say:
- "Find all files related to 'situation room' and integrate them"
- "Search for files that import `osint_sources_warroom` and update them"
- "Find any new files in the `backend/` directory that need integration"

I'll search the codebase and integrate automatically.

## Example Workflow

**You:** "I've added a new `SituationRoomEngine` class in `backend/simulation/situation_room_engine.py`. Please scan it and make sure all imports work."

**I will:**
1. Read `backend/simulation/situation_room_engine.py`
2. Check what it imports
3. Check what imports it
4. Update any broken imports
5. Verify integration with existing code

## Best Practices

✅ **DO:**
- Tell me the file path: "Check `backend/core/new_file.py`"
- Mention the directory: "Scan `backend/simulation/situation-room/`"
- Reference by name: "The `situation_room_engine.py` file"
- Ask me to find related files: "Find all files that need to import this"

❌ **DON'T:**
- Copy-paste entire files (unless it's a small snippet)
- Assume I know about new files without telling me
- Manually update imports when I can do it automatically

## What I Can Do Automatically

When you tell me about new files, I can:
- ✅ Read and analyze the file structure
- ✅ Check for missing dependencies
- ✅ Update import statements across the project
- ✅ Fix broken references
- ✅ Create missing files if needed
- ✅ Update related configuration
- ✅ Run lint checks
- ✅ Verify imports work

## Quick Commands

- **"Scan [directory]"** - I'll list and read files in that directory
- **"Integrate [file path]"** - I'll read it and integrate it
- **"Update imports for [file]"** - I'll fix all import references
- **"Find files that need [X]"** - I'll search and update

