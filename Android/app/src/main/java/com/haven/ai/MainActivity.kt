package com.haven.ai

import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.media.MediaPlayer
import android.os.Bundle
import android.speech.RecognizerIntent
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.EditorInfo
import android.widget.EditText
import android.widget.FrameLayout
import android.widget.ImageButton
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.updatePadding
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.floatingactionbutton.FloatingActionButton
import com.google.android.material.snackbar.Snackbar
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.HttpException
import java.io.File
import java.io.FileOutputStream
import java.io.IOException

class MainActivity : AppCompatActivity() {

    private lateinit var chatAdapter: ChatAdapter
    private lateinit var api: HavenApi

    // Views
    private lateinit var rootLayout: LinearLayout
    private lateinit var recyclerView: RecyclerView
    private lateinit var editText: EditText
    private lateinit var btnSend: FloatingActionButton
    private lateinit var btnMic: ImageButton
    private lateinit var btnVoiceToggle: ImageButton
    private lateinit var btnToggleStatus: ImageButton
    private lateinit var btnModes: ImageButton
    private lateinit var toolbar: MaterialToolbar
    private lateinit var statusBar: LinearLayout
    private lateinit var statusModel: TextView
    private lateinit var statusMemory: TextView
    private lateinit var statusTTS: TextView
    private lateinit var statusConnection: TextView
    private lateinit var inputArea: LinearLayout

    // State
    private var isVoiceEnabled = true
    private var mediaPlayer: MediaPlayer? = null

