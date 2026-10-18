#include "LabAuthoringLibrary.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Components/SceneComponent.h"
#include "Dom/JsonObject.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraphNode_Comment.h"
#include "EdGraphSchema_K2.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Engine/SCS_Node.h"
#include "Engine/SimpleConstructionScript.h"
#include "FileHelpers.h"
#include "K2Node_CallFunction.h"
#include "K2Node_CallParentFunction.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_Event.h"
#include "K2Node_ExecutionSequence.h"
#include "K2Node_FunctionEntry.h"
#include "K2Node_FunctionResult.h"
#include "K2Node_IfThenElse.h"
#include "K2Node_Self.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "KismetCompiler.h"
#include "Kismet2/CompilerResultsLog.h"
#include "Logging/TokenizedMessage.h"
#include "Misc/PackageName.h"
#include "ScopedTransaction.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/UnrealType.h"

namespace LabAuthoring
{
using Obj = TSharedPtr<FJsonObject>;
using Val = TSharedPtr<FJsonValue>;
static Obj Object() { return MakeShared<FJsonObject>(); }
static FString Str(const Obj& J, const TCHAR* K, const FString& D=TEXT(""))
{ FString V; return J.IsValid() && J->TryGetStringField(K,V) ? V : D; }
static bool Flag(const Obj& J, const TCHAR* K, bool D=false)
{ bool V; return J.IsValid() && J->TryGetBoolField(K,V) ? V : D; }
static int32 Int(const Obj& J, const TCHAR* K, int32 D=0)
{ double V; return J.IsValid() && J->TryGetNumberField(K,V) ? static_cast<int32>(V) : D; }
static TArray<Val> Array(const Obj& J,const TCHAR* K)
{ const TArray<Val>* V; return J.IsValid() && J->TryGetArrayField(K,V) ? *V : TArray<Val>(); }
static Obj Child(const Obj& J,const TCHAR* K)
{ const Obj* V; return J.IsValid() && J->TryGetObjectField(K,V) ? *V : Obj(); }
static FString ValueText(const Val& V)
{
    if (!V.IsValid() || V->Type==EJson::Null) return TEXT("None");
    if (V->Type==EJson::String) return V->AsString();
    if (V->Type==EJson::Boolean) return V->AsBool() ? TEXT("true") : TEXT("false");
    if (V->Type==EJson::Number) return FString::Printf(TEXT("%.17g"),V->AsNumber());
    return TEXT("");
}
static FString Json(const Obj& J)
{ FString R; auto W=TJsonWriterFactory<>::Create(&R); FJsonSerializer::Serialize(J.ToSharedRef(),W); return R; }
static UClass* Class(const FString& Path)
{
    if (Path.IsEmpty()) return nullptr;
    if (UClass* C=LoadObject<UClass>(nullptr,*Path)) return C;
    if (UBlueprint* B=LoadObject<UBlueprint>(nullptr,*Path)) return B->GeneratedClass;
    return nullptr;
}
static FEdGraphPinType Type(const Obj& J)
{
    FEdGraphPinType P; const FString T=Str(J,TEXT("type"),TEXT("bool"));
    if (T==TEXT("float") || T==TEXT("double")) { P.PinCategory=UEdGraphSchema_K2::PC_Real; P.PinSubCategory=UEdGraphSchema_K2::PC_Double; }
    else if (T==TEXT("float32")) { P.PinCategory=UEdGraphSchema_K2::PC_Real; P.PinSubCategory=UEdGraphSchema_K2::PC_Float; }
    else if (T==TEXT("vector") || T==TEXT("rotator") || T==TEXT("transform"))
    {
        P.PinCategory=UEdGraphSchema_K2::PC_Struct;
        const FString S=T==TEXT("vector") ? TEXT("Vector") : T==TEXT("rotator") ? TEXT("Rotator") : TEXT("Transform");
        P.PinSubCategoryObject=LoadObject<UScriptStruct>(nullptr,*(TEXT("/Script/CoreUObject.")+S));
    }
    else if (T==TEXT("object") || T==TEXT("class"))
    { P.PinCategory=T==TEXT("class") ? UEdGraphSchema_K2::PC_Class : UEdGraphSchema_K2::PC_Object; P.PinSubCategoryObject=Class(Str(J,TEXT("class"),TEXT("/Script/Engine.Actor"))); }
    else if (T==TEXT("struct")) { P.PinCategory=UEdGraphSchema_K2::PC_Struct; P.PinSubCategoryObject=LoadObject<UScriptStruct>(nullptr,*Str(J,TEXT("class"))); }
    else { P.PinCategory=FName(*T); }
    if (Flag(J,TEXT("array"))) P.ContainerType=EPinContainerType::Array;
    return P;
}
static Obj PinInfo(UEdGraphPin* P)
{
    Obj J=Object(); J->SetStringField(TEXT("name"),P->PinName.ToString());
    J->SetStringField(TEXT("direction"),P->Direction==EGPD_Input?TEXT("in"):TEXT("out"));
    J->SetStringField(TEXT("type"),P->PinType.PinCategory.ToString()); J->SetStringField(TEXT("subtype"),P->PinType.PinSubCategory.ToString());
    if (P->PinType.PinSubCategoryObject.IsValid()) J->SetStringField(TEXT("class"),P->PinType.PinSubCategoryObject->GetPathName());
    J->SetStringField(TEXT("default"),P->DefaultValue); J->SetBoolField(TEXT("hidden"),P->bHidden);
    if (P->DefaultObject) J->SetStringField(TEXT("object"),P->DefaultObject->GetPathName());
    TArray<Val> Links; for (UEdGraphPin* L:P->LinkedTo) { Obj V=Object(); V->SetStringField(TEXT("node"),L->GetOwningNode()->GetName()); V->SetStringField(TEXT("pin"),L->PinName.ToString()); Links.Add(MakeShared<FJsonValueObject>(V)); }
    J->SetArrayField(TEXT("links"),Links); return J;
}
static Obj Inspect(UBlueprint* B)
{
    Obj R=Object(); R->SetBoolField(TEXT("ok"),B!=nullptr); if (!B) return R;
    R->SetStringField(TEXT("asset"),B->GetPathName()); R->SetStringField(TEXT("parent"),GetPathNameSafe(B->ParentClass)); R->SetNumberField(TEXT("status"),static_cast<int32>(B->Status));
    TArray<Val> Graphs; TArray<UEdGraph*> All; B->GetAllGraphs(All);
    for (UEdGraph* G:All)
    {
        Obj J=Object(); J->SetStringField(TEXT("name"),G->GetName()); TArray<Val> Nodes;
        for (UEdGraphNode* N:G->Nodes)
        {
            Obj O=Object(); O->SetStringField(TEXT("name"),N->GetName()); O->SetStringField(TEXT("class"),N->GetClass()->GetPathName()); O->SetStringField(TEXT("title"),N->GetNodeTitle(ENodeTitleType::ListView).ToString());
            if (auto Call=Cast<UK2Node_CallFunction>(N)) { O->SetStringField(TEXT("function"),Call->FunctionReference.GetMemberName().ToString()); O->SetStringField(TEXT("function_owner"),GetPathNameSafe(Call->FunctionReference.GetMemberParentClass())); }
            O->SetNumberField(TEXT("x"),N->NodePosX); O->SetNumberField(TEXT("y"),N->NodePosY);
            TArray<Val> Pins; for (UEdGraphPin* P:N->Pins) Pins.Add(MakeShared<FJsonValueObject>(PinInfo(P))); O->SetArrayField(TEXT("pins"),Pins); Nodes.Add(MakeShared<FJsonValueObject>(O));
        }
        J->SetArrayField(TEXT("nodes"),Nodes); Graphs.Add(MakeShared<FJsonValueObject>(J));
    }
    R->SetArrayField(TEXT("graphs"),Graphs); TArray<Val> Vars;
    for (const FBPVariableDescription& V:B->NewVariables) { Obj J=Object(); J->SetStringField(TEXT("name"),V.VarName.ToString()); J->SetStringField(TEXT("default"),V.DefaultValue); J->SetStringField(TEXT("type"),V.VarType.PinCategory.ToString()); Vars.Add(MakeShared<FJsonValueObject>(J)); }
    R->SetArrayField(TEXT("variables"),Vars); TArray<Val> Comps;
    if (B->SimpleConstructionScript) for (USCS_Node* N:B->SimpleConstructionScript->GetAllNodes()) { Obj J=Object(); J->SetStringField(TEXT("name"),N->GetVariableName().ToString()); J->SetStringField(TEXT("class"),GetPathNameSafe(N->ComponentClass)); J->SetStringField(TEXT("template"),GetPathNameSafe(N->ComponentTemplate)); Comps.Add(MakeShared<FJsonValueObject>(J)); }
    R->SetArrayField(TEXT("components"),Comps); return R;
}
static bool Properties(UObject* Target,const Obj& Props,TArray<Val>& Errors)
{
    if (!Props.IsValid()) return true;
    bool Good=true;
    for (const auto& KV:Props->Values)
    {
        TArray<FString> Parts; KV.Key.ParseIntoArray(Parts,TEXT(".")); void* Container=Target; UStruct* Owner=Target->GetClass(); FProperty* P=nullptr;
        for (int32 I=0;I<Parts.Num();++I)
        {
            P=FindFProperty<FProperty>(Owner,*Parts[I]); if (!P) break;
            if (I+1<Parts.Num()) { FStructProperty* S=CastField<FStructProperty>(P); if (!S) { P=nullptr; break; } Container=S->ContainerPtrToValuePtr<void>(Container); Owner=S->Struct; }
        }
        if (!P) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Property not found: ")+GetNameSafe(Target)+TEXT(".")+KV.Key)); Good=false; continue; }
        void* Address=P->ContainerPtrToValuePtr<void>(Container);
        if (KV.Value->Type==EJson::Object && KV.Value->AsObject()->HasField(TEXT("object")))
        {
            FObjectPropertyBase* OP=CastField<FObjectPropertyBase>(P); const FString Path=Str(KV.Value->AsObject(),TEXT("object")); UObject* O=Path.IsEmpty()?nullptr:LoadObject<UObject>(nullptr,*Path);
            if (!OP || (!O && !Path.IsEmpty())) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Invalid object property: ")+KV.Key)); Good=false; continue; } OP->SetObjectPropertyValue(Address,O);
        }
        else if (!P->ImportText_Direct(*ValueText(KV.Value),Address,Target,PPF_None)) { Errors.Add(MakeShared<FJsonValueString>(TEXT("ImportText failed: ")+KV.Key+TEXT(" = ")+ValueText(KV.Value))); Good=false; }
    }
    Target->PostEditChange(); return Good;
}
static USCS_Node* FindParent(UBlueprint* B,FName Name)
{
    if (B->SimpleConstructionScript) if (USCS_Node* N=B->SimpleConstructionScript->FindSCSNode(Name)) return N;
    for (UClass* C=B->ParentClass;C;C=C->GetSuperClass()) if (UBlueprintGeneratedClass* BG=Cast<UBlueprintGeneratedClass>(C)) if (BG->SimpleConstructionScript) if (USCS_Node* N=BG->SimpleConstructionScript->FindSCSNode(Name)) return N;
    return nullptr;
}
static UEdGraphPin* Pin(UEdGraphNode* N,const FString& Name,EEdGraphPinDirection Dir)
{
    if (!N) return nullptr; UEdGraphPin* Fallback=nullptr;
    for (UEdGraphPin* P:N->Pins) if (P->PinName.ToString()==Name) { if (P->Direction==Dir) return P; Fallback=P; }
    return Fallback;
}
}

