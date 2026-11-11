package ai.uzhavan.uzhavan

import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import io.flutter.plugin.common.MethodChannel
import java.util.concurrent.Executors

/**
 * On-device-ONLY speech recognition for UZHAVAN AI (zero-cloud policy).
 *
 * This class calls [SpeechRecognizer.createOnDeviceSpeechRecognizer] and NOTHING ELSE.
 * It never calls [SpeechRecognizer.createSpeechRecognizer] (the default recognizer, which
 * Android may serve from an online Google service) and never falls back to it: when an
 * on-device recognizer is not available it reports `offline_unavailable` and the app asks
 * the farmer to type instead. No audio is captured or sent by this app code.
 *
 * Why not the `speech_to_text` Flutter plugin: its `onDevice` option silently falls back to
 * the default (possibly online) recognizer below API 31 or when no on-device service exists,
 * and the app was not even passing it. Removing it removes that code path from the APK.
 *
 * Limit of what this proves: Android's on-device recognizer API is documented to process audio
 * locally, but the recognition service is a vendor component (Google/Samsung) that this app
 * cannot audit. Verify on the device with data/Wi-Fi off (see the voice report).
 */
class LocalSpeechRecognizer(
    private val context: Context,
    private val channel: MethodChannel,
) {
    private val tag = "UZ_LOCAL_STT"
    private val main = Handler(Looper.getMainLooper())
    private var recognizer: SpeechRecognizer? = null

    // ── availability ────────────────────────────────────────────────────────────────────────
    /** state: ready | ready_unverified | language_missing | language_unsupported |
     *         unsupported_api | no_on_device_service */
    fun availability(localeTag: String, result: MethodChannel.Result) {
        val api = Build.VERSION.SDK_INT
        if (api < Build.VERSION_CODES.S) {
            Log.i(tag, "availability: unsupported_api api=$api (on-device recognizer needs API 31+)")
            result.success(mapOf("state" to "unsupported_api", "api" to api))
            return
        }
        if (!SpeechRecognizer.isOnDeviceRecognitionAvailable(context)) {
            Log.i(tag, "availability: no_on_device_service api=$api")
            result.success(mapOf("state" to "no_on_device_service", "api" to api))
            return
        }
        if (api < Build.VERSION_CODES.TIRAMISU) {
            // API 31/32 cannot list installed offline languages; verified when listening starts.
            Log.i(tag, "availability: ready_unverified api=$api locale=$localeTag")
            result.success(mapOf("state" to "ready_unverified", "api" to api))
            return
        }
        val probe = SpeechRecognizer.createOnDeviceSpeechRecognizer(context)
        val intent = recognizerIntent(localeTag)
        probe.checkRecognitionSupport(
            intent,
            Executors.newSingleThreadExecutor(),
            object : android.speech.RecognitionSupportCallback {
                override fun onSupportResult(support: android.speech.RecognitionSupport) {
                    val installed = support.installedOnDeviceLanguages
                    val supported = support.supportedOnDeviceLanguages
                    val want = localeTag.lowercase()
                    val lang = want.substringBefore('-')
                    val has = { l: List<String> -> l.any { it.lowercase() == want || it.lowercase().substringBefore('-') == lang } }
                    val state = when {
                        has(installed) -> "ready"
                        has(supported) -> "language_missing"
                        else -> "language_unsupported"
                    }
                    Log.i(tag, "availability: $state api=$api locale=$localeTag installed=${installed.size} supported=${supported.size}")
                    main.post {
                        probe.destroy()
                        result.success(mapOf("state" to state, "api" to api, "installed" to installed, "supported" to supported))
                    }
                }

                override fun onError(error: Int) {
                    Log.w(tag, "availability: checkRecognitionSupport error=$error -> ready_unverified")
                    main.post {
                        probe.destroy()
                        result.success(mapOf("state" to "ready_unverified", "api" to api))
                    }
                }
            },
        )
    }

    // ── listening ───────────────────────────────────────────────────────────────────────────
    fun start(localeTag: String, result: MethodChannel.Result) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S ||
            !SpeechRecognizer.isOnDeviceRecognitionAvailable(context)
        ) {
            Log.w(tag, "start refused: no on-device recognizer; NOT falling back to the default recognizer")
            emit(mapOf("type" to "error", "code" to "offline_unavailable"))
            result.success(false)
            return
        }
        destroyRecognizer()
        val r = SpeechRecognizer.createOnDeviceSpeechRecognizer(context)
        r.setRecognitionListener(listener)
        recognizer = r
        Log.i(tag, "start: recognizer=ON_DEVICE locale=$localeTag prefer_offline=true")
        r.startListening(recognizerIntent(localeTag))
        result.success(true)
    }

    fun stop() {
        Log.i(tag, "stop (finish utterance)")
        recognizer?.stopListening()
    }

    fun cancel() {
        Log.i(tag, "cancel")
        recognizer?.cancel()
    }

    fun dispose() = destroyRecognizer()

    private fun destroyRecognizer() {
        recognizer?.destroy()
        recognizer = null
    }

    private fun recognizerIntent(localeTag: String) =
        Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, localeTag)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            putExtra(RecognizerIntent.EXTRA_CALLING_PACKAGE, context.packageName)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1800L)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1800L)
        }

    private fun emit(event: Map<String, Any?>) {
        main.post { channel.invokeMethod("event", event) }
    }

    private fun firstOf(b: Bundle?): String =
        b?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull().orEmpty()

    private val listener = object : RecognitionListener {
        override fun onReadyForSpeech(params: Bundle?) {
            Log.i(tag, "ready_for_speech")
            emit(mapOf("type" to "status", "value" to "listening"))
        }

        override fun onBeginningOfSpeech() = emit(mapOf("type" to "status", "value" to "speech_began"))
        override fun onRmsChanged(rmsdB: Float) {}
        override fun onBufferReceived(buffer: ByteArray?) {}
        override fun onEndOfSpeech() {
            Log.i(tag, "end_of_speech")
            emit(mapOf("type" to "status", "value" to "end_of_speech"))
        }

        override fun onPartialResults(partialResults: Bundle?) {
            val t = firstOf(partialResults)
            if (t.isNotEmpty()) emit(mapOf("type" to "partial", "text" to t))
        }

        override fun onResults(results: Bundle?) {
            val t = firstOf(results)
            Log.i(tag, "final_result chars=${t.length}")      // text itself is never logged here
            emit(mapOf("type" to "final", "text" to t))
        }

        override fun onError(error: Int) {
            val code = when (error) {
                SpeechRecognizer.ERROR_NO_MATCH, SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "no_speech"
                SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "permission"
                12, 13 -> "language_missing"          // ERROR_LANGUAGE_NOT_SUPPORTED / _UNAVAILABLE (API 31)
                SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "busy"
                SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "network_refused"
                else -> "error_$error"
            }
            Log.w(tag, "error code=$error mapped=$code")
            emit(mapOf("type" to "error", "code" to code))
        }

        override fun onEvent(eventType: Int, params: Bundle?) {}
    }
}
