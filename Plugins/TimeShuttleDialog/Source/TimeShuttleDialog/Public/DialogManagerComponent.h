#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "DialogTypes.h"
#include "DialogManagerComponent.generated.h"
class UAudioComponent;
class UDialogWidget;
class UEnhancedInputComponent;
class UEnhancedInputLocalPlayerSubsystem;
class UInputAction;
class UInputMappingContext;
struct FStreamableHandle;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FDialogStarted, FName, ConversationId, UObject*, Source);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FDialogLineEvent, FName, ConversationId, FName, LineId, FName, EventId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FDialogEnded, FName, ConversationId, EDialogEndReason, Reason, UObject*, Source);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FDialogError, FName, ConversationId, const FString&, Message);

UCLASS(Blueprintable, ClassGroup=(Dialogue), meta=(BlueprintSpawnableComponent))
class TIMESHUTTLEDIALOG_API UDialogManagerComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UDialogManagerComponent();
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Dialogue|Setup") TSubclassOf<UDialogWidget> WidgetClass;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Dialogue|Setup") TObjectPtr<UInputMappingContext> DialogueInputContext;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Dialogue|Setup") TObjectPtr<UInputAction> NextAction;
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Dialogue|Setup") TObjectPtr<UInputAction> ToggleAutoAction;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue|Audio", meta=(ClampMin="0", ClampMax="2")) float VoiceVolume = 1.f;
    /** Deliberately false. Enable only when cross-level and explicit-save persistence is wanted. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Dialogue|Memory") bool bEnablePersistentMemory = false;
    UPROPERTY(BlueprintAssignable, Category="Dialogue|Events") FDialogStarted OnConversationStarted;
    UPROPERTY(BlueprintAssignable, Category="Dialogue|Events") FDialogLineEvent OnLineStarted;
    UPROPERTY(BlueprintAssignable, Category="Dialogue|Events") FDialogLineEvent OnLineEnded;
    UPROPERTY(BlueprintAssignable, Category="Dialogue|Events") FDialogEnded OnConversationEnded;
    UPROPERTY(BlueprintAssignable, Category="Dialogue|Events") FDialogError OnDialogueError;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Dialogue|State") EDialogState State = EDialogState::Idle;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Dialogue|State") bool bAutomatic = true;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Dialogue|State") FName ActiveConversationId;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Dialogue|State") int32 CurrentLineIndex = INDEX_NONE;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Dialogue|State") int32 ActivePriority = 3;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Dialogue|State") FString LastError;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Dialogue|State") EDialogEndReason LastEndReason = EDialogEndReason::Completed;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Dialogue|State") int32 CompletedCount = 0;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Dialogue|State") int32 EndedCount = 0;
    UFUNCTION(BlueprintCallable, Category="Dialogue", meta=(RowType="/Script/TimeShuttleDialog.DialogConversationRow"))
    EDialogRequestResult RequestDialogue(FDataTableRowHandle Conversation, EDialogTrigger Trigger, UObject* Source);
    UFUNCTION(BlueprintCallable, Category="Dialogue") void NextLine();
    UFUNCTION(BlueprintCallable, Category="Dialogue") void ToggleAutomatic();
    UFUNCTION(BlueprintCallable, Category="Dialogue") void SetAutomatic(bool bNewAutomatic);
    /** For lifecycle/story cancellation. There is deliberately no player Skip action. */
    UFUNCTION(BlueprintCallable, Category="Dialogue") void CancelDialogue(EDialogEndReason Reason = EDialogEndReason::CancelledByStory);
    UFUNCTION(BlueprintCallable, Category="Dialogue") void NotifyPlayerDied();
    UFUNCTION(BlueprintPure, Category="Dialogue") bool IsDialogueActive() const { return State != EDialogState::Idle; }
    UFUNCTION(BlueprintPure, Category="Dialogue") bool IsControlLocked() const { return IsDialogueActive() && ActiveConversation.bLockPlayerMovement; }
    UFUNCTION(BlueprintPure, Category="Dialogue") bool CanAdvance() const;
    UFUNCTION(BlueprintPure, Category="Dialogue") bool IsDialoguePaused() const;
    UFUNCTION(BlueprintPure, Category="Dialogue") UAudioComponent* GetVoiceComponent() const { return Voice; }
    UFUNCTION(BlueprintPure, Category="Dialogue") UDialogWidget* GetDialogueWidget() const { return Widget; }
    UFUNCTION(BlueprintCallable, Category="Dialogue|Validation") static bool ValidateConversation(FDataTableRowHandle Conversation, FString& Error);
    UFUNCTION(BlueprintPure, Category="Dialogue") static UDialogManagerComponent* FindDialogueManager(AActor* Player);
    /** Insert only before press/trigger paths; release paths must still clean up held controls. */
    UFUNCTION(BlueprintPure, Category="Dialogue") static bool AllowGameplayInput(AActor* Player, FName ActionName);
    UFUNCTION(BlueprintCallable, Category="Dialogue") static void PlayerDied(AActor* Player);
    UFUNCTION(BlueprintCallable, Category="Dialogue|Memory") static bool SavePlayerMemory(AActor* Player, const FString& SlotName, int32 UserIndex, bool bPrimarySaveSucceeded);
    UFUNCTION(BlueprintCallable, Category="Dialogue|Memory") static bool LoadPlayerMemory(AActor* Player, const FString& SlotName, int32 UserIndex);
    /** Implemented by the project adapter to release held fire/aim/interaction on lock entry. */
    UFUNCTION(BlueprintImplementableEvent, Category="Dialogue") void ControlLockChanged(bool bLocked);
