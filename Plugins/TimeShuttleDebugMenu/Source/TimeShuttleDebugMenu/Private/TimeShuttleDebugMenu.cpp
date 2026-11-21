#include "CoreMinimal.h"
#include "StoryJump.h"
#include "Components/ActorComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Framework/Application/IInputProcessor.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Input/Events.h"
#include "Kismet/GameplayStatics.h"
#include "Layout/WidgetPath.h"
#include "Modules/ModuleManager.h"
#include "Styling/CoreStyle.h"
#include "UObject/UnrealType.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SComboBox.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SViewport.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST

DEFINE_LOG_CATEGORY_STATIC(LogTimeShuttleDebugMenu, Log, All);

namespace
{
constexpr TCHAR TimeAbilityClass[] =
	TEXT("/Game/Blueprints/Components/Player/AC_TimeAbility.AC_TimeAbility_C");
constexpr TCHAR KeyPromptClass[] =
	TEXT("/Game/Blueprints/Components/Player/AC_KeyPrompt.AC_KeyPrompt_C");
constexpr TCHAR AutomaticClass[] =
	TEXT("/Game/Blueprints/Weapons/Player/WeaponBases/BP_Weapon_AutomaticBase.BP_Weapon_AutomaticBase_C");
constexpr TCHAR ShotgunClass[] =
	TEXT("/Game/Blueprints/Weapons/Player/WeaponBases/BP_Weapon_ShotgunBase.BP_Weapon_ShotgunBase_C");

const FLinearColor Accent(0.30f, 0.92f, 0.84f);
const FLinearColor Secondary(0.59f, 0.68f, 0.72f);

template <typename PropertyType>
const PropertyType* FindProperty(const UObject* Object, FName Name)
{
	return IsValid(Object) ? FindFProperty<PropertyType>(Object->GetClass(), Name) : nullptr;
}

bool IsLoadedClass(const UObject* Object, const TCHAR* ClassPath)
{
	const UClass* Class = FindObject<UClass>(nullptr, ClassPath);
	return Class && IsValid(Object) && Object->IsA(Class);
}

FString ReadNumber(const UObject* Object, FName Name)
{
	const FNumericProperty* Property = FindProperty<FNumericProperty>(Object, Name);
	if (!Property)
	{
		return TEXT("-");
	}

	const void* Value = Property->ContainerPtrToValuePtr<void>(Object);
	if (Property->IsFloatingPoint())
	{
		return FString::Printf(TEXT("%.0f"), Property->GetFloatingPointPropertyValue(Value));
	}
	return LexToString(Property->GetSignedIntPropertyValue(Value));
}

UActorComponent* FindComponent(APawn* Pawn, const TCHAR* ClassPath)
{
	UClass* Class = FindObject<UClass>(nullptr, ClassPath);
	return Class && IsValid(Pawn) ? Pawn->GetComponentByClass(Class) : nullptr;
}

UObject* FindFirearm(APawn* Pawn)
{
	const FObjectPropertyBase* Property = FindProperty<FObjectPropertyBase>(Pawn, TEXT("SpawnedItem"));
	UObject* Item = Property ? Property->GetObjectPropertyValue_InContainer(Pawn) : nullptr;
	return IsLoadedClass(Item, AutomaticClass) || IsLoadedClass(Item, ShotgunClass) ? Item : nullptr;
}

class FDebugMenu final : public IInputProcessor
{
public:
	explicit FDebugMenu(FStoryJump& InStoryJump) : StoryJump(InStoryJump) {}

	void Tick(float DeltaTime, FSlateApplication&, TSharedRef<ICursor>) override
	{
		if (!Overlay)
		{
			return;
		}

		if (!Controller.IsValid() || !Viewport.IsValid() || !Pawn.IsValid() ||
			Controller->GetPawn() != Pawn.Get())
		{
			Close(Overlay->HasUserFocusedDescendants(SlateUser));
			return;
		}

		RefreshIn -= DeltaTime;
		if (RefreshIn <= 0.f)
		{
			Refresh();
		}
	}

