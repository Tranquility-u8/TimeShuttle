#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Components/ActorComponent.h"
#include "DialogTypes.h"
#include "DialogTriggerActor.generated.h"
class UBoxComponent;
class UDialogManagerComponent;

/** Reusable participant for NPC interaction and explicit story calls. Leaving its area never cancels. */
UCLASS(Blueprintable, ClassGroup=(Dialogue), meta=(BlueprintSpawnableComponent))
class TIMESHUTTLEDIALOG_API UDialogParticipantComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue", meta=(RowType="/Script/TimeShuttleDialog.DialogConversationRow")) FDataTableRowHandle Conversation;
    UFUNCTION(BlueprintCallable, Category="Dialogue") EDialogRequestResult Interact(AActor* Player);
    UFUNCTION(BlueprintCallable, Category="Dialogue") EDialogRequestResult TriggerStory(AActor* Player);
};

UCLASS(Blueprintable)
class TIMESHUTTLEDIALOG_API ADialogTriggerActor : public AActor
{
    GENERATED_BODY()
public:
    ADialogTriggerActor();
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Dialogue") TObjectPtr<UBoxComponent> TriggerBox;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue", meta=(RowType="/Script/TimeShuttleDialog.DialogConversationRow")) FDataTableRowHandle Conversation;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue") bool bTriggerEnabled = true;
    UPROPERTY(VisibleInstanceOnly, BlueprintReadOnly, Category="Dialogue") EDialogRequestResult LastRequestResult = EDialogRequestResult::InvalidData;
    /** Explicitly callable for story sequences, with effective priority 1. */
    UFUNCTION(BlueprintCallable, Category="Dialogue") EDialogRequestResult TriggerStory(AActor* Player);
protected:
    virtual void BeginPlay() override;
    UFUNCTION() void Overlap(UPrimitiveComponent* Component, AActor* Other, UPrimitiveComponent* OtherComponent, int32 BodyIndex, bool bFromSweep, const FHitResult& Sweep);
};