protected:
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    virtual void TickComponent(float Delta, ELevelTick Type, FActorComponentTickFunction* Function) override;
private:
    UPROPERTY(Transient) FDialogConversationRow ActiveConversation;
    UPROPERTY(Transient) TArray<FDialogLineRow> Lines;
    UPROPERTY(Transient) TArray<FName> LineIds;
    UPROPERTY(Transient) TArray<TObjectPtr<USoundWave>> LoadedWaves;
    UPROPERTY(Transient) TObjectPtr<UAudioComponent> Voice;
    UPROPERTY(Transient) TObjectPtr<UDialogWidget> Widget;
    UPROPERTY(Transient) TObjectPtr<UEnhancedInputComponent> DialogueInput;
    UPROPERTY(Transient) TWeakObjectPtr<UObject> ActiveSource;
    UPROPERTY(Transient) TWeakObjectPtr<APlayerController> LockedController;
    UPROPERTY(Transient) TWeakObjectPtr<UEnhancedInputLocalPlayerSubsystem> InputSubsystem;
    UPROPERTY(Transient) TSet<FName> LocalCompleted;
    TSharedPtr<FStreamableHandle> LoadHandle;
    uint64 Generation = 0;
    uint64 LineGeneration = 0;
    uint64 LastAdvanceFrame = MAX_uint64;
    bool bTransitioning = false;
    bool bShuttingDown = false;
    bool bOwnMoveLock = false;
    bool bVoiceFinished = false;
    bool bLineAnnounced = false;
    bool bVoicePaused = false;
    bool bWasWorldPaused = false;
    bool bManualAdvanceRequested = false;
    double PreviousRealTime = 0.;
    double LineElapsed = 0.;
    double ReadyElapsed = 0.;
    double LoadingElapsed = 0.;
    APlayerController* PlayerController() const;
    bool InstallPresentation();
    void ReleasePresentation();
    void FinishLoading(uint64 ExpectedGeneration);
    void StartLine();
    void AdvanceInternal();
    void AudioFinished(UAudioComponent* Component, uint64 ExpectedGeneration, uint64 ExpectedLine);
    void StopVoice();
    void Finish(EDialogEndReason Reason);
    void Fail(const FString& Message, EDialogEndReason Reason);
    void UpdateStatus();
};