    // Speech-to-text launcher
    private val speechLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK && result.data != null) {
            val spokenText = result.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull()
            if (!spokenText.isNullOrBlank()) {
                val current = editText.text?.toString()?.trim().orEmpty()
                val updated = if (current.isEmpty()) spokenText else "$current $spokenText"
                editText.setText(updated)
                editText.setSelection(updated.length)
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)

        // Find views
        rootLayout = findViewById(R.id.rootLayout)
        toolbar = findViewById(R.id.toolbar)
        statusBar = findViewById(R.id.statusBar)
        recyclerView = findViewById(R.id.recyclerView)
        inputArea = findViewById(R.id.inputArea)
        editText = findViewById(R.id.editText)
        btnSend = findViewById(R.id.btnSend)
        btnMic = findViewById(R.id.btnMic)
        btnVoiceToggle = findViewById(R.id.btnVoiceToggle)
        btnToggleStatus = findViewById(R.id.btnToggleStatus)
        btnModes = findViewById(R.id.btnModes)
        statusModel = findViewById(R.id.statusModel)
        statusMemory = findViewById(R.id.statusMemory)
        statusTTS = findViewById(R.id.statusTTS)
        statusConnection = findViewById(R.id.statusConnection)

        // Handle window insets so text box sits above navigation bar & keyboard
        ViewCompat.setOnApplyWindowInsetsListener(rootLayout) { _, insets ->
            val statusInsets = insets.getInsets(WindowInsetsCompat.Type.statusBars())
            val navInsets = insets.getInsets(WindowInsetsCompat.Type.navigationBars())
            val imeInsets = insets.getInsets(WindowInsetsCompat.Type.ime())

            // Toolbar padding for status bar / camera cutout
            toolbar.updatePadding(top = statusInsets.top)

            // Input area raised above navigation bar or keyboard
            val bottomInset = maxOf(navInsets.bottom, imeInsets.bottom)
            inputArea.updatePadding(bottom = bottomInset)

            insets
        }

        // Initialize API client
        api = RetrofitClient.api

        // Setup RecyclerView
        chatAdapter = ChatAdapter()
        recyclerView.layoutManager = LinearLayoutManager(this).apply {
            stackFromEnd = true
        }
        recyclerView.adapter = chatAdapter

        // Send button
        btnSend.setOnClickListener {
            sendMessage()
        }

        // Voice Input (STT) button
        btnMic.setOnClickListener {
            startSpeechRecognition()
        }

        // Toggle Voice Mode (auto TTS readout)
        btnVoiceToggle.setOnClickListener {
            isVoiceEnabled = !isVoiceEnabled
            updateVoiceToggleIcon()
            val stateText = if (isVoiceEnabled) "Voice mode ON" else "Voice mode OFF"
            Toast.makeText(this, stateText, Toast.LENGTH_SHORT).show()
        }
        updateVoiceToggleIcon()

        // Toggle detailed status bar visibility
        btnToggleStatus.setOnClickListener {
            toggleStatusBar()
        }

        // Toolbar title tap also toggles status bar
        toolbar.setOnClickListener {
            toggleStatusBar()
        }

        // Modes and tools menu
        btnModes.setOnClickListener {
            showModesDialog()
        }

        // Enter key sends message
        editText.setOnEditorActionListener { _, actionId, event ->
            if ((actionId == EditorInfo.IME_ACTION_SEND) ||
                (actionId == EditorInfo.IME_NULL && event?.action == KeyEvent.ACTION_DOWN)
            ) {
                sendMessage()
                true
            } else {
                false
            }
        }

        // Check server status on startup
        checkServerStatus()

        // Welcome greeting
        chatAdapter.addMessage(
            ChatMessage(
                "Haven AI ready. How can I help you today?",
                isUser = false,
            )
        )
    }

    private fun toggleStatusBar() {
        if (statusBar.visibility == View.VISIBLE) {
            statusBar.visibility = View.GONE
            btnToggleStatus.setColorFilter(Color.parseColor("#888888"))
        } else {
            statusBar.visibility = View.VISIBLE
            btnToggleStatus.setColorFilter(Color.parseColor("#2196F3"))
            checkServerStatus()
        }
    }

    private fun updateVoiceToggleIcon() {
        if (isVoiceEnabled) {
            btnVoiceToggle.setImageResource(android.R.drawable.ic_lock_silent_mode_off)
            btnVoiceToggle.setColorFilter(Color.parseColor("#64B5F6"))
        } else {
            btnVoiceToggle.setImageResource(android.R.drawable.ic_lock_silent_mode)
            btnVoiceToggle.setColorFilter(Color.parseColor("#757575"))
        }
    }

    private fun startSpeechRecognition() {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak to Haven...")
        }
        try {
            speechLauncher.launch(intent)
        } catch (_: Exception) {
            showError("Voice recognition not supported on this device.")
        }
    }

    private fun sendMessage() {
        val text = editText.text?.toString()?.trim()
        if (text.isNullOrEmpty()) return

        // Clear input
        editText.text?.clear()

        // Add user message to chat
        chatAdapter.addMessage(ChatMessage(text, isUser = true))

        // Scroll to bottom
        recyclerView.post {
            recyclerView.scrollToPosition(chatAdapter.itemCount - 1)
        }

        // Send to server
        lifecycleScope.launch {
            try {
                // Show typing indicator
                chatAdapter.addMessage(ChatMessage("...", isUser = false))
                recyclerView.scrollToPosition(chatAdapter.itemCount - 1)

                val response = api.sendMessage(MessageRequest(text))

                // Remove typing indicator from backing list and adapter
                chatAdapter.removeLastMessage()

                // Add Haven's response
                chatAdapter.addMessage(ChatMessage(response.reply, isUser = false))

                // Scroll to bottom
                recyclerView.post {
                    recyclerView.scrollToPosition(chatAdapter.itemCount - 1)
                }

                // If voice mode is on, play TTS speech
                if (isVoiceEnabled && response.reply.isNotBlank()) {
                    playVoiceResponse(response.reply)
                }

            } catch (_: IOException) {
                chatAdapter.removeLastMessage()
                showError("Network error. Check if Haven is running and Tailscale is connected.")
            } catch (e: HttpException) {
                chatAdapter.removeLastMessage()
                showError("Server error: ${e.code()}")
            } catch (e: Exception) {
                chatAdapter.removeLastMessage()
                showError("Error: ${e.message}")
            }
        }
    }

    private fun playVoiceResponse(text: String) {
        lifecycleScope.launch {
            try {
                val ttsResponse = withContext(Dispatchers.IO) {
                    api.generateTTS(TTSRequest(text = text, voice = "af_heart", speed = 1.0f))
                }
                if (ttsResponse.isSuccessful && ttsResponse.body() != null) {
                    val audioBytes = withContext(Dispatchers.IO) {
                        ttsResponse.body()!!.bytes()
                    }
                    val tempAudioFile = File(cacheDir, "haven_reply.wav")
                    withContext(Dispatchers.IO) {
                        FileOutputStream(tempAudioFile).use { it.write(audioBytes) }
                    }

                    // Play audio
                    mediaPlayer?.release()
                    mediaPlayer = MediaPlayer().apply {
                        setDataSource(tempAudioFile.absolutePath)
                        prepare()
                        start()
                    }
                }
            } catch (_: Exception) {
                // Voice failed silently, text is already displayed in chat
            }
        }
    }

    private fun checkServerStatus() {
        lifecycleScope.launch {
            try {
                val status = api.getStatus()

                // Update status indicators
                statusModel.text = "Model: ${if (status.modelLoaded) "✓" else "✗"}"
                statusModel.setTextColor(if (status.modelLoaded) Color.GREEN else Color.RED)

                statusMemory.text = "Memory: ${if (status.memoryLoaded) "✓" else "✗"}"
                statusMemory.setTextColor(if (status.memoryLoaded) Color.GREEN else Color.RED)

                statusTTS.text = "TTS: ${if (status.ttsLoaded) "✓" else "✗"}"
                statusTTS.setTextColor(if (status.ttsLoaded) Color.GREEN else Color.RED)

                val isOnline = status.status == "online"
                statusConnection.text = "Net: ${if (isOnline) "✓" else "✗"}"
                statusConnection.setTextColor(if (isOnline) Color.GREEN else Color.RED)

                // Update toolbar subtitle
                toolbar.subtitle = if (isOnline) "Haven Online • Tap for status" else "Haven Starting • Tap for status"

            } catch (_: Exception) {
                statusModel.text = "Model: ✗"
                statusModel.setTextColor(Color.RED)
                statusMemory.text = "Memory: ✗"
                statusMemory.setTextColor(Color.RED)
                statusTTS.text = "TTS: ✗"
                statusTTS.setTextColor(Color.RED)
                statusConnection.text = "Net: ✗"
                statusConnection.setTextColor(Color.RED)
                toolbar.subtitle = "Disconnected • Tap to configure"
            }
        }
    }

    private fun showModesDialog() {
        val modes = arrayOf(
            "🖥️ PC System Monitor (CPU, RAM, Disk)",
            "🧠 Memory & Knowledge Stats",
            "🎮 D&D Adventure Mode",
            "⚙️ Change Server URL (Tailscale IP)",
            "🗑️ Clear Chat History"
        )

        MaterialAlertDialogBuilder(this)
            .setTitle("Haven Modes & Tools")
            .setItems(modes) { _, which ->
                when (which) {
                    0 -> showSystemMonitorDialog()
                    1 -> showMemoryStatsDialog()
                    2 -> startDnDAdventure()
                    3 -> showServerConfigDialog()
                    4 -> {
                        chatAdapter.clearMessages()
                        chatAdapter.addMessage(ChatMessage("Chat cleared. What would you like to work on?", isUser = false))
                    }
                }
            }
            .setNegativeButton("Close", null)
            .show()
    }

    private fun showSystemMonitorDialog() {
        lifecycleScope.launch {
            try {
                val sys = api.getSystemInfo()
                val message = """
                    CPU Usage: ${sys.cpuPercent}%
                    RAM Usage: ${sys.memoryPercent}% (${sys.memoryAvailableGb} GB free / ${sys.memoryTotalGb} GB total)
                    Disk Usage: ${sys.diskPercent}% (${sys.diskFreeGb} GB free / ${sys.diskTotalGb} GB total)
                """.trimIndent()

                MaterialAlertDialogBuilder(this@MainActivity)
                    .setTitle("PC System Status")
                    .setMessage(message)
                    .setPositiveButton("OK", null)
                    .show()
            } catch (e: Exception) {
                showError("Could not fetch system info: ${e.message}")
            }
        }
    }

    private fun showMemoryStatsDialog() {
        lifecycleScope.launch {
            try {
                val stats = api.getMemoryStats()
                val message = stats.entries.joinToString("\n") { (k, v) -> "$k: $v" }

                MaterialAlertDialogBuilder(this@MainActivity)
                    .setTitle("Haven Memory Stats")
                    .setMessage(if (message.isBlank()) "Memory is active." else message)
                    .setPositiveButton("OK", null)
                    .show()
            } catch (e: Exception) {
                showError("Could not fetch memory stats: ${e.message}")
            }
        }
    }

    private fun startDnDAdventure() {
        editText.setText("Let's start a D&D adventure!")
        sendMessage()
    }

    private fun showServerConfigDialog() {
        val input = EditText(this).apply {
            setText(RetrofitClient.currentBaseUrl)
            setSelection(text.length)
            setSingleLine()
            setTextColor(Color.WHITE)
        }

        val container = FrameLayout(this).apply {
            val padding = (20 * resources.displayMetrics.density).toInt()
            setPadding(padding, padding / 2, padding, padding / 2)
            addView(input)
        }

        MaterialAlertDialogBuilder(this)
            .setTitle("Server URL")
            .setMessage("Enter your PC's Tailscale or local IP and port:")
            .setView(container)
            .setPositiveButton("Connect") { _, _ ->
                val newUrl = input.text.toString().trim()
                if (newUrl.isNotEmpty()) {
                    api = RetrofitClient.updateBaseUrl(newUrl)
                    checkServerStatus()
                }
            }
            .setNeutralButton("Refresh Status") { _, _ ->
                checkServerStatus()
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun showError(message: String) {
        val view = findViewById<View>(android.R.id.content) ?: window.decorView
        Snackbar.make(view, message, Snackbar.LENGTH_LONG).show()
    }

    override fun onDestroy() {
        super.onDestroy()
        mediaPlayer?.release()
        mediaPlayer = null
    }
}
