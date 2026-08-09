from pathlib import Path

# Root project folder
ROOT = Path("Kotlin")

# Files to create
files = [
    "settings.gradle.kts",
    "build.gradle.kts",
    "gradle.properties",

    "app/build.gradle.kts",
    "app/proguard-rules.pro",

    "app/src/main/AndroidManifest.xml",

    "app/src/main/res/values/strings.xml",
    "app/src/main/res/values/themes.xml",

    "app/src/main/res/xml/network_security_config.xml",

    "app/src/main/java/com/negotiateai/app/MainActivity.kt",
    "app/src/main/java/com/negotiateai/app/NegotiateAiApp.kt",

    "app/src/main/java/com/negotiateai/app/core/theme/Color.kt",
    "app/src/main/java/com/negotiateai/app/core/theme/Type.kt",
    "app/src/main/java/com/negotiateai/app/core/theme/Theme.kt",
    "app/src/main/java/com/negotiateai/app/core/theme/Shape.kt",

    "app/src/main/java/com/negotiateai/app/core/network/ApiClient.kt",
    "app/src/main/java/com/negotiateai/app/core/network/AuthInterceptor.kt",
    "app/src/main/java/com/negotiateai/app/core/network/TokenManager.kt",

    "app/src/main/java/com/negotiateai/app/core/ui/Components.kt",

    "app/src/main/java/com/negotiateai/app/data/model/Models.kt",
    "app/src/main/java/com/negotiateai/app/data/api/ApiService.kt",

    "app/src/main/java/com/negotiateai/app/data/repository/AuthRepository.kt",
    "app/src/main/java/com/negotiateai/app/data/repository/CaseRepository.kt",
    "app/src/main/java/com/negotiateai/app/data/repository/NegotiationRepository.kt",

    "app/src/main/java/com/negotiateai/app/feature/auth/AuthViewModel.kt",
    "app/src/main/java/com/negotiateai/app/feature/auth/AuthScreen.kt",

    "app/src/main/java/com/negotiateai/app/feature/dashboard/DashboardViewModel.kt",
    "app/src/main/java/com/negotiateai/app/feature/dashboard/CaseDashboardScreen.kt",

    "app/src/main/java/com/negotiateai/app/feature/case/CaseDetailScreen.kt",
    "app/src/main/java/com/negotiateai/app/feature/case/CaseViewModel.kt",
    "app/src/main/java/com/negotiateai/app/feature/case/CreateCaseScreen.kt",

    "app/src/main/java/com/negotiateai/app/feature/negotiation/NegotiationViewModel.kt",
    "app/src/main/java/com/negotiateai/app/feature/negotiation/NegotiationChatScreen.kt",

    "app/src/main/java/com/negotiateai/app/feature/prediction/PredictionViewModel.kt",
    "app/src/main/java/com/negotiateai/app/feature/prediction/PredictionScreen.kt",

    "app/src/main/java/com/negotiateai/app/feature/settlement/SettlementScreen.kt",

    "app/src/main/java/com/negotiateai/app/navigation/NavGraph.kt",
    "app/src/main/java/com/negotiateai/app/navigation/AppNavigation.kt",
]

# Create folders and files
for file in files:
    path = ROOT / file
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.touch()
        print(f"Created: {path}")
    else:
        print(f"Exists:  {path}")

print("\n✅ Android project structure created successfully!")