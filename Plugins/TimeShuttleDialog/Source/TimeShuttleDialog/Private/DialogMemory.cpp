#include "DialogMemory.h"
#include "Kismet/GameplayStatics.h"

void UDialogMemory::SetMemoryEnabled(bool bEnabled) { bMemoryEnabled = bEnabled; }
bool UDialogMemory::HasCompleted(FName Id) const { return bMemoryEnabled && Completed.Contains(Id); }
void UDialogMemory::RememberCompleted(FName Id) { if (bMemoryEnabled && !Id.IsNone()) Completed.Add(Id); }
void UDialogMemory::ResetMemory() { Completed.Reset(); }
bool UDialogMemory::SaveMemory(const FString& SlotName, int32 UserIndex)
{
    if (!bMemoryEnabled || SlotName.IsEmpty() || UserIndex < 0) return false;
    auto* Save = Cast<UDialogMemorySave>(UGameplayStatics::CreateSaveGameObject(UDialogMemorySave::StaticClass()));
    Save->CompletedConversations = Completed;
    return UGameplayStatics::SaveGameToSlot(Save, SlotName + TEXT("_Dialogue"), UserIndex);
}
bool UDialogMemory::LoadMemory(const FString& SlotName, int32 UserIndex)
{
    if (!bMemoryEnabled || SlotName.IsEmpty() || UserIndex < 0) return false;
    // An older/main save may have no dialogue sidecar. Never retain another slot's flags.
    Completed.Reset();
    if (!UGameplayStatics::DoesSaveGameExist(SlotName + TEXT("_Dialogue"), UserIndex)) return true;
    auto* Save = Cast<UDialogMemorySave>(UGameplayStatics::LoadGameFromSlot(SlotName + TEXT("_Dialogue"), UserIndex));
    if (!Save || Save->FormatVersion != 1) return false;
    Completed = Save->CompletedConversations;
    return true;
}