FString ULabAuthoringLibrary::InspectBlueprint(const FString& AssetPath)
{ return LabAuthoring::Json(LabAuthoring::Inspect(LoadObject<UBlueprint>(nullptr,*AssetPath))); }

FString ULabAuthoringLibrary::InspectClass(const FString& ClassPath)
{
    using namespace LabAuthoring; Obj R=Object(); UClass* C=Class(ClassPath); R->SetBoolField(TEXT("ok"),C!=nullptr); if (!C) return Json(R);
    R->SetStringField(TEXT("class"),C->GetPathName()); TArray<Val> Functions,PropertiesArray; UObject* D=C->GetDefaultObject();
    for (TFieldIterator<UFunction> F(C,EFieldIteratorFlags::IncludeSuper);F;++F)
    {
        Obj J=Object(); J->SetStringField(TEXT("name"),F->GetName()); J->SetStringField(TEXT("owner"),GetPathNameSafe(F->GetOwnerClass())); J->SetBoolField(TEXT("pure"),F->HasAnyFunctionFlags(FUNC_BlueprintPure)); TArray<Val> Params;
        for (TFieldIterator<FProperty> P(*F);P && P->HasAnyPropertyFlags(CPF_Parm);++P) { Obj V=Object(); V->SetStringField(TEXT("name"),P->GetName()); V->SetStringField(TEXT("cpp_type"),P->GetCPPType()); V->SetBoolField(TEXT("out"),P->HasAnyPropertyFlags(CPF_OutParm)); V->SetBoolField(TEXT("return"),P->HasAnyPropertyFlags(CPF_ReturnParm)); Params.Add(MakeShared<FJsonValueObject>(V)); }
        J->SetArrayField(TEXT("params"),Params); Functions.Add(MakeShared<FJsonValueObject>(J));
    }
    for (TFieldIterator<FProperty> P(C,EFieldIteratorFlags::IncludeSuper);P;++P)
    { Obj V=Object(); V->SetStringField(TEXT("name"),P->GetName()); V->SetStringField(TEXT("cpp_type"),P->GetCPPType()); if (D) { FString T; P->ExportText_InContainer(0,T,D,D,D,PPF_None); V->SetStringField(TEXT("default"),T); } PropertiesArray.Add(MakeShared<FJsonValueObject>(V)); }
    R->SetArrayField(TEXT("functions"),Functions); R->SetArrayField(TEXT("properties"),PropertiesArray); return Json(R);
}

