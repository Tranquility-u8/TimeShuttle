#include "StoryJump.h"

#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Algo/AllOf.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "Components/CapsuleComponent.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/PackageName.h"
#include "Misc/Parse.h"
#include "UObject/StructOnScope.h"
#include "UObject/UnrealType.h"

DEFINE_LOG_CATEGORY_STATIC(LogStoryJump, Log, All);

namespace
{
constexpr TCHAR ConfigSection[] = TEXT("TimeShuttle.StoryJump");
constexpr TCHAR TravelOption[] = TEXT("TSStoryJump");

FString Field(const FString& Row, const TCHAR* Name)
{
	FString Value;
	FParse::Value(*Row, Name, Value);
	return Value;
}

template <typename T>
const T* Property(const UObject& Object, FName Name)
{
	return FindFProperty<T>(Object.GetClass(), Name);
}

bool Flag(const UObject& Object, FName Name)
{
	const FBoolProperty* Field = Property<FBoolProperty>(Object, Name);
	return Field && Field->GetPropertyValue_InContainer(&Object);
}

bool SetFlag(UObject& Object, FName Name, bool Value)
{
	const FBoolProperty* Field = Property<FBoolProperty>(Object, Name);
	if (!Field)
	{
		return false;
	}
	Field->SetPropertyValue_InContainer(&Object, Value);
	return true;
}

bool SetName(UObject& Object, FName Name, FName Value)
{
	const FNameProperty* Field = Property<FNameProperty>(Object, Name);
	if (!Field)
	{
		return false;
	}
	Field->SetPropertyValue_InContainer(&Object, Value);
	return true;
}

UObject* ObjectField(const UObject& Object, FName Name)
{
	const FObjectPropertyBase* Field = Property<FObjectPropertyBase>(Object, Name);
	return Field ? Field->GetObjectPropertyValue_InContainer(&Object) : nullptr;
}

bool Call(UObject& Object, FName Name)
{
	UFunction* Function = Object.FindFunction(Name);
	if (!Function)
	{
		return false;
	}

	const FProperty* Return = Function->GetReturnProperty();
	if (Function->NumParms != (Return ? 1 : 0) || (Return && !CastField<FBoolProperty>(Return)))
	{
		return false;
	}

	FStructOnScope Params(Function);
	Object.ProcessEvent(Function, Params.GetStructMemory());
	const FBoolProperty* Result = CastField<FBoolProperty>(Return);
	return !Result || Result->GetPropertyValue_InContainer(Params.GetStructMemory());
}

void FocusPickup(AActor& Pickup)
{
	UFunction* Function = Pickup.FindFunction(TEXT("Interface_ToggleFocus"));
	if (Function && Function->NumParms == 1 && !Function->GetReturnProperty())
	{
		const FBoolProperty* Focused = CastField<FBoolProperty>(Function->ChildProperties);
		if (Focused && Focused->HasAnyPropertyFlags(CPF_Parm) && !Focused->HasAnyPropertyFlags(CPF_OutParm))
		{
			FStructOnScope Params(Function);
			Focused->SetPropertyValue_InContainer(Params.GetStructMemory(), true);
			Pickup.ProcessEvent(Function, Params.GetStructMemory());
		}
	}
}

bool EquipFromSlot(ACharacter& Player, const FString& Slot)
{
	UFunction* Swap = Player.FindFunction(TEXT("SwapWeapon"));
	if (!Swap)
	{
		return false;
	}
	const FProperty* Argument = FindFProperty<FProperty>(Swap, TEXT("NextWeapon"));
	const FEnumProperty* EnumProperty = CastField<FEnumProperty>(Argument);
	const FByteProperty* ByteProperty = CastField<FByteProperty>(Argument);
	const UEnum* Enum = EnumProperty ? EnumProperty->GetEnum() : ByteProperty ? ByteProperty->Enum.Get() : nullptr;
	if (!Enum)
	{
		return false;
	}
	const int64 Value = Enum->GetValueByNameString(Slot, EGetByNameFlags::CheckAuthoredName);
	if (Value == INDEX_NONE)
	{
		return false;
	}
	FStructOnScope Params(Swap);
	const FNumericProperty* Storage = EnumProperty ? EnumProperty->GetUnderlyingProperty() : ByteProperty;
	Storage->SetIntPropertyValue(Argument->ContainerPtrToValuePtr<void>(Params.GetStructMemory()), Value);
	Player.ProcessEvent(Swap, Params.GetStructMemory());
	return true;
}

AActor* FindRole(const AActor& Flow, FName Role)
{
	const FMapProperty* Roles = Property<FMapProperty>(Flow, TEXT("Roles"));
	if (!Roles || !CastField<FNameProperty>(Roles->KeyProp))
	{
		return Cast<AActor>(ObjectField(Flow, Role));
	}
	const FObjectPropertyBase* ActorProperty = CastField<FObjectPropertyBase>(Roles->ValueProp);
	if (!ActorProperty)
	{
		return nullptr;
	}

	FScriptMapHelper Map(Roles, Roles->ContainerPtrToValuePtr<void>(&Flow));
	const uint8* Value = Map.FindValueFromHash(&Role);
	return Value ? Cast<AActor>(ActorProperty->GetObjectPropertyValue(Value)) : Cast<AActor>(ObjectField(Flow, Role));
}

bool PlaceAtRole(AActor& Flow, ACharacter& Player, APlayerController& Controller, const FStoryJumpPoint& Point)
{
	if (Point.AnchorRole.IsNone())
	{
		return true;
	}
	AActor* Anchor = FindRole(Flow, Point.AnchorRole);
	AActor* Face = Point.FaceRole.IsNone() ? nullptr : FindRole(Flow, Point.FaceRole);
	if (!IsValid(Anchor) || (!Point.FaceRole.IsNone() && !IsValid(Face)))
	{
		return false;
	}

	const FVector Position = Anchor->GetActorLocation() +
		FVector(0, 0, Player.GetCapsuleComponent()->GetScaledCapsuleHalfHeight() + 2);
	const float Yaw = Face ? (Face->GetActorLocation() - Position).Rotation().Yaw : Anchor->GetActorRotation().Yaw;
	const FRotator Rotation(0, Yaw, 0);
	if (!Player.TeleportTo(Position, Rotation))
	{
		return false;
	}
	Player.GetCharacterMovement()->StopMovementImmediately();
	Controller.SetControlRotation(Rotation);
	return true;
}

bool PrepareFlow(AActor& Flow, FName Preparation)
{
	if (Preparation.IsNone())
	{
		return true;
	}
	const bool bDeviceReady = Preparation == TEXT("Chapter1DeviceReady");
	const bool bDeviceEquipped = Preparation == TEXT("Chapter1DeviceEquipped");
	const bool bAfterEscape = Preparation == TEXT("Chapter1AfterEscape") || bDeviceReady || bDeviceEquipped;
	const bool bPastWake = bAfterEscape || Preparation == TEXT("Chapter1AfterWake") ||
		Preparation == TEXT("Chapter1AfterLowPass");
	if (!bPastWake)
	{
		// Future mission Blueprints can supply an idempotent no-argument preparation function.
		return Call(Flow, Preparation);
	}

	const FIntProperty* BlinkBeat = Property<FIntProperty>(Flow, TEXT("BlinkBeat"));
	if (!BlinkBeat)
	{
		return false;
	}
	BlinkBeat->SetPropertyValue_InContainer(&Flow, 6);

	if (Preparation == TEXT("Chapter1AfterLowPass") && !SetFlag(Flow, TEXT("CrossedLowPass"), true))
	{
		return false;
	}
	if (!bAfterEscape)
	{
		return true;
	}
	if (!SetFlag(Flow, TEXT("CrossedNorth"), true) || !Call(Flow, TEXT("StopEscapeAmbience")) ||
		!Call(Flow, TEXT("RestoreInjurySpeed")))
	{
		return false;
	}
	if (!bDeviceReady && !bDeviceEquipped)
	{
		return true;
	}

	AActor* Head = Cast<AActor>(ObjectField(Flow, TEXT("OmenHead")));
	AActor* Lift = Cast<AActor>(ObjectField(Flow, TEXT("EquipmentLift")));
	AActor* Regulator = Cast<AActor>(ObjectField(Flow, TEXT("RegulatorMesh")));
	AActor* Latch = Cast<AActor>(ObjectField(Flow, TEXT("DeviceLatch")));
	if (!IsValid(Head) || !IsValid(Lift) || !IsValid(Regulator) || !IsValid(Latch) ||
		!SetFlag(Flow, TEXT("DeviceEquipped"), bDeviceEquipped))
	{
		return false;
	}
	FVector HeadLocation = Head->GetActorLocation();
	HeadLocation.Z = 700;
	Head->SetActorLocation(HeadLocation);
	FVector LiftLocation = Lift->GetActorLocation();
	LiftLocation.Z = 43;
	Lift->SetActorLocation(LiftLocation);
	Regulator->SetActorHiddenInGame(bDeviceEquipped);
	Latch->SetActorHiddenInGame(bDeviceEquipped);
	return true;
}

AActor* FindUniqueFlow(UWorld& World, const FString& ClassPath)
{
	UClass* Class = FindObject<UClass>(nullptr, *ClassPath);
	if (!Class)
	{
		return nullptr;
	}
	TActorIterator<AActor> It(&World, Class);
	AActor* Flow = It ? *It : nullptr;
	if (It)
	{
		++It;
	}
	return It ? nullptr : Flow;
}

bool HasStep(AActor& Flow, FName Step, bool bCheckpoint)
{
	TInlineComponentArray<UActorComponent*> Components(&Flow);
	int32 Matches = 0;
	for (const UActorComponent* Component : Components)
	{
		const FNameProperty* Id = Property<FNameProperty>(*Component, TEXT("StepId"));
		if (Id && Id->GetPropertyValue_InContainer(Component) == Step &&
			(!bCheckpoint || Flag(*Component, TEXT("bCheckpoint"))))
		{
			++Matches;
		}
	}
	return Matches == 1;
}
}

