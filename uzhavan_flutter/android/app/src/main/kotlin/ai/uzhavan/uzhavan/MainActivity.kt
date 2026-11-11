package ai.uzhavan.uzhavan

import android.Manifest
import android.content.pm.PackageManager
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * Hosts the on-device-only speech recognizer (see [LocalSpeechRecognizer]).
 * Channel `ai.uzhavan/local_stt` is the only speech-recognition path in the app.
 */
class MainActivity : FlutterActivity() {
    private var stt: LocalSpeechRecognizer? = null
    private var pendingPermission: MethodChannel.Result? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        val channel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "ai.uzhavan/local_stt")
        val recognizer = LocalSpeechRecognizer(this, channel)
        stt = recognizer
        channel.setMethodCallHandler { call, result ->
            when (call.method) {
                "hasPermission" -> result.success(hasMic())
                "requestPermission" -> requestMic(result)
                "availability" -> recognizer.availability(call.argument<String>("locale") ?: "ta-IN", result)
                "start" -> recognizer.start(call.argument<String>("locale") ?: "ta-IN", result)
                "stop" -> { recognizer.stop(); result.success(null) }
                "cancel" -> { recognizer.cancel(); result.success(null) }
                else -> result.notImplemented()
            }
        }
    }

    private fun hasMic() =
        checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED

    private fun requestMic(result: MethodChannel.Result) {
        if (hasMic()) { result.success(true); return }
        pendingPermission?.success(false)
        pendingPermission = result
        requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), MIC_REQUEST)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == MIC_REQUEST) {
            pendingPermission?.success(grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED)
            pendingPermission = null
        }
    }

    // The recognizer holds the microphone: release it whenever the app leaves the foreground.
    override fun onPause() {
        stt?.cancel()
        super.onPause()
    }

    override fun onDestroy() {
        stt?.dispose()
        super.onDestroy()
    }

    private companion object {
        const val MIC_REQUEST = 4711
    }
}
