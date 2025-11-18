# SMARTII Android App - Full Device Control

## Architecture Overview

**Technology Stack:**
- **Language:** Kotlin
- **UI:** Jetpack Compose (modern declarative UI)
- **Backend:** Existing Python FastAPI (localhost:8000)
- **Communication:** WebSocket + HTTP REST
- **Wake Word:** Porcupine Android SDK
- **Speech:** Android Speech Recognition API
- **TTS:** Android TextToSpeech API

## Core Features

### 1. Background Service (Always-On)
- Foreground Service with notification
- Wake word detection running 24/7
- Low battery consumption with optimized audio processing
- Auto-restart on device reboot

### 2. Device Control APIs

#### **Contacts Integration**
```kotlin
// ContactsManager.kt
class ContactsManager(private val context: Context) {
    
    fun searchContact(name: String): Contact? {
        val cursor = context.contentResolver.query(
            ContactsContract.Contacts.CONTENT_URI,
            null,
            "${ContactsContract.Contacts.DISPLAY_NAME} LIKE ?",
            arrayOf("%$name%"),
            null
        )
        // Parse cursor and return Contact
    }
    
    fun getAllContacts(): List<Contact> {
        // Query all contacts
    }
    
    fun getPhoneNumbers(contactId: String): List<String> {
        // Get phone numbers for contact
    }
}
```

**Permissions Required:**
- `READ_CONTACTS`

#### **SMS Integration**
```kotlin
// SmsManager.kt
class SmsManager(private val context: Context) {
    
    fun sendSms(phoneNumber: String, message: String) {
        val smsManager = android.telephony.SmsManager.getDefault()
        smsManager.sendTextMessage(
            phoneNumber,
            null,
            message,
            null,
            null
        )
    }
    
    fun getRecentMessages(limit: Int = 10): List<SmsMessage> {
        val cursor = context.contentResolver.query(
            Uri.parse("content://sms/inbox"),
            null, null, null,
            "date DESC LIMIT $limit"
        )
        // Parse cursor and return messages
    }
}
```

**Permissions Required:**
- `SEND_SMS`
- `READ_SMS`

#### **Phone Calls**
```kotlin
// CallManager.kt
class CallManager(private val context: Context) {
    
    fun makeCall(phoneNumber: String) {
        val intent = Intent(Intent.ACTION_CALL).apply {
            data = Uri.parse("tel:$phoneNumber")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        context.startActivity(intent)
    }
    
    fun getCallHistory(limit: Int = 10): List<CallLog> {
        val cursor = context.contentResolver.query(
            CallLog.Calls.CONTENT_URI,
            null, null, null,
            "${CallLog.Calls.DATE} DESC LIMIT $limit"
        )
        // Parse cursor and return call logs
    }
}
```

**Permissions Required:**
- `CALL_PHONE`
- `READ_CALL_LOG`

#### **App Launching**
```kotlin
// AppLauncher.kt
class AppLauncher(private val context: Context) {
    
    fun openApp(packageName: String) {
        val intent = context.packageManager.getLaunchIntentForPackage(packageName)
        intent?.let {
            it.flags = Intent.FLAG_ACTIVITY_NEW_TASK
            context.startActivity(it)
        }
    }
    
    fun openAppByName(appName: String) {
        val apps = getInstalledApps()
        val app = apps.find { it.name.contains(appName, ignoreCase = true) }
        app?.let { openApp(it.packageName) }
    }
    
    fun getInstalledApps(): List<AppInfo> {
        val pm = context.packageManager
        return pm.getInstalledApplications(PackageManager.GET_META_DATA)
            .filter { (it.flags and ApplicationInfo.FLAG_SYSTEM) == 0 }
            .map { AppInfo(it.loadLabel(pm).toString(), it.packageName) }
    }
    
    // Special intents for common apps
    fun openWhatsApp() {
        openApp("com.whatsapp")
    }
    
    fun openWhatsAppChat(phoneNumber: String, message: String? = null) {
        val intent = Intent(Intent.ACTION_VIEW).apply {
            data = Uri.parse("https://wa.me/$phoneNumber${message?.let { "?text=${Uri.encode(it)}" } ?: ""}")
            setPackage("com.whatsapp")
        }
        context.startActivity(intent)
    }
}
```

#### **Settings Control**
```kotlin
// SettingsManager.kt
class SettingsManager(private val context: Context) {
    
    fun openWifiSettings() {
        context.startActivity(Intent(Settings.ACTION_WIFI_SETTINGS))
    }
    
    fun openBluetoothSettings() {
        context.startActivity(Intent(Settings.ACTION_BLUETOOTH_SETTINGS))
    }
    
    fun setBrightness(level: Int) {
        Settings.System.putInt(
            context.contentResolver,
            Settings.System.SCREEN_BRIGHTNESS,
            level.coerceIn(0, 255)
        )
    }
    
    fun setVolume(streamType: Int, level: Int) {
        val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
        audioManager.setStreamVolume(streamType, level, 0)
    }
}
```

**Permissions Required:**
- `WRITE_SETTINGS`
- `MODIFY_AUDIO_SETTINGS`

### 3. Backend Communication

```kotlin
// BackendClient.kt
class BackendClient {
    private val baseUrl = "http://192.168.1.100:8000" // WiFi IP
    private var webSocket: WebSocket? = null
    
    suspend fun sendMessage(text: String): String {
        return withContext(Dispatchers.IO) {
            val client = OkHttpClient()
            val request = Request.Builder()
                .url("$baseUrl/api/conversation")
                .post(jsonBody {
                    "message" to text
                    "user_id" to "android_user"
                })
                .build()
            
            val response = client.newCall(request).execute()
            response.body?.string() ?: ""
        }
    }
    
    fun connectWebSocket(listener: WebSocketListener) {
        val client = OkHttpClient()
        val request = Request.Builder()
            .url("ws://192.168.1.100:8000/ws/android_user")
            .build()
        
        webSocket = client.newWebSocket(request, listener)
    }
}
```