FString ULabAuthoringLibrary::ApplyGraphPresentation(const FString& JsonPatch)
{
    using namespace LabAuthoring;
    Obj Patch,Report=Object(); TArray<Val> Errors; UBlueprint* BP=nullptr;
    Report->SetBoolField(TEXT("applied"),false);
    Report->SetBoolField(TEXT("compiled"),false);
    Report->SetBoolField(TEXT("saved"),false);
    auto Error=[&](const FString& Message) { Errors.Add(MakeShared<FJsonValueString>(Message)); };
    auto Finish=[&]() { Report->SetBoolField(TEXT("ok"),Errors.IsEmpty()); Report->SetArrayField(TEXT("errors"),Errors); return Json(Report); };
    if (!IsInGameThread()) { Error(TEXT("Presentation edits require the editor game thread")); return Finish(); }
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(JsonPatch),Patch) || !Patch.IsValid())
    { Error(TEXT("Invalid JSON object")); return Finish(); }
    auto OnlyKeys=[&](const Obj& J,std::initializer_list<const TCHAR*> Allowed,const FString& Where)
    {
        if (!J.IsValid()) { Error(Where+TEXT(" must be an object")); return false; }
        bool Good=true;
        for (const auto& KV:J->Values)
        {
            bool Found=false; for (const TCHAR* Key:Allowed) if (KV.Key==Key) { Found=true; break; }
            if (!Found) { Error(TEXT("Forbidden presentation patch field: ")+Where+TEXT(".")+KV.Key); Good=false; }
        }
        return Good;
    };
    auto Integer=[&](const Obj& J,const TCHAR* Key,int32& Value,const FString& Where)
    {
        double Number=0;
        if (!J.IsValid() || !J->TryGetNumberField(Key,Number) || !FMath::IsFinite(Number) ||
            Number<static_cast<double>(MIN_int32) || Number>static_cast<double>(MAX_int32))
        { Error(Where+TEXT(".")+Key+TEXT(" must be a finite int32")); return false; }
        Value=static_cast<int32>(Number);
        if (static_cast<double>(Value)!=Number) { Error(Where+TEXT(".")+Key+TEXT(" must be an integer")); return false; }
        return true;
    };
    OnlyKeys(Patch,{TEXT("asset"),TEXT("graphs"),TEXT("kind"),TEXT("node_count"),TEXT("all_links_defaults_and_node_fields_unchanged")},TEXT("patch"));
    const FString Asset=Str(Patch,TEXT("asset"));
    if (Asset.IsEmpty()) { Error(TEXT("asset is required")); return Finish(); }
    BP=LoadObject<UBlueprint>(nullptr,*Asset);
    if (!BP) { Error(TEXT("Blueprint not found: ")+Asset); return Finish(); }
    Report->SetStringField(TEXT("asset"),BP->GetPathName());
    Report->SetObjectField(TEXT("before"),Inspect(BP));
    const TArray<Val>* GraphPatches=nullptr;
    if (!Patch->TryGetArrayField(TEXT("graphs"),GraphPatches) || GraphPatches->IsEmpty())
    { Error(TEXT("graphs must be a nonempty array")); return Finish(); }

    struct FPresentationEdit
    {
        UEdGraphNode* Node=nullptr;
        int32 X=0,Y=0,Width=0,Height=0,OldX=0,OldY=0,OldWidth=0,OldHeight=0;
        FString Text,OldText;
        FLinearColor Color=FLinearColor::White,OldColor=FLinearColor::White;
        bool bWidth=false,bHeight=false,bText=false,bColor=false,bChanged=false;
    };
    TArray<FPresentationEdit> Edits;
    TArray<UEdGraph*> AllGraphs; BP->GetAllGraphs(AllGraphs);
    TSet<FString> SeenGraphs;
    TSet<UEdGraphNode*> SeenNodes;
    // Complete preflight: no Modify/dirtying/writes occur anywhere in this loop.
    for (const Val& GraphValue:*GraphPatches)
    {
        if (!GraphValue.IsValid() || GraphValue->Type!=EJson::Object) { Error(TEXT("Each graph patch must be an object")); continue; }
        const Obj GraphPatch=GraphValue->AsObject();
        OnlyKeys(GraphPatch,{TEXT("name"),TEXT("nodes")},TEXT("graph"));
        const FString GraphName=Str(GraphPatch,TEXT("name"));
        if (GraphName.IsEmpty() || SeenGraphs.Contains(GraphName)) { Error(TEXT("Empty or duplicate graph patch: ")+GraphName); continue; }
        SeenGraphs.Add(GraphName);
        UEdGraph* Graph=nullptr; int32 GraphMatches=0;
        for (UEdGraph* Candidate:AllGraphs) if (Candidate && Candidate->GetName()==GraphName) { Graph=Candidate; ++GraphMatches; }
        if (GraphMatches!=1) { Error(TEXT("Graph identity must resolve exactly once: ")+GraphName); continue; }
        const TArray<Val>* NodePatches=nullptr;
        if (!GraphPatch->TryGetArrayField(TEXT("nodes"),NodePatches) || NodePatches->IsEmpty())
        { Error(TEXT("nodes must be a nonempty array: ")+GraphName); continue; }
        for (const Val& NodeValue:*NodePatches)
        {
            if (!NodeValue.IsValid() || NodeValue->Type!=EJson::Object) { Error(TEXT("Each node patch must be an object")); continue; }
            const Obj NodePatch=NodeValue->AsObject();
            OnlyKeys(NodePatch,{TEXT("id"),TEXT("runtime_node_name"),TEXT("runtime_class"),TEXT("old"),TEXT("new")},GraphName+TEXT(".node"));
            const FString NodeName=Str(NodePatch,TEXT("runtime_node_name"));
            const FString RuntimeClass=Str(NodePatch,TEXT("runtime_class"));
            const FString Where=GraphName+TEXT(".")+NodeName;
            UEdGraphNode* Node=nullptr; int32 Matches=0;
            for (UEdGraphNode* Candidate:Graph->Nodes) if (Candidate && Candidate->GetName()==NodeName) { Node=Candidate; ++Matches; }
            if (NodeName.IsEmpty() || Matches!=1 || !Node) { Error(TEXT("Node identity must resolve exactly once: ")+Where); continue; }
            if (SeenNodes.Contains(Node)) { Error(TEXT("Duplicate node patch: ")+Where); continue; }
            SeenNodes.Add(Node);
            if (RuntimeClass.IsEmpty() || Node->GetClass()->GetPathName()!=RuntimeClass)
            { Error(TEXT("Node class mismatch: ")+Where); continue; }
            const Obj Old=Child(NodePatch,TEXT("old")),New=Child(NodePatch,TEXT("new"));
            OnlyKeys(Old,{TEXT("x"),TEXT("y")},Where+TEXT(".old"));
            OnlyKeys(New,{TEXT("x"),TEXT("y"),TEXT("width"),TEXT("height"),TEXT("text"),TEXT("color")},Where+TEXT(".new"));
            if (!Old.IsValid() || !New.IsValid()) continue;
            FPresentationEdit Edit; Edit.Node=Node;
            bool Valid=Integer(Old,TEXT("x"),Edit.OldX,Where+TEXT(".old"));
            Valid=Integer(Old,TEXT("y"),Edit.OldY,Where+TEXT(".old")) && Valid;
            Valid=Integer(New,TEXT("x"),Edit.X,Where+TEXT(".new")) && Valid;
            Valid=Integer(New,TEXT("y"),Edit.Y,Where+TEXT(".new")) && Valid;
            if (!Valid) continue;
            if (Node->NodePosX!=Edit.OldX || Node->NodePosY!=Edit.OldY)
            { Error(FString::Printf(TEXT("Old position mismatch: %s expected (%d,%d), actual (%d,%d)"),*Where,Edit.OldX,Edit.OldY,Node->NodePosX,Node->NodePosY)); continue; }
            Edit.OldWidth=Edit.Width=Node->NodeWidth; Edit.OldHeight=Edit.Height=Node->NodeHeight;
            Edit.OldText=Edit.Text=Node->NodeComment;
            Edit.bWidth=New->HasField(TEXT("width")); Edit.bHeight=New->HasField(TEXT("height"));
            Edit.bText=New->HasField(TEXT("text")); Edit.bColor=New->HasField(TEXT("color"));
            UEdGraphNode_Comment* Comment=Cast<UEdGraphNode_Comment>(Node);
            if ((Edit.bWidth || Edit.bHeight || Edit.bText || Edit.bColor) && !Comment)
            { Error(TEXT("width/height/text/color are permitted only on comment nodes: ")+Where); continue; }
            if (Comment) Edit.OldColor=Edit.Color=Comment->CommentColor;
            if (Edit.bWidth)
            {
                Valid=Integer(New,TEXT("width"),Edit.Width,Where+TEXT(".new")) && Valid;
                if (Edit.Width<=0 || Edit.Width>100000) { Error(TEXT("Comment width must be 1..100000: ")+Where); Valid=false; }
            }
            if (Edit.bHeight)
            {
                Valid=Integer(New,TEXT("height"),Edit.Height,Where+TEXT(".new")) && Valid;
                if (Edit.Height<=0 || Edit.Height>100000) { Error(TEXT("Comment height must be 1..100000: ")+Where); Valid=false; }
            }
            if (Edit.bText && (!New->TryGetStringField(TEXT("text"),Edit.Text) || Edit.Text.Len()>16384))
            { Error(TEXT("Comment text must be a string of at most 16384 characters: ")+Where); Valid=false; }
            if (Edit.bColor)
            {
                FString Color;
                if (!New->TryGetStringField(TEXT("color"),Color) || !Edit.Color.InitFromString(Color) ||
                    !FMath::IsFinite(Edit.Color.R) || !FMath::IsFinite(Edit.Color.G) || !FMath::IsFinite(Edit.Color.B) || !FMath::IsFinite(Edit.Color.A))
                { Error(TEXT("Comment color must be a finite UE string (R=...,G=...,B=...,A=...): ")+Where); Valid=false; }
            }
            Edit.bChanged=Edit.X!=Edit.OldX || Edit.Y!=Edit.OldY || Edit.Width!=Edit.OldWidth || Edit.Height!=Edit.OldHeight || Edit.Text!=Edit.OldText || Edit.Color!=Edit.OldColor;
            if (Valid) Edits.Add(Edit);
        }
    }
    if (Patch->HasField(TEXT("node_count")))
    {
        int32 Expected=0;
        if (Integer(Patch,TEXT("node_count"),Expected,TEXT("patch")) && Expected!=Edits.Num()) Error(TEXT("node_count does not match the fully validated node patch count"));
    }
    if (Edits.IsEmpty()) Error(TEXT("No valid node presentation edits"));
    if (!Errors.IsEmpty()) { Report->SetNumberField(TEXT("validated_node_count"),Edits.Num()); return Finish(); }

    // Same Inspect representation before/after, omitting only permitted positions
    // and the title generated from a comment node's editable display text.
    auto Semantic=[&]()
    {
        Obj Data=Inspect(BP);
        for (const Val& G:Array(Data,TEXT("graphs"))) for (const Val& N:Array(G->AsObject(),TEXT("nodes")))
        {
            Obj Node=N->AsObject(); Node->RemoveField(TEXT("x")); Node->RemoveField(TEXT("y"));
            UClass* NodeClass=FindObject<UClass>(nullptr,*Str(Node,TEXT("class")));
            if (NodeClass && NodeClass->IsChildOf(UEdGraphNode_Comment::StaticClass())) Node->RemoveField(TEXT("title"));
        }
        return Data;
    };
    Obj BeforeSemantic=Semantic(); const FString BeforeText=Json(BeforeSemantic);
    Report->SetObjectField(TEXT("semantic_before"),BeforeSemantic);
    int32 Changed=0; for (const FPresentationEdit& Edit:Edits) if (Edit.bChanged) ++Changed;
    Report->SetNumberField(TEXT("validated_node_count"),Edits.Num());
    Report->SetNumberField(TEXT("changed_node_count"),Changed);
    if (Changed>0)
    {
        FScopedTransaction Transaction(NSLOCTEXT("LabAuthoring","GraphPresentation","Adjust Blueprint graph presentation"));
        BP->Modify();
        for (const FPresentationEdit& Edit:Edits)
        {
            if (!Edit.bChanged) continue;
            Edit.Node->Modify();
            Edit.Node->NodePosX=Edit.X; Edit.Node->NodePosY=Edit.Y;
            if (UEdGraphNode_Comment* Comment=Cast<UEdGraphNode_Comment>(Edit.Node))
            {
                if (Edit.bWidth) Comment->NodeWidth=Edit.Width;
                if (Edit.bHeight) Comment->NodeHeight=Edit.Height;
                if (Edit.bText) Comment->NodeComment=Edit.Text;
                if (Edit.bColor) Comment->CommentColor=Edit.Color;
            }
        }
        Obj AfterSemantic=Semantic();
        const bool Same=BeforeText==Json(AfterSemantic);
        Report->SetBoolField(TEXT("semantic_unchanged"),Same);
        Report->SetObjectField(TEXT("semantic_after"),AfterSemantic);
        if (!Same)
        {
            // Restore only fields this API owns; never touch any semantic state.
            for (const FPresentationEdit& Edit:Edits)
            {
                Edit.Node->NodePosX=Edit.OldX; Edit.Node->NodePosY=Edit.OldY;
                if (UEdGraphNode_Comment* Comment=Cast<UEdGraphNode_Comment>(Edit.Node))
                { Comment->NodeWidth=Edit.OldWidth; Comment->NodeHeight=Edit.OldHeight; Comment->NodeComment=Edit.OldText; Comment->CommentColor=Edit.OldColor; }
            }
            Transaction.Cancel();
            Report->SetBoolField(TEXT("presentation_rolled_back"),true);
            Error(TEXT("Semantic Inspect changed unexpectedly; presentation changes rolled back, no compile/save performed"));
        }
        else Report->SetBoolField(TEXT("applied"),true);
    }
    else
    {
        Report->SetBoolField(TEXT("semantic_unchanged"),true);
        Report->SetObjectField(TEXT("semantic_after"),Semantic());
        Report->SetBoolField(TEXT("applied"),true);
    }
    Report->SetObjectField(TEXT("after"),Inspect(BP));
    return Finish();
}

