# Add project specific ProGuard rules here.
# By default, the flags in this file are appended to flags specified
# in Android SDK tools.

# Retrofit and OkHttp
-keepattributes Signature
-keepattributes Exceptions
-keepattributes InnerClasses
-keepattributes Annotation
-keepattributes *Annotation*
-keepattributes SourceFile,LineNumberTable
-keep class retrofit2.** { *; }
-keep class okhttp3.** { *; }
-keep class okio.** { *; }
-keep class com.google.gson.** { *; }
-keep class com.haven.ai.** { *; }

# Gson
-keepattributes Signature
-keepattributes *Annotation*
-dontwarn java.awt.**
-dontwarn javax.**
-dontwarn org.**