void FStoryJump::Start()
{
	TArray<FString> Rows;
	GConfig->GetArray(ConfigSection, TEXT("Points"), Rows, GGameIni);
	TSet<FName> Seen;
	for (const FString& Row : Rows)
	{
		TSharedPtr<FStoryJumpPoint> Point = MakeShared<FStoryJumpPoint>();
		Point->Id = FName(*Field(Row, TEXT("Id=")));
		Point->Label = Field(Row, TEXT("Label="));
		const FString Group = FString(ConfigSection) + TEXT(".") + Field(Row, TEXT("Group="));
		GConfig->GetString(*Group, TEXT("Map"), Point->Map, GGameIni);
		GConfig->GetString(*Group, TEXT("Options"), Point->Options, GGameIni);
		GConfig->GetString(*Group, TEXT("FlowClass"), Point->FlowClass, GGameIni);
		Point->PickupClass = Field(Row, TEXT("Pickup="));
		if (!Point->PickupClass.IsEmpty())
		{
			GConfig->GetString(*Group, TEXT("EquipmentClass"), Point->EquipmentClass, GGameIni);
			GConfig->GetString(*Group, TEXT("EquipmentSlot"), Point->EquipmentSlot, GGameIni);
			FString PickupClassPath;
			if (GConfig->GetString(*Group, *Point->PickupClass, PickupClassPath, GGameIni))
			{
				Point->PickupClass = MoveTemp(PickupClassPath);
			}
		}
		Point->Step = FName(*Field(Row, TEXT("Step=")));
		Point->Prepare = FName(*Field(Row, TEXT("Prepare=")));
		Point->AnchorRole = FName(*Field(Row, TEXT("Anchor=")));
		Point->FaceRole = FName(*Field(Row, TEXT("Face=")));
		Point->bCheckpoint = Field(Row, TEXT("Checkpoint=")).ToBool();
		const FString Id = Point->Id.ToString();
		const bool bSafeId = Algo::AllOf(Id,
			[](TCHAR Character) { return FChar::IsAlnum(Character) || Character == TEXT('_'); });
		if (Point->Id.IsNone() || !bSafeId || Seen.Contains(Point->Id) || Point->Label.IsEmpty() ||
			!FPackageName::IsValidLongPackageName(Point->Map) || Point->FlowClass.IsEmpty() || Point->Step.IsNone() ||
			(!Point->PickupClass.IsEmpty() && (Point->EquipmentClass.IsEmpty() || Point->EquipmentSlot.IsEmpty())))
		{
			UE_LOG(LogStoryJump, Error, TEXT("Rejected invalid or duplicate story jump: %s"), *Id);
			continue;
		}
		Seen.Add(Point->Id);
		Points.Add(Point);
	}

	BeforeActorsHandle = FWorldDelegates::OnWorldPreActorTick.AddRaw(this, &FStoryJump::BeforeActors);
	CleanupHandle = FWorldDelegates::OnWorldCleanup.AddRaw(this, &FStoryJump::CleanWorld);
	ConsoleCommand = IConsoleManager::Get().RegisterConsoleCommand(TEXT("TS.StoryJump"),
		TEXT("Jump to a configured main story entry. Usage: TS.StoryJump <Id>"),
		FConsoleCommandWithWorldAndArgsDelegate::CreateRaw(this, &FStoryJump::RunCommand), ECVF_Default);
}

