using UnrealBuildTool;

public class TimeShuttleDebugMenu : ModuleRules
{
	public TimeShuttleDebugMenu(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PrivateDependencyModuleNames.AddRange(new[]
		{
			"Core", "CoreUObject", "Engine", "InputCore", "Slate", "SlateCore"
		});
	}
}
