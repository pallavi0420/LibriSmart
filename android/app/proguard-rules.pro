# LibriSmart ProGuard & R8 Optimization Rules for Google Play Store Release

# Kotlin Serialization & DTO Data Preservation
-keepattributes *Annotation*, InnerClasses, Signature, EnclosingMethod
-dontnote kotlinx.serialization.SerializationKt
-keepclassmembers class * {
    @kotlinx.serialization.Serializable <fields>;
}
-keepclassmembers class * {
    companion object;
}
-keepclasseswithmembers class * {
    @kotlinx.serialization.Serializable <init>(...);
}
-keep class com.librismart.app.data.remote.dto.** { *; }

# Retrofit 2 & OkHttp Networking
-dontnote retrofit2.Platform
-dontwarn retrofit2.Platform$Java8
-keep class retrofit2.** { *; }
-keepclasseswithmembers interface * {
    @retrofit2.http.* <methods>;
}
-dontwarn okhttp3.**
-dontwarn okio.**

# Room Database & SQLite
-keep class * extends androidx.room.RoomDatabase
-keep class com.librismart.app.data.local.** { *; }
-dontwarn androidx.room.paging.**

# CameraX & ML Kit Vision Barcode Scanning
-keep class com.google.mlkit.vision.barcode.** { *; }
-keep class com.google.mlkit.vision.common.** { *; }
-dontwarn androidx.camera.core.**
-dontwarn androidx.camera.camera2.**
-dontwarn androidx.camera.lifecycle.**
-dontwarn androidx.camera.view.**

# Kotlin Coroutines
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
-dontwarn kotlinx.coroutines.**

# Coil Image Loading
-keep class coil.** { *; }
-dontwarn coil.**
