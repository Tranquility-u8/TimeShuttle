#pragma once
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "Sound/SoundWave.h"
#include "DialogTypes.generated.h"

UENUM(BlueprintType)
enum class EDialogTrigger : uint8 { Collision, NPC, Story };
UENUM(BlueprintType)
enum class EDialogState : uint8 { Idle, Loading, PlayingVoice, ReadingText, WaitingForNext };
UENUM(BlueprintType)
enum class EDialogEndReason : uint8 { Completed, InterruptedByPriority, PlayerDied, LevelChanged, CancelledByStory, InvalidData, AudioFailed };
UENUM(BlueprintType)
enum class EDialogRequestResult : uint8 { Accepted, Busy, AlreadyCompleted, InvalidData, PlayerUnavailable, ReentrantRequest };

/** One sentence. The DataTable row name is its stable line ID. */
USTRUCT(BlueprintType)
struct TIMESHUTTLEDIALOG_API FDialogLineRow : public FTableRowBase
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue") FName SpeakerId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue") FText SpeakerName;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue", meta=(MultiLine=true)) FText DialogueText;
    /** Empty is an intentional text-only sentence; an invalid non-empty reference is an error. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue") TSoftObjectPtr<USoundWave> VoiceWave;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Timing", meta=(ClampMin="0.1", Units="s")) float TextOnlyDuration = 3.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Timing", meta=(ClampMin="0.0", Units="s")) float PostLineDelay = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Events") FName LineEventId;
};

/** One complete linear conversation. No player answer branches. */
USTRUCT(BlueprintType)
struct TIMESHUTTLEDIALOG_API FDialogConversationRow : public FTableRowBase
{
    GENERATED_BODY()
    /** Stable authored ID used across level changes and save games. Must be unique. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue") FName ConversationId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue", meta=(RowType="/Script/TimeShuttleDialog.DialogLineRow")) TArray<FDataTableRowHandle> Lines;
    /** 1 is highest. Story requests always have effective priority 1. Equal priority never interrupts. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue", meta=(ClampMin="1", ClampMax="3")) int32 Priority = 3;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue") bool bLockPlayerMovement = false;
    /** Local completion is remembered for the life of the manager. Cross-level/save memory is separately opt-in. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue") bool bPlayOnce = false;
};