void FStoryJump::Stop()
{
	FWorldDelegates::OnWorldPreActorTick.Remove(BeforeActorsHandle);
	FWorldDelegates::OnWorldCleanup.Remove(CleanupHandle);
	if (ConsoleCommand)
	{
		IConsoleManager::Get().UnregisterConsoleObject(ConsoleCommand);
	}
}

bool FStoryJump::Travel(UWorld& World, const FStoryJumpPoint& Point)
{
	if (!World.IsGameWorld() || World.GetNetMode() != NM_Standalone || TravelRequested.Contains(&World) ||
		!FPackageName::DoesPackageExist(Point.Map))
	{
		UE_LOG(LogStoryJump, Error, TEXT("Cannot travel to %s from %s"), *Point.Id.ToString(), *World.GetName());
		return false;
	}
	const FString Options = Point.Options + FString::Printf(TEXT("?%s=%s"), TravelOption, *Point.Id.ToString());
	UE_LOG(LogStoryJump, Log, TEXT("Travel requested: %s (%s)"), *Point.Id.ToString(), *Point.Map);
	TravelRequested.Add(&World);
	UGameplayStatics::OpenLevel(&World, FName(*Point.Map), true, Options);
	return true;
}

void FStoryJump::RunCommand(const TArray<FString>& Args, UWorld* World)
{
	const TSharedPtr<FStoryJumpPoint>* Point = Args.Num() == 1 ? Points.FindByPredicate(
		[&Args](const TSharedPtr<FStoryJumpPoint>& Item) { return Item->Id == FName(*Args[0]); }) : nullptr;
	if (World && Point)
	{
		Travel(*World, **Point);
		return;
	}
	UE_LOG(LogStoryJump, Warning, TEXT("Usage: TS.StoryJump <configured Id> in a standalone game world"));
}

