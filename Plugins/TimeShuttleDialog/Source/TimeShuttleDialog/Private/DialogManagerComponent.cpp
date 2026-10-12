#include "DialogManagerComponent.h"
#include "DialogMemory.h"
#include "DialogWidget.h"
#include "Components/AudioComponent.h"
#include "Engine/AssetManager.h"
#include "Engine/GameInstance.h"
#include "Engine/LocalPlayer.h"
#include "Engine/StreamableManager.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/ScopeLock.h"
#include "Modules/ModuleManager.h"
#include "UObject/UnrealType.h"

IMPLEMENT_MODULE(FDefaultModuleImpl, TimeShuttleDialog)
DEFINE_LOG_CATEGORY_STATIC(LogDialogSystem, Log, All);

UDialogManagerComponent::UDialogManagerComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    PrimaryComponentTick.bTickEvenWhenPaused = true;
    WidgetClass = UDialogWidget::StaticClass();
}
void UDialogManagerComponent::BeginPlay()
{
    Super::BeginPlay();
    bAutomatic = true;
    // The subsystem starts disabled. A runtime opt-in must survive a Pawn/level change.
    if (bEnablePersistentMemory)
        if (auto* GI = GetWorld()->GetGameInstance()) GI->GetSubsystem<UDialogMemory>()->SetMemoryEnabled(true);
}
void UDialogManagerComponent::EndPlay(const EEndPlayReason::Type Reason)
{
    bShuttingDown = true;
    Finish(EDialogEndReason::LevelChanged);
    Super::EndPlay(Reason);
}
APlayerController* UDialogManagerComponent::PlayerController() const
{
    const auto* Pawn = Cast<APawn>(GetOwner());
    return Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
}
UDialogManagerComponent* UDialogManagerComponent::FindDialogueManager(AActor* Player)
{
    return IsValid(Player) ? Player->FindComponentByClass<UDialogManagerComponent>() : nullptr;
}
bool UDialogManagerComponent::AllowGameplayInput(AActor* Player, FName Action)
{
    auto* Manager = FindDialogueManager(Player);
    if (!Manager || !Manager->IsDialogueActive()) return true;
    if (Action == TEXT("IA_Look") || Action == TEXT("IA_Menu")) return true;
    // Space is reserved for dialogue even in the free-movement variant.
    if (Action == TEXT("IA_Jump")) return false;
    return !Manager->IsControlLocked();
}
void UDialogManagerComponent::PlayerDied(AActor* Player)
{
    if (auto* Manager = FindDialogueManager(Player)) Manager->NotifyPlayerDied();
}
bool UDialogManagerComponent::SavePlayerMemory(AActor* Player, const FString& SlotName, int32 UserIndex, bool bPrimarySaveSucceeded)
{
    if (!IsValid(Player) || !bPrimarySaveSucceeded || !Player->GetGameInstance()) return false;
    return Player->GetGameInstance()->GetSubsystem<UDialogMemory>()->SaveMemory(SlotName, UserIndex);
}
bool UDialogManagerComponent::LoadPlayerMemory(AActor* Player, const FString& SlotName, int32 UserIndex)
{
    if (!IsValid(Player) || !Player->GetGameInstance()) return false;
    if (auto* Manager = FindDialogueManager(Player))
    {
        Manager->CancelDialogue(EDialogEndReason::CancelledByStory);
        // Loading an earlier save starts a new completion history, including local-only once flags.
        Manager->LocalCompleted.Reset();
    }
    return Player->GetGameInstance()->GetSubsystem<UDialogMemory>()->LoadMemory(SlotName, UserIndex);
}
void UDialogManagerComponent::NotifyPlayerDied() { CancelDialogue(EDialogEndReason::PlayerDied); }
bool UDialogManagerComponent::IsDialoguePaused() const { return GetWorld() && UGameplayStatics::IsGamePaused(this); }
bool UDialogManagerComponent::CanAdvance() const
{
    return IsDialogueActive() && !IsDialoguePaused() && State != EDialogState::Loading && bVoiceFinished;
}

