#pragma once

#include "CoreMinimal.h"
#include "Engine/World.h"

#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST

struct FStoryJumpPoint
{
	FName Id;
	FString Label;
	FString Map;
	FString Options;
	FString FlowClass;
	FString PickupClass;
	FString EquipmentClass;
	FString EquipmentSlot;
	FName Step;
	FName AnchorRole;
	FName FaceRole;
	FName Prepare;
	bool bCheckpoint = false;
};

class FStoryJump
{
public:
	void Start();
	void Stop();
	bool Travel(UWorld& World, const FStoryJumpPoint& Point);

	const TArray<TSharedPtr<FStoryJumpPoint>>& GetPoints() const { return Points; }

private:
	struct FArrival
	{
		TWeakObjectPtr<AActor> SuspendedFlow;
		TWeakObjectPtr<AActor> Pickup;
		FName Id;
		double Deadline = 0.0;
		double NextEquipAttempt = 0.0;
		bool bEquipRequested = false;
		bool bPrepared = false;
		bool bFinished = false;
	};

	void BeforeActors(UWorld* World, ELevelTick TickType, float DeltaSeconds);
	void CleanWorld(UWorld* World, bool bSessionEnded, bool bCleanupResources);
	void RunCommand(const TArray<FString>& Args, UWorld* World);

	TArray<TSharedPtr<FStoryJumpPoint>> Points;
	TMap<TWeakObjectPtr<UWorld>, FArrival> Arrivals;
	TSet<TWeakObjectPtr<UWorld>> TravelRequested;
	FDelegateHandle BeforeActorsHandle;
	FDelegateHandle CleanupHandle;
	class IConsoleObject* ConsoleCommand = nullptr;
};

#endif
