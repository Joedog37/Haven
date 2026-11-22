# Haven AI — Android App

This Android app connects to your **Haven AI server** over your **Tailscale network**, so you can chat with your AI from your phone anywhere.

---

## Prerequisites

1. **Android Studio** (latest version) — download from https://developer.android.com/studio
2. **Android SDK** (included with Android Studio)
3. **JDK 17** (included with Android Studio)
4. Your **Haven AI server** running on your PC
5. **Tailscale** installed and running on both your PC and Android phone

---

## How to Build

### Step 1: Open the Project

1. Open **Android Studio**
2. Click **File → New → Import Project**
3. Navigate to `G:\Haven\Android` and select it
4. Click **OK** — Android Studio will sync Gradle automatically

### Step 2: Generate App Icon (one-time)

1. Right-click the `app` folder in the Project view
2. Go to **New → Image Asset**
3. Set:
   - **Asset Type**: Icon
   - **Clip**: Action Bar and Tab Icon
   - **Foreground Path**: Choose any image or use the default
   - **Name**: `ic_launcher`
4. Click **Next** → **Finish**

### Step 3: Build and Run

**Option A — Run on your phone (recommended):**
1. Enable **Developer Options** on your Android phone:
   - Go to **Settings → About phone**
   - Tap **Build number** 7 times
2. Enable **USB Debugging**:
   - Go to **Settings → Developer options → USB debugging** (ON)
3. Install **Tailscale** on your phone from the Play Store
4. Connect your phone to your PC via USB
5. In Android Studio, select your device from the device dropdown
6. Click the **Run** button (green play icon)

**Option B — Run on an emulator:**
1. Open **Device Manager** in Android Studio (Tools → Device Manager)
2. Click **Create Device** and pick any phone (e.g., Pixel 6)
3. Download a system image if prompted
4. Click **Finish** to create the emulator
5. Select the emulator and click **Run**

---

## How It Works

The app connects to your Haven server using your **Tailscale IP address**:

```
http://100.102.81.112:8000
```

This is your PC's Tailscale IP (`joseph-build`). As long as:
- ✅ Your PC is **on and awake**
- ✅ **Haven** is running (`Pc/main.py`)
- ✅ **Tailscale** is running on both devices

...the app will connect and you can chat with Haven.

---

## Features

| Feature | Status |
|---------|--------|
| Chat with Haven AI | ✅ Working |
| Server status indicators | ✅ Working |
| Dark JARVIS-style theme | ✅ Working |
| Typing indicator | ✅ Working |
| Message history scroll | ✅ Working |
| TTS audio playback | ⏳ Planned |
| Voice input (STT) | ⏳ Planned |
| Game controls | ⏳ Planned |

---

## Changing the Server IP

If your Tailscale IP changes, edit `RetrofitClient.kt`:

```kotlin
const val BASE_URL = "http://YOUR_NEW_IP:8000/"
```

Then rebuild the app.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot connect to Haven" | Make sure Haven is running on your PC and Tailscale is active on both devices |
| "Network error" | Check that your phone can reach `100.102.81.112:8000` — try opening it in your phone's browser first |
| App crashes on startup | Check Logcat in Android Studio for error details |
| Gradle sync fails | Make sure you have internet access — Gradle needs to download dependencies |
| Build fails | Clean project: **Build → Clean Project**, then **Build → Rebuild Project** |

---

## Project Structure

```
Android/
├── app/
│   ├── src/main/
│   │   ├── java/com/haven/ai/
│   │   │   ├── MainActivity.kt       # Main chat screen
│   │   │   ├── ChatAdapter.kt        # RecyclerView adapter
│   │   │   ├── HavenApi.kt           # API interface + data models
│   │   │   └── RetrofitClient.kt     # Network client (Tailscale IP)
│   │   ├── res/
│   │   │   ├── layout/
│   │   │   │   ├── activity_main.xml # Chat UI layout
│   │   │   │   └── item_message.xml  # Message bubble layout
│   │   │   ├── values/
│   │   │   │   ├── strings.xml       # App strings
│   │   │   │   ├── colors.xml        # Color definitions
│   │   │   │   └── themes.xml        # Dark theme
│   │   │   └── xml/
│   │   │       └── network_security_config.xml
│   │   └── AndroidManifest.xml
│   ├── build.gradle.kts              # App-level Gradle config
│   └── proguard-rules.pro
├── build.gradle.kts                  # Project-level Gradle config
├── settings.gradle.kts
├── gradle.properties
└── gradle/wrapper/
    └── gradle-wrapper.properties
```

---

## Next Steps

Once the basic chat works, you can add:
- **TTS audio playback** — play Haven's voice responses
- **Voice input** — speak to Haven via microphone
- **Game controls** — play DnD and Oregon Trail from your phone
- **Settings screen** — change server URL, voice, theme
- **Push notifications** — get alerts when Haven has updates
