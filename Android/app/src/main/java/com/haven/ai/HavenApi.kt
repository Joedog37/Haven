@file:Suppress("unused")

package com.haven.ai

import com.google.gson.annotations.SerializedName
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

// Request/Response models
data class MessageRequest(val text: String)

data class MessageResponse(
    val reply: String,
    @SerializedName("audio_url")
    val audioUrl: String? = null,
)

data class StatusResponse(
    val status: String,
    @SerializedName("model_loaded")
    val modelLoaded: Boolean,
    @SerializedName("memory_loaded")
    val memoryLoaded: Boolean,
    @SerializedName("tts_loaded")
    val ttsLoaded: Boolean,
    @SerializedName("stt_loaded")
    val sttLoaded: Boolean,
    @SerializedName("tts_voice")
    val ttsVoice: String? = null,
    @SerializedName("web_search_available")
    val webSearchAvailable: Boolean = false,
    @SerializedName("agent_tools_loaded")
    val agentToolsLoaded: Boolean = false,
    @SerializedName("game_engine_loaded")
    val gameEngineLoaded: Boolean = false,
)

data class SystemInfoResponse(
    @SerializedName("cpu_percent")
    val cpuPercent: Double,
    @SerializedName("memory_percent")
    val memoryPercent: Double,
    @SerializedName("memory_total_gb")
    val memoryTotalGb: Double,
    @SerializedName("memory_available_gb")
    val memoryAvailableGb: Double,
    @SerializedName("disk_percent")
    val diskPercent: Double,
    @SerializedName("disk_total_gb")
    val diskTotalGb: Double,
    @SerializedName("disk_free_gb")
    val diskFreeGb: Double,
)

data class TTSRequest(val text: String, val voice: String = "af_heart", val speed: Float = 1.0f)

// Retrofit API interface
interface HavenApi {

    @GET("/api/status")
    suspend fun getStatus(): StatusResponse

    @POST("/api/message")
    suspend fun sendMessage(@Body request: MessageRequest): MessageResponse

    @GET("/api/system")
    suspend fun getSystemInfo(): SystemInfoResponse

    @POST("/api/voice/tts")
    suspend fun generateTTS(@Body request: TTSRequest): Response<ResponseBody>

    @GET("/api/voice/voices")
    suspend fun getVoices(): Map<String, Any>

    @GET("/api/memory/stats")
    suspend fun getMemoryStats(): Map<String, Any>

    @GET("/api/tools/status")
    suspend fun getToolsStatus(): Map<String, Any>

    @GET("/api/games/status")
    suspend fun getGamesStatus(): Map<String, Any>
}
