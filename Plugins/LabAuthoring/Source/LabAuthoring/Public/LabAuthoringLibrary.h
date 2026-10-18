#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LabAuthoringLibrary.generated.h"

/** Editor preparation only. Never place calls to this library in a runtime Blueprint. */
UCLASS()
class LABAUTHORING_API ULabAuthoringLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Lab Authoring|Editor")
    static FString ApplySpec(const FString& JsonSpec);

    /** Validate all identities and old positions, then edit only positions/comment presentation. Never compile or save. */
    UFUNCTION(BlueprintCallable, Category="Lab Authoring|Editor")
    static FString ApplyGraphPresentation(const FString& JsonPatch);

    UFUNCTION(BlueprintCallable, Category="Lab Authoring|Editor")
    static FString InspectBlueprint(const FString& AssetPath);

    UFUNCTION(BlueprintCallable, Category="Lab Authoring|Editor")
    static FString InspectClass(const FString& ClassPath);
};