### 4. Project Structure

```
android-native/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/smartii/
│   │   │   │   ├── MainActivity.kt
│   │   │   │   ├── service/
│   │   │   │   │   ├── SmartiiService.kt (Foreground Service)
│   │   │   │   │   ├── WakeWordDetector.kt
│   │   │   │   ├── managers/
│   │   │   │   │   ├── ContactsManager.kt
│   │   │   │   │   ├── SmsManager.kt
│   │   │   │   │   ├── CallManager.kt
│   │   │   │   │   ├── AppLauncher.kt
│   │   │   │   │   ├── SettingsManager.kt
│   │   │   │   ├── network/
│   │   │   │   │   ├── BackendClient.kt
│   │   │   │   ├── ui/
│   │   │   │   │   ├── screens/
│   │   │   │   │   │   ├── MainScreen.kt
│   │   │   │   │   │   ├── SettingsScreen.kt
│   │   │   │   │   ├── components/
│   │   │   │   │       ├── VoiceVisualizer.kt
│   │   │   ├── AndroidManifest.xml
│   │   │   ├── res/
│   │   │       ├── values/
│   │   │       │   ├── strings.xml
│   │   │       ├── drawable/
│   │   │       ├── mipmap/
│   ├── build.gradle
├── build.gradle
├── settings.gradle
├── gradle.properties
└── README.md
```

## Setup Instructions

### 1. Create Android Studio Project
```bash
# In Android Studio:
# File > New > New Project
# Select "Empty Compose Activity"
# Name: SMARTII
# Package: com.smartii
# Minimum SDK: API 26 (Android 8.0)
```

### 2. Add Dependencies (build.gradle)
```gradle
dependencies {
    // Core Android
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.lifecycle:lifecycle-runtime-ktx:2.6.2'
    
    // Compose UI
    implementation 'androidx.activity:activity-compose:1.8.0'
    implementation 'androidx.compose.ui:ui:1.5.4'
    implementation 'androidx.compose.material3:material3:1.1.2'
    
    // Networking
    implementation 'com.squareup.okhttp3:okhttp:4.12.0'
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    
    // Porcupine Wake Word
    implementation 'ai.picovoice:porcupine-android:3.0.0'
    
    // Permissions
    implementation 'com.google.accompanist:accompanist-permissions:0.32.0'
    
    // Coroutines
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3'
}
```

### 3. Add Permissions (AndroidManifest.xml)
```xml
<manifest>
    <!-- Audio -->
    <uses-permission android:name="android.permission.RECORD_AUDIO" />
    <uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />
    
    <!-- Contacts -->
    <uses-permission android:name="android.permission.READ_CONTACTS" />
    
    <!-- SMS -->
    <uses-permission android:name="android.permission.SEND_SMS" />
    <uses-permission android:name="android.permission.READ_SMS" />
    
    <!-- Phone -->
    <uses-permission android:name="android.permission.CALL_PHONE" />
    <uses-permission android:name="android.permission.READ_CALL_LOG" />
    
    <!-- Settings -->
    <uses-permission android:name="android.permission.WRITE_SETTINGS" />
    
    <!-- Network -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    
    <!-- Foreground Service -->
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MICROPHONE" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    
    <!-- Boot -->
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />
    
    <application>
        <!-- Service -->
        <service
            android:name=".service.SmartiiService"
            android:enabled="true"
            android:exported="false"
            android:foregroundServiceType="microphone" />
        
        <!-- Boot Receiver -->
        <receiver
            android:name=".receivers.BootReceiver"
            android:enabled="true"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED" />
            </intent-filter>
        </receiver>
    </application>
</manifest>
```

## Next Steps

1. **Create base Android project** in Android Studio
2. **Implement SmartiiService** - foreground service with wake word
3. **Add device control managers** - contacts, SMS, calls, apps
4. **Connect to backend** - HTTP + WebSocket
5. **Build UI** - Compose screens with voice visualizer
6. **Test permissions** - runtime permission flow
7. **Deploy APK** - install on physical device

## Testing on Same Network

Backend must be accessible from Android:
```bash
# On Windows, get IP address:
ipconfig

# Update backend app.py to allow external connections:
# uvicorn app:app --host 0.0.0.0 --port 8000

# In Android app, use:
# baseUrl = "http://192.168.1.XXX:8000"
```

## WhatsApp Business API Setup

For programmatic message sending (without opening app):

1. Go to https://developers.facebook.com
2. Create Meta Business Account
3. Create new app, add WhatsApp product
4. Get access token + phone number ID
5. Set environment variables on Windows:
   ```powershell
   $env:WHATSAPP_API_KEY = "your_access_token"
   $env:WHATSAPP_PHONE_ID = "your_phone_id"
   ```
6. Restart backend

First 1000 conversations/month are FREE!

## Limitations

- **Network Required:** Android app needs WiFi/mobile data to reach backend
- **Same Network:** Backend must be on same network OR use ngrok/cloudflare tunnel
- **WhatsApp API:** Requires business verification for production use
- **Contacts/SMS/Calls:** Dangerous permissions - may require Play Store approval

## Alternative: Desktop-Only WhatsApp

If not using Android app, Windows desktop can:
- ✅ Open WhatsApp Desktop app
- ✅ Pre-fill messages with deep links
- ❌ Cannot send automatically (user must click)

Already implemented in `windows_control.py`!
