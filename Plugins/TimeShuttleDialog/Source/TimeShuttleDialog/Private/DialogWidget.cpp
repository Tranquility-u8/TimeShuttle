#include "DialogWidget.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/SafeZone.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"

void UDialogWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    SetIsFocusable(false);
    if (!SpeakerLabel || !DialogueLabel || !StatusLabel)
    {
        auto* Safe = WidgetTree->ConstructWidget<USafeZone>(USafeZone::StaticClass(), TEXT("DialogueSafeZone"));
        WidgetTree->RootWidget = Safe;
        auto* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>();
        Safe->AddChild(Canvas);
        auto* Panel = WidgetTree->ConstructWidget<UBorder>();
        Panel->SetBrushColor(PanelColor);
        Panel->SetPadding(FMargin(24, 16));
        auto* CanvasSlot = Canvas->AddChildToCanvas(Panel);
        CanvasSlot->SetAnchors(FAnchors(.12f, .88f, .88f, .88f));
        CanvasSlot->SetAlignment(FVector2D(0, 1));
        CanvasSlot->SetOffsets(FMargin(0, 0, 0, 0));
        CanvasSlot->SetAutoSize(true);
        auto* Rows = WidgetTree->ConstructWidget<UVerticalBox>();
        Panel->AddChild(Rows);
        SpeakerLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SpeakerLabel"));
        DialogueLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("DialogueLabel"));
        StatusLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("StatusLabel"));
        Rows->AddChildToVerticalBox(SpeakerLabel)->SetPadding(FMargin(0,0,0,7));
        Rows->AddChildToVerticalBox(DialogueLabel)->SetPadding(FMargin(0,0,0,12));
        Rows->AddChildToVerticalBox(StatusLabel);
    }
    auto Font = DialogueLabel->GetFont();
    Font.Size = TextSize;
    DialogueLabel->SetFont(Font);
    DialogueLabel->SetAutoWrapText(true);
    DialogueLabel->SetColorAndOpacity(TextColor);
    Font.Size = FMath::Max(16, TextSize - 3);
    SpeakerLabel->SetFont(Font);
    SpeakerLabel->SetColorAndOpacity(SpeakerColor);
    Font.Size = FMath::Max(14, TextSize - 8);
    StatusLabel->SetFont(Font);
    StatusLabel->SetColorAndOpacity(FLinearColor(.65f,.72f,.78f));
    SetVisibility(ESlateVisibility::HitTestInvisible);
}
void UDialogWidget::ShowLine(const FDialogLineRow& Line)
{
    if (SpeakerLabel) SpeakerLabel->SetText(Line.SpeakerName);
    if (DialogueLabel) DialogueLabel->SetText(Line.DialogueText);
}
void UDialogWidget::ShowStatus(bool bAutomatic, bool bCanAdvance, bool bPaused, bool bLoading)
{
    if (!StatusLabel) return;
    FText Text;
    if (bPaused) Text = NSLOCTEXT("DialogSystem", "Paused", "PAUSED");
    else if (bLoading) Text = NSLOCTEXT("DialogSystem", "Loading", "Loading dialogue...");
    else if (bAutomatic) Text = NSLOCTEXT("DialogSystem", "Auto", "AUTO   |   P: Manual");
    else if (bCanAdvance) Text = NSLOCTEXT("DialogSystem", "Next", "MANUAL   |   Enter / Space: Next   |   P: Auto");
    else Text = NSLOCTEXT("DialogSystem", "Listening", "MANUAL   |   Listening...   |   P: Auto");
    StatusLabel->SetText(Text);
}
