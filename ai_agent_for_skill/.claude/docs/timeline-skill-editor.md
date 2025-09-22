# Timeline-Based Skill Editor System

## Overview

A Unity-based timeline skill editor system that uses Odin SerializationUtility for JSON serialization/deserialization. The system provides a visual timeline editor for creating complex skill sequences and a runtime player for executing them.

## System Architecture

### Core Components

1. **Data Layer** (`SkillSystem.Data`)
   - `SkillData`: Main skill container with tracks and metadata
   - `SkillTrack`: Individual track containing a list of actions
   - `SkillDataSerializer`: JSON serialization utility using Odin

2. **Actions Layer** (`SkillSystem.Actions`)
   - `ISkillAction`: Base abstract class for all skill actions
   - `LogAction`: Debug logging action
   - `CollisionAction`: Physics collision detection action
   - `AnimationAction`: Animation playback action

3. **Editor Layer** (`SkillSystem.Editor`)
   - `SkillEditorWindow`: Timeline-based visual editor window

4. **Runtime Layer** (`SkillSystem.Runtime`)
   - `SkillPlayer`: Runtime execution engine
   - `SkillPlayerController`: Helper component for testing and control

## Key Features

### ✅ Timeline Editor
- Visual timeline interface with drag-and-drop actions
- Multiple tracks support with individual colors and settings
- Frame-based timeline with configurable frame rate
- Real-time playback preview
- Context menu for adding different action types
- Inspector panel for editing selected actions/tracks

### ✅ JSON Serialization
- Complete serialization using Odin SerializationUtility
- No separate storage - everything serialized to JSON
- Load/Save functionality with file browser integration
- Human-readable JSON format for easy debugging

### ✅ Action System
- Extensible action framework
- Frame-based timing with duration support
- Multiple action types:
  - **LogAction**: Debug message output
  - **CollisionAction**: Physics-based collision detection
  - **AnimationAction**: Animation clip playback
- Easy to extend with new action types

### ✅ Runtime Execution
- Data-driven skill playback
- Event system for skill lifecycle
- Frame-accurate execution
- Looping and pause/resume support
- Active action tracking

## Usage Guide

### Opening the Skill Editor

1. In Unity, go to `Tools > Skill Editor`
2. The timeline editor window will open
3. Use the toolbar to create, load, and save skills

### Creating a Skill

1. Click "New" to create a new skill
2. Configure skill properties in the inspector:
   - Skill name and description
   - Total duration (frames)
   - Frame rate (FPS)

### Working with Tracks

1. Each skill can have multiple tracks
2. Click "Add Track" to create new tracks
3. Configure track properties:
   - Track name
   - Track color
   - Enabled/disabled state
4. Delete tracks using the "X" button

### Adding Actions

1. Right-click in the timeline area to open context menu
2. Select action type to add
3. Actions will be created at the clicked frame position
4. Drag actions to reposition them
5. Select actions to edit properties in the inspector

### Playback Controls

- **Play/Stop**: Control skill playback in editor
- **Frame Scrubbing**: Click timeline to jump to specific frames
- **Timeline Navigation**: Scroll and zoom through the timeline

### Runtime Usage

1. Add `SkillPlayer` component to a GameObject
2. Load skills via code:
   ```csharp
   skillPlayer.LoadAndPlaySkill("path/to/skill.json");
   ```
3. Or use `SkillPlayerController` for testing with UI controls

## Code Examples

### Creating Actions Programmatically

```csharp
// Create a log action
var logAction = new LogAction();
logAction.frame = 10;
logAction.message = "Skill started!";
logAction.duration = 1;

// Create a collision action
var collisionAction = new CollisionAction();
collisionAction.frame = 30;
collisionAction.position = Vector3.forward * 2f;
collisionAction.damage = 25f;
collisionAction.duration = 5;
```

### Loading and Playing Skills

```csharp
// Load from file
skillPlayer.LoadSkill("Assets/Skills/MySkill.json");
skillPlayer.PlaySkill();

// Load from JSON string
string jsonData = "..."; // JSON skill data
skillPlayer.LoadSkillFromJson(jsonData);
skillPlayer.PlaySkill();
```

### Extending with Custom Actions

```csharp
[System.Serializable]
public class CustomAction : ISkillAction
{
    [SerializeField] public float customValue = 1.0f;

    public override string GetActionName()
    {
        return "Custom Action";
    }

    public override void Execute()
    {
        // Custom action logic here
        Debug.Log($"Executing custom action with value: {customValue}");
    }

    public override void OnGUI(float trackWidth, float trackHeight)
    {
        var rect = new Rect(0, 0, trackWidth, trackHeight);
        GUI.Box(rect, $"Custom: {customValue}");
    }
}
```

## File Structure

```
Assets/Scripts/SkillSystem/
├── Actions/
│   ├── ISkillAction.cs           # Base action class
│   ├── LogAction.cs              # Debug logging action
│   ├── CollisionAction.cs        # Physics collision action
│   └── AnimationAction.cs        # Animation playback action
├── Data/
│   ├── SkillData.cs              # Main skill data container
│   ├── SkillTrack.cs             # Track data structure
│   └── SkillDataSerializer.cs    # JSON serialization utility
├── Editor/
│   └── SkillEditorWindow.cs      # Timeline editor window
└── Runtime/
    ├── SkillPlayer.cs            # Runtime skill execution
    └── SkillPlayerController.cs  # Testing and control helper
```

## Technical Implementation

### JSON Serialization
- Uses Odin's `SerializationUtility` with `DataFormat.JSON`
- All data structures inherit from `SerializedScriptableObject` or use `[OdinSerialize]`
- Polymorphic action serialization using `[SerializeReference]`

### Timeline Rendering
- Custom editor GUI using Unity's IMGUI system
- Frame-based timeline with configurable width per frame
- Drag-and-drop action positioning
- Real-time playhead visualization

### Runtime Execution
- Frame-based timing system with configurable frame rates
- Action lifecycle management (Initialize → Execute → Update → Cleanup)
- Event-driven architecture for skill lifecycle notifications

## Future Enhancements

- [ ] Bezier curve interpolation for smooth action transitions
- [ ] Group/folder organization for tracks
- [ ] Copy/paste actions between tracks
- [ ] Undo/redo system
- [ ] Timeline zoom and pan controls
- [ ] Action templates and presets
- [ ] Multi-selection and bulk editing
- [ ] Timeline markers and annotations
- [ ] Asset references validation
- [ ] Performance profiling tools

## Dependencies

- Unity 2019.4+ (LTS recommended)
- Odin Inspector & Serializer
- Standard Unity packages (Physics, Animation)

## Testing

The system includes a `SkillPlayerController` component with:
- Visual debug GUI showing playback state
- Keyboard controls for play/pause/stop
- Test skill creation functionality
- Runtime event logging

Use the context menu functions to create and test sample skills.