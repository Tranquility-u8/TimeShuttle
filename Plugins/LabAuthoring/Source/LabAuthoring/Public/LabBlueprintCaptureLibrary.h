#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LabBlueprintCaptureLibrary.generated.h"

/** Editor-only evidence renderer. It never edits, compiles, or saves the source Blueprint. */
UCLASS()
class LABAUTHORING_API ULabBlueprintCaptureLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /**
     * Render the actual native Slate graph widgets on a transient Blueprint copy.
     * OutputPng must be below this project's Saved directory. Writes a fit overview,
     * optional overlapping 1:1 tiles, and a JSON manifest beside the overview.
     */
    UFUNCTION(BlueprintCallable, Category="Lab Authoring|Editor")
    static FString CaptureBlueprintGraph(const FString& AssetPath, const FString& GraphName,
        const FString& OutputPng, int32 Width = 2400, int32 Height = 1440, bool bIncludeTiles = true);
};