	bool HandleKeyDownEvent(FSlateApplication&, const FKeyEvent& Event) override
	{
		const FKey Key = Event.GetKey();
		if (ConsumedKeys.Contains(Key) && Event.IsRepeat())
		{
			return true;
		}
		if (Key != EKeys::F10 && Key != EKeys::Escape)
		{
			return false;
		}

		const int32 User = Event.GetUserIndex();
		if (Overlay)
		{
			if (!Overlay->HasUserFocusedDescendants(User))
			{
				const TSharedPtr<SViewport> Widget = PreviousFocus.Pin();
				if (!Widget || !Widget->HasUserFocus(User).IsSet())
				{
					return false;
				}
			}
			ConsumedKeys.Add(Key);
			Close(true);
			return true;
		}

		if (Key != EKeys::F10 || Event.IsRepeat() || !GEngine)
		{
			return false;
		}

		for (const FWorldContext& Context : GEngine->GetWorldContexts())
		{
			UWorld* World = Context.World();
			UGameViewportClient* GameViewport = Context.GameViewport;
			if (!World || !World->IsGameWorld() || World->GetNetMode() != NM_Standalone ||
				!GameViewport || GameViewport->IgnoreInput() || UGameplayStatics::IsGamePaused(World))
			{
				continue;
			}

			const TSharedPtr<SViewport> Widget = GameViewport->GetGameViewportWidget();
			APlayerController* Player = World->GetFirstPlayerController();
			APawn* PlayerPawn = Player ? Player->GetPawn() : nullptr;
			if (Widget && Widget->HasUserFocus(User).IsSet() && IsValid(PlayerPawn) &&
				Player->IsLocalController() && !Player->bShowMouseCursor &&
				FindProperty<FNumericProperty>(PlayerPawn, TEXT("Health")))
			{
				Open(*GameViewport, *Player, *PlayerPawn, Widget.ToSharedRef(), User);
				ConsumedKeys.Add(Key);
				return true;
			}
		}
		return false;
	}

	bool HandleKeyUpEvent(FSlateApplication&, const FKeyEvent& Event) override
	{
		return ConsumedKeys.Remove(Event.GetKey()) != 0;
	}

	void OnWorldTearDown(UWorld* World)
	{
		if (MenuWorld.Get() == World)
		{
			Close(false);
		}
	}

