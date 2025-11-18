# Android Native Services

## Purpose
Deep Android OS integration for SMARTII mobile app.

## Why Kotlin/Java?
- **Native APIs**: Full access to Android system services
- **Performance**: Native background processing
- **Integration**: Contacts, calendar, notifications, sensors
- **Lifecycle**: Proper handling of Android app lifecycle

## Features
- Background voice processing (foreground service)
- System integration (contacts, calendar, SMS)
- Hardware access (sensors, camera, Bluetooth)
- Notification management
- Home screen widgets
- Google Assistant integration

## Architecture
```
android-native/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/smartii/
│   │   │   │   ├── VoiceService.kt        # Background voice
│   │   │   │   ├── ContactsManager.kt     # Contacts access
│   │   │   │   ├── NotificationManager.kt # Notifications
│   │   │   │   └── SensorManager.kt       # Sensors
│   │   │   ├── AndroidManifest.xml
│   │   │   └── res/                       # Resources
│   │   └── test/                          # Unit tests
│   └── build.gradle
├── build.gradle
└── settings.gradle
```

## Services

### 1. Voice Service (Foreground)
```kotlin
class SmartiiVoiceService : Service() {
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // Always-listening voice processing
        startForeground(NOTIFICATION_ID, notification)
        startVoiceCapture()
        return START_STICKY
    }
}
```

### 2. Contacts Integration
```kotlin
class ContactsManager(context: Context) {
    fun getAllContacts(): List<Contact>
    fun searchContact(name: String): Contact?
    fun callContact(phoneNumber: String)
    fun sendSMS(phoneNumber: String, message: String)
}
```

### 3. System Integration
- **Calendar**: Read/write events, reminders
- **Notifications**: Display, manage, reply
- **Sensors**: Accelerometer, GPS, proximity
- **Camera**: Capture photos, scan QR codes
- **Bluetooth**: Connect to devices

## Permissions
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
<uses-permission android:name="android.permission.READ_CONTACTS" />
<uses-permission android:name="android.permission.WRITE_CONTACTS" />
<uses-permission android:name="android.permission.SEND_SMS" />
<uses-permission android:name="android.permission.READ_CALENDAR" />
<uses-permission android:name="android.permission.WRITE_CALENDAR" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.BLUETOOTH" />
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
```

## Communication with Backend
```kotlin
// WebSocket connection to Python backend
class BackendClient(private val url: String) {
    private val client = OkHttpClient()
    
    fun connect() {
        val request = Request.Builder().url(url).build()
        val ws = client.newWebSocket(request, listener)
    }
    
    fun sendVoiceCommand(audio: ByteArray) {
        ws.send(audio.toBase64())
    }
}
```

## Development

### Prerequisites
- Android Studio Arctic Fox or later
- JDK 11+
- Android SDK 21+ (Lollipop)

### Build
```bash
./gradlew assembleDebug
```

### Run
```bash
./gradlew installDebug
adb shell am start -n com.smartii/.MainActivity
```

### Test
```bash
./gradlew test
```

## Status
⏳ **Planned** - Architecture defined, implementation pending
