#pragma once
#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "DialogMemory.generated.h"

UCLASS()
class TIMESHUTTLEDIALOG_API UDialogMemorySave : public USaveGame
{
    GENERATED_BODY()
public:
    UPROPERTY(SaveGame) int32 FormatVersion = 1;
    UPROPERTY(SaveGame) TSet<FName> CompletedConversations;
};

/** Cross-level memory. Disabled on every fresh game instance until explicitly enabled. Never auto-saves/loads. */
UCLASS()
class TIMESHUTTLEDIALOG_API UDialogMemory : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Dialogue|Memory") void SetMemoryEnabled(bool bEnabled);
    UFUNCTION(BlueprintPure, Category="Dialogue|Memory") bool IsMemoryEnabled() const { return bMemoryEnabled; }
    UFUNCTION(BlueprintPure, Category="Dialogue|Memory") bool HasCompleted(FName ConversationId) const;
    UFUNCTION(BlueprintCallable, Category="Dialogue|Memory") void RememberCompleted(FName ConversationId);
    UFUNCTION(BlueprintCallable, Category="Dialogue|Memory") void ResetMemory();
    /** Explicit save hooks only. Supply the same slot/user used for the desired game profile. */
    UFUNCTION(BlueprintCallable, Category="Dialogue|Memory") bool SaveMemory(const FString& SlotName, int32 UserIndex = 0);
    UFUNCTION(BlueprintCallable, Category="Dialogue|Memory") bool LoadMemory(const FString& SlotName, int32 UserIndex = 0);
private:
    UPROPERTY(Transient) bool bMemoryEnabled = false;
    UPROPERTY(Transient) TSet<FName> Completed;
};