void FStoryJump::CleanWorld(UWorld* World, bool, bool)
{
	Arrivals.Remove(World);
	TravelRequested.Remove(World);
}

void FStoryJump::BeforeActors(UWorld* World, ELevelTick, float)
{
	const AGameModeBase* Mode = World->GetAuthGameMode();
	if (!World->IsGameWorld() || World->GetNetMode() != NM_Standalone || !Mode)
	{
		return;
	}

	FArrival* Arrival = Arrivals.Find(World);
	if (!Arrival)
	{
		FArrival& New = Arrivals.Add(World);
		New.Id = FName(*UGameplayStatics::ParseOption(Mode->OptionsString, TravelOption));
		New.Deadline = FPlatformTime::Seconds() + 15.0;
		New.bFinished = New.Id.IsNone();
		Arrival = &New;
	}
	if (Arrival->bFinished)
	{
		return;
	}

	const TSharedPtr<FStoryJumpPoint>* Found = Points.FindByPredicate(
		[Arrival](const TSharedPtr<FStoryJumpPoint>& Point) { return Point->Id == Arrival->Id; });
	const auto Reject = [Arrival](const TCHAR* Reason)
	{
		if (AActor* Flow = Arrival->SuspendedFlow.Get())
		{
			Flow->SetActorTickEnabled(true);
		}
		if (AActor* Pickup = Arrival->Pickup.Get())
		{
			Pickup->Destroy();
		}
		Arrival->bFinished = true;
		UE_LOG(LogStoryJump, Error, TEXT("Story jump %s failed: %s"), *Arrival->Id.ToString(), Reason);
	};
	if (!Found)
	{
		Reject(TEXT("unknown travel point"));
		return;
	}
	const FStoryJumpPoint& Point = **Found;
	if (UGameplayStatics::GetCurrentLevelName(World) != FPackageName::GetShortName(Point.Map))
	{
		Reject(TEXT("travel arrived in the wrong map"));
		return;
	}
	if (FPlatformTime::Seconds() > Arrival->Deadline)
	{
		Reject(TEXT("timed out waiting for the local player, mission flow or equipment"));
		return;
	}

	AActor* Flow = FindUniqueFlow(*World, Point.FlowClass);
	APlayerController* Controller = World->GetFirstPlayerController();
	ACharacter* Player = Controller ? Cast<ACharacter>(Controller->GetPawn()) : nullptr;
	if (!IsValid(Flow) || !IsValid(Player))
	{
		return;
	}

	if (!Arrival->bPrepared)
	{
		if (Flag(*Flow, TEXT("bInitialized")) || !HasStep(*Flow, Point.Step, Point.bCheckpoint))
		{
			Reject(TEXT("flow already initialized or configured step missing, duplicate or not a checkpoint"));
			return;
		}
		if (!Point.PickupClass.IsEmpty())
		{
			const UObject* Equipment = ObjectField(*Player, TEXT("SpawnedItem"));
			const UClass* EquipmentClass = FindObject<UClass>(nullptr, *Point.EquipmentClass);
			const bool bEquipmentReady = IsValid(Equipment) && EquipmentClass && Equipment->IsA(EquipmentClass);
			if (bEquipmentReady)
			{
				Flow->SetActorTickEnabled(true);
				Arrival->SuspendedFlow.Reset();
			}
			else if (!Arrival->bEquipRequested)
			{
				UClass* Class = LoadClass<AActor>(nullptr, *Point.PickupClass);
				FActorSpawnParameters Parameters;
				Parameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
				AActor* Pickup = Class ? World->SpawnActor<AActor>(
					Class, Player->GetActorLocation(), Player->GetActorRotation(), Parameters) : nullptr;
				if (IsValid(Pickup))
				{
					FocusPickup(*Pickup);
				}
				if (!IsValid(Pickup) || !Call(*Pickup, TEXT("Interface_Interact")))
				{
					Arrival->Pickup = Pickup;
					Reject(TEXT("native prerequisite pickup did not accept interaction"));
					return;
				}
				Arrival->Pickup = Pickup;
				Arrival->bEquipRequested = true;
				Flow->SetActorTickEnabled(false);
				Arrival->SuspendedFlow = Flow;
				return;
			}
			else
			{
				// Native pickup can populate the slot while the player's spawn-time equip gate is closed.
				const double Now = FPlatformTime::Seconds();
				if (Now >= Arrival->NextEquipAttempt)
				{
					if (!EquipFromSlot(*Player, Point.EquipmentSlot))
					{
						Reject(TEXT("configured equipment slot did not match the native equip API"));
						return;
					}
					Arrival->NextEquipAttempt = Now + 0.25;
				}
				return;
			}
		}
		if (!PlaceAtRole(*Flow, *Player, *Controller, Point) || !PrepareFlow(*Flow, Point.Prepare) ||
			!SetName(*Flow, TEXT("StartStep"), Point.Step))
		{
			Reject(TEXT("anchor, preparation or StartStep is unavailable"));
			return;
		}
		Arrival->bPrepared = true;
	}

	const FNameProperty* Pending = Property<FNameProperty>(*Flow, TEXT("PendingStep"));
	if (!Pending || Pending->GetPropertyValue_InContainer(Flow) != Point.Step)
	{
		return;
	}
	Arrival->bFinished = true;
	UE_LOG(LogStoryJump, Log, TEXT("Story jump %s prepared; starting native task %s"),
		*Point.Id.ToString(), *Point.Step.ToString());
}

#endif
