#include "DialogTriggerActor.h"
#include "DialogManagerComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Pawn.h"

EDialogRequestResult UDialogParticipantComponent::Interact(AActor* Player)
{
    auto* Manager = UDialogManagerComponent::FindDialogueManager(Player);
    return Manager ? Manager->RequestDialogue(Conversation, EDialogTrigger::NPC, GetOwner()) : EDialogRequestResult::PlayerUnavailable;
}
EDialogRequestResult UDialogParticipantComponent::TriggerStory(AActor* Player)
{
    auto* Manager = UDialogManagerComponent::FindDialogueManager(Player);
    return Manager ? Manager->RequestDialogue(Conversation, EDialogTrigger::Story, GetOwner()) : EDialogRequestResult::PlayerUnavailable;
}
ADialogTriggerActor::ADialogTriggerActor()
{
    PrimaryActorTick.bCanEverTick = false;
    TriggerBox = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerBox"));
    SetRootComponent(TriggerBox);
    TriggerBox->SetBoxExtent(FVector(100,100,120));
    TriggerBox->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    TriggerBox->SetCollisionResponseToAllChannels(ECR_Ignore);
    TriggerBox->SetCollisionResponseToChannel(ECC_Pawn,ECR_Overlap);
    TriggerBox->SetGenerateOverlapEvents(true);
}
void ADialogTriggerActor::BeginPlay()
{
    Super::BeginPlay();
    TriggerBox->OnComponentBeginOverlap.AddDynamic(this, &ADialogTriggerActor::Overlap);
}
void ADialogTriggerActor::Overlap(UPrimitiveComponent*, AActor* Other, UPrimitiveComponent*, int32, bool, const FHitResult&)
{
    auto* Pawn = Cast<APawn>(Other);
    if (!bTriggerEnabled || !Pawn || !Pawn->IsPlayerControlled() || !Pawn->IsLocallyControlled()) return;
    auto* Manager = UDialogManagerComponent::FindDialogueManager(Pawn);
    if (Manager) LastRequestResult = Manager->RequestDialogue(Conversation, EDialogTrigger::Collision, this);
}
EDialogRequestResult ADialogTriggerActor::TriggerStory(AActor* Player)
{
    auto* Manager = UDialogManagerComponent::FindDialogueManager(Player);
    LastRequestResult = Manager ? Manager->RequestDialogue(Conversation, EDialogTrigger::Story, this) : EDialogRequestResult::PlayerUnavailable;
    return LastRequestResult;
}