bool UDialogManagerComponent::ValidateConversation(FDataTableRowHandle Handle, FString& Error)
{
    Error.Reset();
    if (!Handle.DataTable || Handle.RowName.IsNone() || Handle.DataTable->GetRowStruct() != FDialogConversationRow::StaticStruct())
        { Error = TEXT("Select a valid conversation DataTable and row."); return false; }
    const auto* Conversation = Handle.GetRow<FDialogConversationRow>(TEXT("DialogValidation"));
    if (!Conversation) { Error = TEXT("Conversation row does not exist."); return false; }
    if (Conversation->ConversationId.IsNone()) { Error = TEXT("ConversationId must be a stable, non-empty ID."); return false; }
    if (Conversation->Priority < 1 || Conversation->Priority > 3) { Error = TEXT("Priority must be 1, 2 or 3."); return false; }
    if (Conversation->Lines.IsEmpty()) { Error = TEXT("Conversation has no lines."); return false; }
    for (const auto& Row : Handle.DataTable->GetRowMap())
    {
        if (Row.Key != Handle.RowName && reinterpret_cast<const FDialogConversationRow*>(Row.Value)->ConversationId == Conversation->ConversationId)
            { Error = TEXT("Duplicate ConversationId in conversation table."); return false; }
    }
    for (const auto& LineHandle : Conversation->Lines)
    {
        if (!LineHandle.DataTable || LineHandle.DataTable->GetRowStruct() != FDialogLineRow::StaticStruct())
            { Error = TEXT("A line uses the wrong DataTable row structure."); return false; }
        const auto* Line = LineHandle.GetRow<FDialogLineRow>(TEXT("DialogValidation"));
        if (!Line) { Error = TEXT("Missing line: ") + LineHandle.RowName.ToString(); return false; }
        if (Line->SpeakerName.IsEmpty() || Line->DialogueText.IsEmpty())
            { Error = TEXT("Speaker/text is empty: ") + LineHandle.RowName.ToString(); return false; }
        if (!FMath::IsFinite(Line->TextOnlyDuration) || Line->TextOnlyDuration < .1f || !FMath::IsFinite(Line->PostLineDelay) || Line->PostLineDelay < 0.f)
            { Error = TEXT("Invalid timing: ") + LineHandle.RowName.ToString(); return false; }
    }
    return true;
}

