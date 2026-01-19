# Skill System Adapter Sample

This sample shows how to integrate RAG Builder with your existing skill system.

## Files

- `SampleImplementations.cs` - Sample implementations of `IActionInfo`, `ISkillInfo`, and related interfaces
- `SampleActionProvider.cs` - Sample implementation of `IActionProvider` that scans action types
- `SampleSetup.cs` - Example of how to register providers at editor startup

## Usage

### 1. Copy and Modify

Copy these files to your project and modify them to work with your skill system:

```csharp
// In your project's editor code
using RAGBuilder;
using RAGBuilder.Editor;
using UnityEditor;

[InitializeOnLoad]
public static class MyRAGSetup
{
    static MyRAGSetup()
    {
        // Get or create configuration
        var config = RAGBuilderSettingsProvider.GetConfig();
        
        // Create your action provider
        // Replace 'MyBaseActionClass' with your base action type
        var actionProvider = new SampleActionProvider(typeof(MyBaseActionClass));
        
        // Initialize the service
        RAGBuilderService.Instance.Initialize(
            config,
            actionProvider: actionProvider
        );
    }
}
```

### 2. Implement IActionInfo

If the sample implementation doesn't fit your needs, create your own:

```csharp
public class MyActionInfo : IActionInfo
{
    private MyActionType myAction;
    
    public MyActionInfo(MyActionType action)
    {
        myAction = action;
    }
    
    public string TypeName => myAction.GetType().Name;
    public string DisplayName => myAction.DisplayName;
    public string Category => myAction.Category;
    public string Description => myAction.Description;
    public string SearchText => $"{TypeName} {DisplayName} {Description}";
    public IReadOnlyList<IActionParameterInfo> Parameters => ExtractParameters();
    
    private List<IActionParameterInfo> ExtractParameters()
    {
        // Extract parameters from your action type
    }
}
```

### 3. Configure Paths

Make sure to configure the export paths in your `RAGBuilderConfig` to match your project structure.
