using UnrealBuildTool;
public class LabAuthoring : ModuleRules
{
    public LabAuthoring(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine" });
        PrivateDependencyModuleNames.AddRange(new[] { "UnrealEd", "BlueprintGraph", "Kismet", "KismetCompiler", "Json", "AssetRegistry",
            "GraphEditor", "Slate", "SlateCore", "UMG", "RenderCore", "RHI" });
    }
}
