#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "DialogTypes.h"
#include "DialogWidget.generated.h"
class UTextBlock;
class UBorder;

/** Blueprint can supply its own layout using SpeakerLabel, DialogueLabel and StatusLabel names. */
UCLASS(Blueprintable)
class TIMESHUTTLEDIALOG_API UDialogWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue|Style") FLinearColor TextColor = FLinearColor::White;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue|Style") FLinearColor SpeakerColor = FLinearColor(.35f,.8f,1.f,1.f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue|Style") FLinearColor PanelColor = FLinearColor(.012f,.018f,.026f,.9f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Dialogue|Style", meta=(ClampMin="16", ClampMax="48")) int32 TextSize = 24;
    UFUNCTION(BlueprintCallable, Category="Dialogue") void ShowLine(const FDialogLineRow& Line);
    UFUNCTION(BlueprintCallable, Category="Dialogue") void ShowStatus(bool bAutomatic, bool bCanAdvance, bool bPaused, bool bLoading);
protected:
    virtual void NativeOnInitialized() override;
    UPROPERTY(BlueprintReadOnly, meta=(BindWidgetOptional), Category="Dialogue") TObjectPtr<UTextBlock> SpeakerLabel;
    UPROPERTY(BlueprintReadOnly, meta=(BindWidgetOptional), Category="Dialogue") TObjectPtr<UTextBlock> DialogueLabel;
    UPROPERTY(BlueprintReadOnly, meta=(BindWidgetOptional), Category="Dialogue") TObjectPtr<UTextBlock> StatusLabel;
};