FString ULabAuthoringLibrary::ApplySpec(const FString& JsonSpec)
{
    using namespace LabAuthoring; Obj Spec,Report=Object(); TArray<Val> Errors; UBlueprint* BP=nullptr;
    auto Finish=[&]() { Report->SetBoolField(TEXT("ok"),Errors.IsEmpty()); Report->SetArrayField(TEXT("errors"),Errors); if (BP) Report->SetObjectField(TEXT("blueprint"),Inspect(BP)); return Json(Report); };
    if (!FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(JsonSpec),Spec) || !Spec.IsValid()) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Invalid JSON object"))); return Finish(); }
    const FString Asset=Str(Spec,TEXT("asset_path")); if (!Asset.StartsWith(TEXT("/Game/")) || Asset.Contains(TEXT("."))) { Errors.Add(MakeShared<FJsonValueString>(TEXT("asset_path must be a /Game package path without object suffix"))); return Finish(); }
    const FScopedTransaction Transaction(NSLOCTEXT("LabAuthoring","ApplySpec","Author Lab Blueprint"));
    BP=LoadObject<UBlueprint>(nullptr,*Asset); const bool Existing=BP!=nullptr;
    if (Existing && !Flag(Spec,TEXT("allow_existing"))) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Asset already exists; explicit allow_existing required"))); return Finish(); }
    if (!BP)
    {
        UClass* Parent=Class(Str(Spec,TEXT("parent_class"),TEXT("/Script/Engine.Actor"))); if (!Parent) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Parent class not found"))); return Finish(); }
        UPackage* Package=CreatePackage(*Asset); BP=FKismetEditorUtilities::CreateBlueprint(Parent,Package,FName(*FPackageName::GetLongPackageAssetName(Asset)),BPTYPE_Normal,UBlueprint::StaticClass(),UBlueprintGeneratedClass::StaticClass(),FName(TEXT("LabAuthoring")));
        if (!BP) { Errors.Add(MakeShared<FJsonValueString>(TEXT("CreateBlueprint failed"))); return Finish(); } FAssetRegistryModule::AssetCreated(BP);
    }
    BP->Modify(); const UEdGraphSchema_K2* Schema=GetDefault<UEdGraphSchema_K2>();
    for (const Val& V:Array(Spec,TEXT("variables")))
    {
        Obj J=V->AsObject(); FName Name(*Str(J,TEXT("name"))); const FString Default=J->HasField(TEXT("default"))?ValueText(J->TryGetField(TEXT("default"))):TEXT("");
        if (FBlueprintEditorUtils::FindNewVariableIndex(BP,Name)==INDEX_NONE && !FBlueprintEditorUtils::AddMemberVariable(BP,Name,Type(J),Default)) Errors.Add(MakeShared<FJsonValueString>(TEXT("Cannot add variable ")+Name.ToString()));
        FBlueprintEditorUtils::SetBlueprintOnlyEditableFlag(BP,Name,!Flag(J,TEXT("instance_editable")));
        FBlueprintEditorUtils::SetBlueprintVariableCategory(BP,Name,nullptr,FText::FromString(Str(J,TEXT("category"),TEXT("Lab"))),true);
        if (J->HasField(TEXT("tooltip"))) FBlueprintEditorUtils::SetBlueprintVariableMetaData(BP,Name,nullptr,TEXT("ToolTip"),Str(J,TEXT("tooltip")));
    }
    if (!Errors.IsEmpty()) return Finish();
    for (const Val& V:Array(Spec,TEXT("components")))
    {
        Obj J=V->AsObject(); const FName Name(*Str(J,TEXT("name"))); UClass* CC=Class(Str(J,TEXT("class")));
        if (!CC || !CC->IsChildOf(UActorComponent::StaticClass()) || !BP->SimpleConstructionScript) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Invalid SCS component class: ")+Name.ToString())); continue; }
        USCS_Node* N=BP->SimpleConstructionScript->FindSCSNode(Name);
        if (!N)
        {
            N=BP->SimpleConstructionScript->CreateNode(CC,Name); const FString ParentName=Str(J,TEXT("parent")); USCS_Node* Parent=ParentName.IsEmpty()?nullptr:FindParent(BP,FName(*ParentName));
            if (Parent && Parent->GetOuter()==BP->SimpleConstructionScript) Parent->AddChildNode(N);
            else { BP->SimpleConstructionScript->AddNode(N); if (Parent) N->SetParent(Parent); else if (!ParentName.IsEmpty()) { USceneComponent* Native=nullptr; if (BP->ParentClass) for (TFieldIterator<FObjectPropertyBase> P(BP->ParentClass);P;++P) if (P->GetFName()==FName(*ParentName)) Native=Cast<USceneComponent>(P->GetObjectPropertyValue_InContainer(BP->ParentClass->GetDefaultObject())); if (Native) N->SetParent(Native); else Errors.Add(MakeShared<FJsonValueString>(TEXT("SCS parent not found: ")+ParentName)); } }
        }
        Properties(N->ComponentTemplate,Child(J,TEXT("properties")),Errors);
    }
    if (!Errors.IsEmpty()) return Finish();
    // Declare all custom functions first, so self calls can resolve through the skeleton.
    TMap<FString,UEdGraph*> Graphs;
    for (const Val& V:Array(Spec,TEXT("graphs")))
    {
        Obj J=V->AsObject(); const FString Name=Str(J,TEXT("name"),TEXT("EventGraph")); const bool Function=Str(J,TEXT("kind"),TEXT("event"))==TEXT("function"); UEdGraph* G=nullptr;
        TArray<UEdGraph*> All; BP->GetAllGraphs(All); for (UEdGraph* Candidate:All) if (Candidate->GetName()==Name) { G=Candidate; break; }
        if (G && Flag(J,TEXT("replace"))) { FBlueprintEditorUtils::RemoveGraph(BP,G); G=nullptr; }
        if (!G)
        {
            G=FBlueprintEditorUtils::CreateNewGraph(BP,FName(*Name),UEdGraph::StaticClass(),UEdGraphSchema_K2::StaticClass());
            if (Function) FBlueprintEditorUtils::AddFunctionGraph<UClass>(BP,G,true,nullptr); else FBlueprintEditorUtils::AddUbergraphPage(BP,G);
        }
        if (Flag(J,TEXT("clear"),!Existing && !Function)) { const auto Old=G->Nodes; for (UEdGraphNode* N:Old) if (!Function || (!N->IsA<UK2Node_FunctionEntry>() && !N->IsA<UK2Node_FunctionResult>())) N->DestroyNode(); }
        if (Function)
        {
            UK2Node_FunctionEntry* Entry=nullptr; UK2Node_FunctionResult* Result=nullptr;
            for (UEdGraphNode* N:G->Nodes) { if (auto E=Cast<UK2Node_FunctionEntry>(N)) Entry=E; if (auto E=Cast<UK2Node_FunctionResult>(N)) Result=E; }
            if (Entry)
            {
                Entry->SetExtraFlags(FUNC_Public|FUNC_BlueprintCallable|(Flag(J,TEXT("pure"))?FUNC_BlueprintPure:0));
                for (const Val& P:Array(J,TEXT("inputs"))) if (!Entry->FindPin(FName(*Str(P->AsObject(),TEXT("name"))))) Entry->CreateUserDefinedPin(FName(*Str(P->AsObject(),TEXT("name"))),Type(P->AsObject()),EGPD_Output);
            }
            if (!Array(J,TEXT("outputs")).IsEmpty() && !Result) { Result=NewObject<UK2Node_FunctionResult>(G); G->AddNode(Result,false,false); Result->CreateNewGuid(); Result->FunctionReference.SetSelfMember(FName(*Name)); Result->AllocateDefaultPins(); }
            if (Result) for (const Val& P:Array(J,TEXT("outputs"))) if (!Result->FindPin(FName(*Str(P->AsObject(),TEXT("name"))))) Result->CreateUserDefinedPin(FName(*Str(P->AsObject(),TEXT("name"))),Type(P->AsObject()),EGPD_Input);
        }
        Graphs.Add(Name,G);
    }
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP); FKismetEditorUtilities::CompileBlueprint(BP,EBlueprintCompileOptions::RegenerateSkeletonOnly|EBlueprintCompileOptions::SkipSave);
    for (const Val& GV:Array(Spec,TEXT("graphs")))
    {
        Obj GJ=GV->AsObject(); UEdGraph* G=Graphs.FindRef(Str(GJ,TEXT("name"),TEXT("EventGraph"))); TMap<FString,UEdGraphNode*> Nodes;
        for (const Val& NV:Array(GJ,TEXT("nodes")))
        {
            Obj J=NV->AsObject(); const FString ID=Str(J,TEXT("id")),Kind=Str(J,TEXT("kind")); UEdGraphNode* N=nullptr; bool Allocate=true;
            if (Kind==TEXT("entry") || Kind==TEXT("result")) { for (UEdGraphNode* X:G->Nodes) if ((Kind==TEXT("entry") && X->IsA<UK2Node_FunctionEntry>()) || (Kind==TEXT("result") && X->IsA<UK2Node_FunctionResult>())) { N=X; break; } Allocate=false; }
            else if (Kind==TEXT("call") || Kind==TEXT("call_parent"))
            {
                UClass* Owner=Str(J,TEXT("class")).IsEmpty()?BP->SkeletonGeneratedClass.Get():Class(Str(J,TEXT("class"))); UFunction* F=Owner?Owner->FindFunctionByName(FName(*Str(J,TEXT("function")))):nullptr;
                if (!F) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Function not found: ")+ID+TEXT(" / ")+Str(J,TEXT("function")))); continue; }
                UK2Node_CallFunction* C=Kind==TEXT("call_parent")?NewObject<UK2Node_CallParentFunction>(G):NewObject<UK2Node_CallFunction>(G); C->SetFromFunction(F); if (Str(J,TEXT("class")).IsEmpty()) C->FunctionReference.SetSelfMember(F->GetFName()); N=C;
            }
            else if (Kind==TEXT("event"))
            {
                UClass* Owner=Class(Str(J,TEXT("class"),TEXT("/Script/Engine.Actor"))); const FName F(*Str(J,TEXT("function")));
                if (!Owner || !Owner->FindFunctionByName(F)) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Event signature not found: ")+ID)); continue; }
                auto E=NewObject<UK2Node_Event>(G); E->EventReference.SetExternalMember(F,Owner); E->bOverrideFunction=true; N=E;
            }
            else if (Kind==TEXT("custom_event")) { auto E=NewObject<UK2Node_CustomEvent>(G); E->CustomFunctionName=FName(*Str(J,TEXT("name"),ID)); N=E; }
            else if (Kind==TEXT("get") || Kind==TEXT("set"))
            {
                UK2Node_Variable* Var=Kind==TEXT("get")?static_cast<UK2Node_Variable*>(NewObject<UK2Node_VariableGet>(G)):static_cast<UK2Node_Variable*>(NewObject<UK2Node_VariableSet>(G));
                const FString Owner=Str(J,TEXT("class")); if (Owner.IsEmpty()) Var->VariableReference.SetSelfMember(FName(*Str(J,TEXT("variable")))); else Var->VariableReference.SetExternalMember(FName(*Str(J,TEXT("variable"))),Class(Owner)); N=Var;
            }
            else if (Kind==TEXT("branch")) N=NewObject<UK2Node_IfThenElse>(G);
            else if (Kind==TEXT("sequence")) N=NewObject<UK2Node_ExecutionSequence>(G);
            else if (Kind==TEXT("self")) N=NewObject<UK2Node_Self>(G);
            else if (Kind==TEXT("comment")) { auto C=NewObject<UEdGraphNode_Comment>(G); C->NodeComment=Str(J,TEXT("text")); C->NodeWidth=Int(J,TEXT("width"),1000); C->NodeHeight=Int(J,TEXT("height"),400); C->CommentColor.InitFromString(Str(J,TEXT("color"),TEXT("(R=0.06,G=0.12,B=0.20,A=1)"))); N=C; }
            if (!N) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Unsupported or missing node: ")+ID+TEXT(" kind=")+Kind)); continue; }
            if (Allocate) { G->AddNode(N,false,false); N->CreateNewGuid(); N->PostPlacedNewNode(); N->AllocateDefaultPins(); }
            // PostPlacedNewNode initializes comment text; apply authored values afterwards.
            if (auto C=Cast<UEdGraphNode_Comment>(N)) { C->NodeComment=Str(J,TEXT("text")); C->NodeWidth=Int(J,TEXT("width"),1000); C->NodeHeight=Int(J,TEXT("height"),400); C->CommentColor.InitFromString(Str(J,TEXT("color"),TEXT("(R=0.06,G=0.12,B=0.20,A=1)"))); }
            N->NodePosX=Int(J,TEXT("x")); N->NodePosY=Int(J,TEXT("y"));
            if (auto E=Cast<UK2Node_CustomEvent>(N)) for (const Val& PV:Array(J,TEXT("inputs"))) E->CreateUserDefinedPin(FName(*Str(PV->AsObject(),TEXT("name"))),Type(PV->AsObject()),EGPD_Output);
            if (auto S=Cast<UK2Node_ExecutionSequence>(N)) for (int32 I=2;I<Int(J,TEXT("outputs"),2);++I) S->AddInputPin();
            for (const Val& PV:Array(J,TEXT("split_pins"))) if (UEdGraphPin* P=Pin(N,PV->AsString(),EGPD_Input)) Schema->SplitPin(P,false);
            Nodes.Add(ID,N);
        }
        // Create links before defaults, so wildcard pins have their concrete type.
        for (const Val& LV:Array(GJ,TEXT("links")))
        {
            const auto& L=LV->AsArray(); if (L.Num()!=4) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Link must have four strings"))); continue; }
            UEdGraphPin* From=Pin(Nodes.FindRef(L[0]->AsString()),L[1]->AsString(),EGPD_Output); UEdGraphPin* To=Pin(Nodes.FindRef(L[2]->AsString()),L[3]->AsString(),EGPD_Input);
            if (!From || !To || !Schema->TryCreateConnection(From,To)) Errors.Add(MakeShared<FJsonValueString>(TEXT("Cannot link ")+L[0]->AsString()+TEXT(".")+L[1]->AsString()+TEXT(" -> ")+L[2]->AsString()+TEXT(".")+L[3]->AsString()));
        }
        for (const Val& NV:Array(GJ,TEXT("nodes")))
        {
            Obj J=NV->AsObject(); UEdGraphNode* N=Nodes.FindRef(Str(J,TEXT("id"))); Obj D=Child(J,TEXT("defaults")); if (!N || !D.IsValid()) continue;
            for (const auto& KV:D->Values)
            {
                UEdGraphPin* P=Pin(N,KV.Key,EGPD_Input); if (!P) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Default pin not found: ")+Str(J,TEXT("id"))+TEXT(".")+KV.Key)); continue; }
                if (KV.Value->Type==EJson::Object && KV.Value->AsObject()->HasField(TEXT("object"))) { const FString Path=Str(KV.Value->AsObject(),TEXT("object")); UObject* O=LoadObject<UObject>(nullptr,*Path); if (!O) Errors.Add(MakeShared<FJsonValueString>(TEXT("Default object not found: ")+Path)); else Schema->TrySetDefaultObject(*P,O); }
                else Schema->TrySetDefaultValue(*P,ValueText(KV.Value));
            }
        }
    }
    if (!Errors.IsEmpty()) return Finish();
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
    if (Flag(Spec,TEXT("compile"),true))
    {
        FCompilerResultsLog Results; FKismetEditorUtilities::CompileBlueprint(BP,EBlueprintCompileOptions::SkipSave,&Results); Report->SetNumberField(TEXT("compile_errors"),Results.NumErrors); Report->SetNumberField(TEXT("compile_warnings"),Results.NumWarnings); TArray<Val> Messages; for (const auto& M:Results.Messages) Messages.Add(MakeShared<FJsonValueString>(M->ToText().ToString())); Report->SetArrayField(TEXT("compile_messages"),Messages);
        if (Results.NumErrors>0 || BP->Status==BS_Error) { Errors.Add(MakeShared<FJsonValueString>(TEXT("Blueprint compile failed"))); return Finish(); }
    }
    if (BP->GeneratedClass) Properties(BP->GeneratedClass->GetDefaultObject(),Child(Spec,TEXT("defaults")),Errors);
    BP->MarkPackageDirty();
    if (Errors.IsEmpty() && Flag(Spec,TEXT("save"))) { TArray<UPackage*> P{BP->GetOutermost()}; if (!UEditorLoadingAndSavingUtils::SavePackages(P,true)) Errors.Add(MakeShared<FJsonValueString>(TEXT("Selective package save failed"))); else Report->SetBoolField(TEXT("saved"),true); }
    return Finish();
}