	void Close(bool bRestoreFocus)
	{
		if (!Overlay)
		{
			return;
		}

		if (UGameViewportClient* GameViewport = Viewport.Get())
		{
			GameViewport->RemoveViewportWidgetContent(Overlay.ToSharedRef());
			GameViewport->SetIgnoreInput(bPreviousIgnoreInput);
		}
		if (APlayerController* Player = Controller.Get())
		{
			Player->bShowMouseCursor = bPreviousCursor;
			Player->FlushPressedKeys();
		}

		Overlay.Reset();
		Status.Reset();
		InvulnerabilityLabel.Reset();
		ReloadLabel.Reset();
		EnergyButton.Reset();
		ReloadButton.Reset();
		SelectedStoryPoint.Reset();

		if (bRestoreFocus && FSlateApplication::IsInitialized())
		{
			if (const TSharedPtr<SViewport> Widget = PreviousFocus.Pin())
			{
				// In embedded PIE, mouse focus is what restores permanent viewport capture.
				const EFocusCause Cause = bPreviousCapture ? EFocusCause::Mouse : EFocusCause::SetDirectly;
				FSlateApplication::Get().SetUserFocus(SlateUser, Widget, Cause);
			}
		}
		PreviousFocus.Reset();
		Controller.Reset();
		Viewport.Reset();
		Pawn.Reset();
		MenuWorld.Reset();
		UE_LOG(LogTimeShuttleDebugMenu, Log, TEXT("Closed"));
	}

private:
	void Open(UGameViewportClient& GameViewport, APlayerController& Player, APawn& PlayerPawn,
		const TSharedRef<SViewport>& ViewportWidget, int32 User)
	{
		Viewport = &GameViewport;
		Controller = &Player;
		Pawn = &PlayerPawn;
		MenuWorld = PlayerPawn.GetWorld();
		PreviousFocus = ViewportWidget;
		SlateUser = User;
		bPreviousCapture = ViewportWidget->HasMouseCaptureByUser(User);
		bPreviousIgnoreInput = GameViewport.IgnoreInput();
		bPreviousCursor = Player.bShowMouseCursor;

		TSharedPtr<SButton> CloseButton;
		SAssignNew(Overlay, SOverlay)
		+ SOverlay::Slot()
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
			.BorderBackgroundColor(FLinearColor(0.01f, 0.02f, 0.025f, 0.62f))
			.Cursor(EMouseCursor::Default)
			.Padding(FMargin(24.f))
			.HAlign(HAlign_Center)
			.VAlign(VAlign_Center)
			[
				SNew(SBox)
				.WidthOverride(560.f)
				.MaxDesiredHeight(570.f)
				[
					SNew(SBorder)
					.BorderImage(FCoreStyle::Get().GetBrush("WhiteBrush"))
					.BorderBackgroundColor(FLinearColor(0.028f, 0.045f, 0.055f, 1.f))
					.Padding(FMargin(24.f, 20.f))
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 18.f)
						[
							SNew(SHorizontalBox)
							+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
							[
								SNew(STextBlock)
								.Text(FText::FromString(TEXT("Debug Menu")))
								.Font(FCoreStyle::GetDefaultFontStyle("Bold", 29))
								.ColorAndOpacity(Accent)
							]
							+ SHorizontalBox::Slot().AutoWidth()
							[
								SAssignNew(CloseButton, SButton)
								.ContentPadding(FMargin(12.f, 6.f))
								.OnClicked_Lambda([this]
								{
									Close(true);
									return FReply::Handled();
								})
								[
									SNew(STextBlock)
									.Text(FText::FromString(TEXT("Close")))
									.Font(FCoreStyle::GetDefaultFontStyle("Regular", 16))
								]
							]
						]
						+ SVerticalBox::Slot().FillHeight(1.f)
						[
							SNew(SScrollBox)
							+ SScrollBox::Slot().Padding(0.f, 0.f, 0.f, 14.f)
							[
								SAssignNew(Status, STextBlock)
								.Font(FCoreStyle::GetDefaultFontStyle("Regular", 17))
								.LineHeightPercentage(1.18f)
								.ColorAndOpacity(Secondary)
							]
							+ SScrollBox::Slot().Padding(0.f, 0.f, 0.f, 5.f)
							[
								SNew(STextBlock)
								.Text(FText::FromString(TEXT("Story Jump")))
								.Font(FCoreStyle::GetDefaultFontStyle("Bold", 18))
								.ColorAndOpacity(Accent)
							]
							+ SScrollBox::Slot().Padding(0.f, 0.f, 0.f, 16.f)
							[
								SNew(SHorizontalBox)
								+ SHorizontalBox::Slot().FillWidth(1.f).Padding(0.f, 0.f, 8.f, 0.f)
								[
									SNew(SComboBox<TSharedPtr<FStoryJumpPoint>>)
									.OptionsSource(&StoryJump.GetPoints())
									.MaxListHeight(285.f)
									.ToolTipText(FText::FromString(TEXT("Reload the destination map and start its story flow at the selected entry.")))
									.OnGenerateWidget_Lambda([](TSharedPtr<FStoryJumpPoint> Point)
									{
										return SNew(STextBlock)
											.Text(FText::FromString(Point->Label))
											.Font(FCoreStyle::GetDefaultFontStyle("Regular", 17));
									})
									.OnSelectionChanged_Lambda([this](TSharedPtr<FStoryJumpPoint> Point, ESelectInfo::Type)
									{
										SelectedStoryPoint = Point;
									})
									[
										SNew(STextBlock)
										.Font(FCoreStyle::GetDefaultFontStyle("Regular", 17))
										.Text_Lambda([this]
										{
											return FText::FromString(SelectedStoryPoint ? SelectedStoryPoint->Label : TEXT("Choose a story point"));
										})
									]
								]
								+ SHorizontalBox::Slot().AutoWidth()
								[
									SNew(SButton)
									.ContentPadding(FMargin(14.f, 7.f))
									.IsEnabled_Lambda([this] { return SelectedStoryPoint.IsValid(); })
									.OnClicked_Lambda([this]
									{
										if (UWorld* World = MenuWorld.Get())
										{
											if (SelectedStoryPoint && StoryJump.Travel(*World, *SelectedStoryPoint))
											{
												Close(false);
											}
										}
										return FReply::Handled();
									})
									[
										SNew(STextBlock)
										.Font(FCoreStyle::GetDefaultFontStyle("Bold", 17))
										.Text(FText::FromString(TEXT("Jump")))
									]
								]
							]
							+ SScrollBox::Slot().Padding(0.f, 0.f, 0.f, 6.f)
							[
								SNew(SButton)
								.ContentPadding(FMargin(14.f, 10.f))
								.OnClicked_Raw(this, &FDebugMenu::ToggleInvulnerability)
								[
									SAssignNew(InvulnerabilityLabel, STextBlock)
									.Font(FCoreStyle::GetDefaultFontStyle("Regular", 18))
								]
							]
							+ SScrollBox::Slot().Padding(0.f, 0.f, 0.f, 6.f)
							[
								SAssignNew(EnergyButton, SButton)
								.ContentPadding(FMargin(14.f, 10.f))
								.OnClicked_Raw(this, &FDebugMenu::RefillEnergy)
								[
									SNew(STextBlock)
									.Text(FText::FromString(TEXT("Refill Time Energy")))
									.Font(FCoreStyle::GetDefaultFontStyle("Regular", 18))
								]
							]
							+ SScrollBox::Slot()
							[
								SAssignNew(ReloadButton, SButton)
								.ContentPadding(FMargin(14.f, 10.f))
								.ToolTipText(FText::FromString(TEXT("Reload normally without spending reserve ammo on the equipped firearm.")))
								.OnClicked_Raw(this, &FDebugMenu::ToggleInfiniteReload)
								[
									SAssignNew(ReloadLabel, STextBlock)
									.Font(FCoreStyle::GetDefaultFontStyle("Regular", 18))
								]
							]
						]
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 14.f, 0.f, 0.f)
						[
							SNew(STextBlock)
							.Text(FText::FromString(TEXT("F10 / Esc to close  |  Simulation continues")))
							.Font(FCoreStyle::GetDefaultFontStyle("Regular", 16))
							.ColorAndOpacity(Secondary)
						]
					]
				]
			]
		];

		Refresh();
		GameViewport.AddViewportWidgetContent(Overlay.ToSharedRef(), 10000);
		Player.FlushPressedKeys();
		GameViewport.SetIgnoreInput(true);
		Player.bShowMouseCursor = true;

		FSlateApplication& Slate = FSlateApplication::Get();
		FWidgetPath Path;
		if (!Slate.GeneratePathToWidgetUnchecked(CloseButton.ToSharedRef(), Path))
		{
			Close(true);
			return;
		}
		Slate.ProcessReply(Path, FReply::Handled().ReleaseMouseCapture().ReleaseMouseLock()
			.SetUserFocus(CloseButton.ToSharedRef()), nullptr, nullptr, SlateUser);
		UE_LOG(LogTimeShuttleDebugMenu, Log, TEXT("Opened in %s"), *UGameplayStatics::GetCurrentLevelName(&PlayerPawn));
	}

	void Refresh()
	{
		RefreshIn = 0.2f;
		APawn* Player = Pawn.Get();
		if (!Player || !Status)
		{
			return;
		}

		UActorComponent* TimeAbility = FindComponent(Player, TimeAbilityClass);
		UObject* Firearm = FindFirearm(Player);
		const FBoolProperty* Infinite = FindProperty<FBoolProperty>(Firearm, TEXT("DebugInfiniteReload"));
		const FVector Position = Player->GetActorLocation();
		Status->SetText(FText::FromString(FString::Printf(
			TEXT("%s   |   World speed %.2fx\nPosition (cm)   %.0f, %.0f, %.0f\nHealth   %s     Time energy   %s / %s\nMagazine   %s     Reserve ammo   %s"),
			*UGameplayStatics::GetCurrentLevelName(Player), UGameplayStatics::GetGlobalTimeDilation(Player),
			Position.X, Position.Y, Position.Z, *ReadNumber(Player, TEXT("Health")),
			*ReadNumber(TimeAbility, TEXT("Energy")), *ReadNumber(TimeAbility, TEXT("MaxEnergy")),
			*ReadNumber(Firearm, TEXT("AmmoCount")), *ReadNumber(Firearm, TEXT("MaxAmmo")))));
		InvulnerabilityLabel->SetText(FText::FromString(Player->CanBeDamaged()
			? TEXT("Invulnerability: Off") : TEXT("Invulnerability: On")));
		ReloadLabel->SetText(FText::FromString(!Infinite ? TEXT("Infinite Reload: No firearm equipped")
			: Infinite->GetPropertyValue_InContainer(Firearm) ? TEXT("Infinite Reload: On") : TEXT("Infinite Reload: Off")));
		const FNumericProperty* Energy = FindProperty<FNumericProperty>(TimeAbility, TEXT("Energy"));
		const FNumericProperty* EnergyMaximum = FindProperty<FNumericProperty>(TimeAbility, TEXT("MaxEnergy"));
		EnergyButton->SetEnabled(Energy && Energy->IsFloatingPoint() &&
			EnergyMaximum && EnergyMaximum->IsFloatingPoint());
		ReloadButton->SetEnabled(Infinite != nullptr);
	}

	FReply ToggleInvulnerability()
	{
		if (APawn* Player = Pawn.Get())
		{
			Player->SetCanBeDamaged(!Player->CanBeDamaged());
			UE_LOG(LogTimeShuttleDebugMenu, Log, TEXT("Invulnerability: %s"),
				Player->CanBeDamaged() ? TEXT("Off") : TEXT("On"));
			Refresh();
		}
		return FReply::Handled();
	}

	FReply RefillEnergy()
	{
		UActorComponent* Ability = FindComponent(Pawn.Get(), TimeAbilityClass);
		const FNumericProperty* Energy = FindProperty<FNumericProperty>(Ability, TEXT("Energy"));
		const FNumericProperty* Maximum = FindProperty<FNumericProperty>(Ability, TEXT("MaxEnergy"));
		if (Energy && Maximum && Energy->IsFloatingPoint() && Maximum->IsFloatingPoint())
		{
			const double Value = Maximum->GetFloatingPointPropertyValue(Maximum->ContainerPtrToValuePtr<void>(Ability));
			Energy->SetFloatingPointPropertyValue(Energy->ContainerPtrToValuePtr<void>(Ability), Value);
			UE_LOG(LogTimeShuttleDebugMenu, Log, TEXT("Time energy refilled to %.2f"), Value);
			Refresh();
		}
		return FReply::Handled();
	}

	FReply ToggleInfiniteReload()
	{
		UObject* Firearm = FindFirearm(Pawn.Get());
		if (const FBoolProperty* Infinite = FindProperty<FBoolProperty>(Firearm, TEXT("DebugInfiniteReload")))
		{
			const bool bEnabled = !Infinite->GetPropertyValue_InContainer(Firearm);
			Infinite->SetPropertyValue_InContainer(Firearm, bEnabled);
			if (UActorComponent* KeyPrompt = FindComponent(Pawn.Get(), KeyPromptClass))
			{
				UFunction* UpdatePrompt = KeyPrompt->FindFunction(TEXT("UpdateReloadPrompt"));
				if (UpdatePrompt && UpdatePrompt->ParmsSize == 0)
				{
					KeyPrompt->ProcessEvent(UpdatePrompt, nullptr);
				}
			}
			UE_LOG(LogTimeShuttleDebugMenu, Log, TEXT("Infinite reload on %s: %s"),
				*GetNameSafe(Firearm), bEnabled ? TEXT("On") : TEXT("Off"));
			Refresh();
		}
		return FReply::Handled();
	}

	FStoryJump& StoryJump;
	TSharedPtr<FStoryJumpPoint> SelectedStoryPoint;
	TWeakObjectPtr<UGameViewportClient> Viewport;
	TWeakObjectPtr<APlayerController> Controller;
	TWeakObjectPtr<APawn> Pawn;
	TWeakObjectPtr<UWorld> MenuWorld;
	TWeakPtr<SViewport> PreviousFocus;
	TSharedPtr<SOverlay> Overlay;
	TSharedPtr<STextBlock> Status;
	TSharedPtr<STextBlock> InvulnerabilityLabel;
	TSharedPtr<STextBlock> ReloadLabel;
	TSharedPtr<SButton> EnergyButton;
	TSharedPtr<SButton> ReloadButton;
	TSet<FKey> ConsumedKeys;
	float RefreshIn = 0.f;
	int32 SlateUser = 0;
	bool bPreviousCapture = false;
	bool bPreviousCursor = false;
	bool bPreviousIgnoreInput = false;
};
}

#endif

class FTimeShuttleDebugMenuModule final : public IModuleInterface
{
#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST
	void StartupModule() override
	{
		if (FSlateApplication::IsInitialized() && !IsRunningCommandlet() && !IsRunningDedicatedServer())
		{
			StoryJump.Start();
			Menu = MakeShared<FDebugMenu>(StoryJump);
			FSlateApplication::Get().RegisterInputPreProcessor(Menu, 0);
			WorldTearDown = FWorldDelegates::OnWorldBeginTearDown.AddSP(Menu.ToSharedRef(), &FDebugMenu::OnWorldTearDown);
		}
	}

	void ShutdownModule() override
	{
		FWorldDelegates::OnWorldBeginTearDown.Remove(WorldTearDown);
		if (Menu && FSlateApplication::IsInitialized())
		{
			Menu->Close(false);
			FSlateApplication::Get().UnregisterInputPreProcessor(Menu);
		}
		Menu.Reset();
		StoryJump.Stop();
	}

	TSharedPtr<FDebugMenu> Menu;
	FStoryJump StoryJump;
	FDelegateHandle WorldTearDown;
#endif
};

IMPLEMENT_MODULE(FTimeShuttleDebugMenuModule, TimeShuttleDebugMenu)