EDialogRequestResult UDialogManagerComponent::RequestDialogue(FDataTableRowHandle Handle, EDialogTrigger Trigger, UObject* Source)
{
    if (bTransitioning || bShuttingDown) return EDialogRequestResult::ReentrantRequest;
    auto* PC = PlayerController();
    if (!PC || !PC->IsLocalController() || IsDialoguePaused()) return EDialogRequestResult::PlayerUnavailable;
    if (const auto* Dead = FindFProperty<FBoolProperty>(GetOwner()->GetClass(), TEXT("IsPlayerDead")))
        if (Dead->GetPropertyValue_InContainer(GetOwner())) return EDialogRequestResult::PlayerUnavailable;
    FString Error;
    if (!ValidateConversation(Handle, Error))
    {
        LastError = Error;
        UE_LOG(LogDialogSystem, Error, TEXT("%s: %s"), *Handle.RowName.ToString(), *Error);
        OnDialogueError.Broadcast(Handle.RowName, Error);
        return EDialogRequestResult::InvalidData;
    }
    const FDialogConversationRow Requested = *Handle.GetRow<FDialogConversationRow>(TEXT("DialogRequest"));
    auto* Memory = GetWorld()->GetGameInstance()->GetSubsystem<UDialogMemory>();
    if (Requested.bPlayOnce && (LocalCompleted.Contains(Requested.ConversationId) || Memory->HasCompleted(Requested.ConversationId)))
        return EDialogRequestResult::AlreadyCompleted;
    const int32 EffectivePriority = Trigger == EDialogTrigger::Story ? 1 : Requested.Priority;
    if (IsDialogueActive() && (EffectivePriority >= ActivePriority || Requested.ConversationId == ActiveConversationId)) return EDialogRequestResult::Busy;
    TGuardValue<bool> Guard(bTransitioning, true);
    if (IsDialogueActive()) Finish(EDialogEndReason::InterruptedByPriority);
    ++Generation;
    ActiveConversation = Requested;
    ActiveConversationId = Requested.ConversationId;
    ActivePriority = EffectivePriority;
    ActiveSource = Source;
    CurrentLineIndex = INDEX_NONE;
    Lines.Reset(); LineIds.Reset(); LoadedWaves.Reset();
    LastError.Reset(); LoadingElapsed = 0.;
    State = EDialogState::Loading;
    PreviousRealTime = FPlatformTime::Seconds();
    bWasWorldPaused = false;
    SetComponentTickEnabled(true);
    for (const auto& Line : Requested.Lines)
    {
        Lines.Add(*Line.GetRow<FDialogLineRow>(TEXT("DialogRequest")));
        LineIds.Add(Line.RowName);
    }
    if (!InstallPresentation()) { Fail(TEXT("Dialogue widget or input setup is missing."), EDialogEndReason::InvalidData); return EDialogRequestResult::InvalidData; }
    OnConversationStarted.Broadcast(ActiveConversationId, ActiveSource.Get());
    TArray<FSoftObjectPath> Paths;
    for (const auto& Line : Lines) if (!Line.VoiceWave.IsNull()) Paths.AddUnique(Line.VoiceWave.ToSoftObjectPath());
    const uint64 Expected = Generation;
    if (Paths.IsEmpty()) FinishLoading(Expected);
    else LoadHandle = UAssetManager::GetStreamableManager().RequestAsyncLoad(Paths, FStreamableDelegate::CreateWeakLambda(this, [this, Expected]() { FinishLoading(Expected); }));
    UpdateStatus();
    return EDialogRequestResult::Accepted;
}
bool UDialogManagerComponent::InstallPresentation()
{
    auto* PC = PlayerController();
    if (!PC || !WidgetClass || !DialogueInputContext || !NextAction || !ToggleAutoAction || !PC->GetLocalPlayer()) return false;
    Widget = CreateWidget<UDialogWidget>(PC, WidgetClass);
    if (!Widget) return false;
    Widget->ShowLine(FDialogLineRow()); // never display designer placeholder text while loading audio
    Widget->AddToPlayerScreen(40);
    auto* Subsystem = PC->GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>();
    if (!Subsystem) return false;
    InputSubsystem = Subsystem;
    // PlayerController also enumerates every Pawn input component. Owning this on the Pawn
    // AND pushing it explicitly would dispatch each action twice (P would toggle back).
    DialogueInput = NewObject<UEnhancedInputComponent>(PC);
    DialogueInput->Priority = 10000;
    DialogueInput->RegisterComponent();
    DialogueInput->BindAction(NextAction, ETriggerEvent::Started, this, &UDialogManagerComponent::NextLine);
    DialogueInput->BindAction(ToggleAutoAction, ETriggerEvent::Started, this, &UDialogManagerComponent::ToggleAutomatic);
    PC->PushInputComponent(DialogueInput);
    FModifyContextOptions Options;
    Options.bIgnoreAllPressedKeysUntilRelease = true;
    Subsystem->AddMappingContext(DialogueInputContext, 10000, Options);
    LockedController = PC;
    if (ActiveConversation.bLockPlayerMovement)
    {
        // Stop project actions before taking our own lock: their teardown may restore input.
        ControlLockChanged(true);
        PC->SetIgnoreMoveInput(true);
        bOwnMoveLock = true;
        if (auto* Character = Cast<ACharacter>(GetOwner()))
        {
            Character->StopJumping();
            Character->GetCharacterMovement()->StopMovementImmediately();
            Character->ConsumeMovementInputVector();
        }
    }
    return true;
}
void UDialogManagerComponent::ReleasePresentation()
{
    if (auto* Subsystem = InputSubsystem.Get()) Subsystem->RemoveMappingContext(DialogueInputContext);
    InputSubsystem.Reset();
    if (auto* PC = LockedController.Get())
    {
        if (DialogueInput) PC->PopInputComponent(DialogueInput);
        if (bOwnMoveLock) PC->SetIgnoreMoveInput(false); // balanced one increment; never ResetIgnoreMoveInput
    }
    const bool WasLocked = bOwnMoveLock;
    bOwnMoveLock = false;
    LockedController.Reset();
    if (DialogueInput) { DialogueInput->DestroyComponent(); DialogueInput = nullptr; }
    if (Widget) { Widget->RemoveFromParent(); Widget = nullptr; }
    if (WasLocked && !bShuttingDown) ControlLockChanged(false);
}
void UDialogManagerComponent::FinishLoading(uint64 Expected)
{
    if (Expected != Generation || State != EDialogState::Loading || bShuttingDown) return;
    LoadedWaves.Reset();
    for (int32 Index = 0; Index < Lines.Num(); ++Index)
    {
        auto* Wave = Lines[Index].VoiceWave.Get();
        if (!Lines[Index].VoiceWave.IsNull() && (!Wave || Wave->bLooping || !FMath::IsFinite(Wave->Duration) || Wave->Duration <= 0.f))
        {
            Fail(TEXT("Missing, looping or invalid SoundWave on line ") + LineIds[Index].ToString(), EDialogEndReason::InvalidData);
            return;
        }
        LoadedWaves.Add(Wave);
    }
    CurrentLineIndex = 0;
    StartLine();
}
void UDialogManagerComponent::StartLine()
{
    if (!Lines.IsValidIndex(CurrentLineIndex)) { Finish(EDialogEndReason::Completed); return; }
    StopVoice();
    ++LineGeneration;
    LineElapsed = 0.; ReadyElapsed = 0.; bManualAdvanceRequested = false;
    const auto& Line = Lines[CurrentLineIndex];
    bVoiceFinished = LoadedWaves[CurrentLineIndex] == nullptr;
    State = bVoiceFinished ? EDialogState::ReadingText : EDialogState::PlayingVoice;
    if (Widget) Widget->ShowLine(Line);
    bLineAnnounced = true;
    const uint64 AnnouncedSession = Generation, AnnouncedSentence = LineGeneration;
    OnLineStarted.Broadcast(ActiveConversationId, LineIds[CurrentLineIndex], Line.LineEventId);
    if (!IsDialogueActive() || Generation != AnnouncedSession || LineGeneration != AnnouncedSentence) return;
    if (!bVoiceFinished)
    {
        Voice = NewObject<UAudioComponent>(GetOwner());
        Voice->bAutoActivate = false;
        Voice->bAutoDestroy = false;
        Voice->bAllowSpatialization = false;
        // UI class ignores world time pitch. Pause is explicitly mirrored below.
        Voice->bIsUISound = true;
        Voice->bAlwaysPlay = true;
        Voice->SetVolumeMultiplier(VoiceVolume);
        Voice->SetPitchMultiplier(1.f);
        Voice->SetSound(LoadedWaves[CurrentLineIndex]);
        Voice->RegisterComponent();
        const uint64 Session = Generation, Sentence = LineGeneration;
        Voice->OnAudioFinishedNative.AddWeakLambda(this, [this, Session, Sentence](UAudioComponent* Component) { AudioFinished(Component, Session, Sentence); });
        Voice->Play();
        bVoicePaused = IsDialoguePaused();
        Voice->SetPaused(bVoicePaused);
    }
    UpdateStatus();
}
void UDialogManagerComponent::AudioFinished(UAudioComponent* Component, uint64 Session, uint64 Sentence)
{
    if (Session != Generation || Sentence != LineGeneration || Component != Voice || State != EDialogState::PlayingVoice) return;
    bVoiceFinished = true;
    ReadyElapsed = 0.;
    State = EDialogState::WaitingForNext;
    UpdateStatus(); // advancement occurs once on a later tick, never inside the audio callback
}
void UDialogManagerComponent::StopVoice()
{
    ++LineGeneration;
    if (Voice)
    {
        Voice->OnAudioFinishedNative.Clear();
        Voice->Stop();
        Voice->DestroyComponent();
        Voice = nullptr;
    }
    bVoicePaused = false;
}
void UDialogManagerComponent::NextLine()
{
    if (bAutomatic || bTransitioning || !CanAdvance() || LastAdvanceFrame == GFrameCounter) return;
    // One request per frame, including two physical keys pressed together.
    LastAdvanceFrame = GFrameCounter;
    bManualAdvanceRequested = true;
}
void UDialogManagerComponent::ToggleAutomatic() { SetAutomatic(!bAutomatic); }
void UDialogManagerComponent::SetAutomatic(bool bNewAutomatic)
{
    if (IsDialoguePaused() || bTransitioning) return;
    bAutomatic = bNewAutomatic;
    bManualAdvanceRequested = false;
    UpdateStatus();
}
void UDialogManagerComponent::TickComponent(float Delta, ELevelTick Type, FActorComponentTickFunction* Function)
{
    Super::TickComponent(Delta, Type, Function);
    const double Now = FPlatformTime::Seconds();
    const double Elapsed = FMath::Max(0., Now - PreviousRealTime);
    PreviousRealTime = Now;
    if (!IsDialogueActive()) return;
    if (!PlayerController()) { Finish(EDialogEndReason::CancelledByStory); return; }
    const bool Paused = IsDialoguePaused();
    if (Voice && Paused != bVoicePaused) { Voice->SetPaused(Paused); bVoicePaused = Paused; }
    if (Paused != bWasWorldPaused) { bWasWorldPaused = Paused; UpdateStatus(); }
    if (Paused) { bManualAdvanceRequested = false; return; }
    if (State == EDialogState::Loading)
    {
        LoadingElapsed += Elapsed;
        if (LoadingElapsed > 30.) Fail(TEXT("Dialogue voice loading timed out."), EDialogEndReason::InvalidData);
        return;
    }
    LineElapsed += Elapsed;
    if (bVoiceFinished) ReadyElapsed += Elapsed;
    if (State == EDialogState::PlayingVoice && LoadedWaves.IsValidIndex(CurrentLineIndex) && LoadedWaves[CurrentLineIndex] && LineElapsed > LoadedWaves[CurrentLineIndex]->Duration + 10.)
        { Fail(TEXT("Audio did not report completion; cancelled without advancing."), EDialogEndReason::AudioFailed); return; }
    if (!Lines.IsValidIndex(CurrentLineIndex)) { Fail(TEXT("Invalid active line index."), EDialogEndReason::InvalidData); return; }
    const auto& Line = Lines[CurrentLineIndex];
    const bool TextReady = LoadedWaves[CurrentLineIndex] || LineElapsed >= Line.TextOnlyDuration;
    const bool GapReady = LoadedWaves[CurrentLineIndex] ? ReadyElapsed >= Line.PostLineDelay : LineElapsed >= Line.TextOnlyDuration + Line.PostLineDelay;
    if (bManualAdvanceRequested || (bAutomatic && bVoiceFinished && TextReady && GapReady)) AdvanceInternal();
}
void UDialogManagerComponent::AdvanceInternal()
{
    if (bTransitioning || !CanAdvance()) return;
    TGuardValue<bool> Guard(bTransitioning, true);
    bManualAdvanceRequested = false;
    if (bLineAnnounced)
    {
        bLineAnnounced = false;
        OnLineEnded.Broadcast(ActiveConversationId, LineIds[CurrentLineIndex], Lines[CurrentLineIndex].LineEventId);
    }
    ++CurrentLineIndex;
    if (CurrentLineIndex >= Lines.Num()) Finish(EDialogEndReason::Completed);
    else StartLine();
}
void UDialogManagerComponent::CancelDialogue(EDialogEndReason Reason)
{
    if (bTransitioning || Reason == EDialogEndReason::Completed) return;
    Finish(Reason);
}
void UDialogManagerComponent::Finish(EDialogEndReason Reason)
{
    if (!IsDialogueActive()) return;
    TGuardValue<bool> Guard(bTransitioning, true);
    const FName FinishedId = ActiveConversationId;
    UObject* Source = ActiveSource.Get();
    ++Generation;
    if (LoadHandle) { LoadHandle->CancelHandle(); LoadHandle.Reset(); }
    StopVoice();
    // Clear active state before outward callbacks so teardown cannot restart the old sentence.
    State = EDialogState::Idle;
    bLineAnnounced = false;
    bManualAdvanceRequested = false;
    bVoiceFinished = false;
    LastEndReason = Reason;
    ++EndedCount;
    if (Reason == EDialogEndReason::Completed)
    {
        ++CompletedCount;
        if (ActiveConversation.bPlayOnce)
        {
            LocalCompleted.Add(FinishedId);
            if (auto* GI = GetWorld()->GetGameInstance()) GI->GetSubsystem<UDialogMemory>()->RememberCompleted(FinishedId);
        }
    }
    ReleasePresentation();
    ActiveConversationId = NAME_None;
    CurrentLineIndex = INDEX_NONE;
    Lines.Reset(); LineIds.Reset(); LoadedWaves.Reset();
    ActiveSource.Reset();
    SetComponentTickEnabled(false);
    UE_LOG(LogDialogSystem, Log, TEXT("Ended %s (%d)"), *FinishedId.ToString(), static_cast<int32>(Reason));
    OnConversationEnded.Broadcast(FinishedId, Reason, Source);
}
void UDialogManagerComponent::Fail(const FString& Message, EDialogEndReason Reason)
{
    LastError = Message;
    const FName Id = ActiveConversationId;
    UE_LOG(LogDialogSystem, Error, TEXT("%s: %s"), *Id.ToString(), *Message);
    Finish(Reason);
    OnDialogueError.Broadcast(Id, Message);
}
void UDialogManagerComponent::UpdateStatus()
{
    if (Widget) Widget->ShowStatus(bAutomatic, CanAdvance(), IsDialoguePaused(), State == EDialogState::Loading);
}
