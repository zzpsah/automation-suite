package com.zzpsah.phoneprinter

import android.content.ContentResolver
import android.database.Cursor
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.OpenableColumns
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

private const val SERVER_PORT = 8765
private const val DISCOVERY_PORT = 8766

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    PrinterScreen(contentResolver)
                }
            }
        }
    }
}

private fun displayName(resolver: ContentResolver, uri: Uri): String {
    var name = uri.lastPathSegment ?: "document"
    val cursor: Cursor? = resolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)
    cursor?.use {
        if (it.moveToFirst()) name = it.getString(0)
    }
    return name
}

private fun makePreview(resolver: ContentResolver, uri: Uri): Bitmap? {
    val mime = resolver.getType(uri).orEmpty()
    return try {
        if (mime == "application/pdf") {
            val pfd = resolver.openFileDescriptor(uri, "r") ?: return null
            PdfRenderer(pfd).use { renderer ->
                if (renderer.pageCount == 0) return null
                renderer.openPage(0).use { page ->
                    val targetWidth = 900
                    val targetHeight = (targetWidth.toFloat() / page.width * page.height).toInt().coerceAtLeast(1)
                    val bitmap = Bitmap.createBitmap(targetWidth, targetHeight, Bitmap.Config.ARGB_8888)
                    page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                    bitmap
                }
            }
        } else {
            resolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it) }
        }
    } catch (_: Exception) {
        null
    }
}

@Composable
fun PrinterScreen(contentResolver: ContentResolver) {
    val mainHandler = remember { Handler(Looper.getMainLooper()) }
    val client = remember { OkHttpClient.Builder().callTimeout(java.time.Duration.ofSeconds(12)).build() }

    var serverIp by remember { mutableStateOf("") }
    var serverName by remember { mutableStateOf("") }
    var manualIp by remember { mutableStateOf("") }
    var showAdvanced by remember { mutableStateOf(false) }
    var printers by remember { mutableStateOf(emptyList<String>()) }
    var selectedPrinter by remember { mutableStateOf("") }
    var selectedUri by remember { mutableStateOf<Uri?>(null) }
    var selectedName by remember { mutableStateOf("No file selected") }
    var preview by remember { mutableStateOf<Bitmap?>(null) }
    var status by remember { mutableStateOf("Searching for Windows Print Hub…") }
    var copies by remember { mutableStateOf("1") }
    var color by remember { mutableStateOf("Color") }
    var duplex by remember { mutableStateOf("Simplex") }
    var orientation by remember { mutableStateOf("Portrait") }
    var paperSize by remember { mutableStateOf("A4") }
    var jobId by remember { mutableStateOf("") }

    fun baseUrl(): String = "http://$serverIp:$SERVER_PORT"

    fun loadPrinters(ip: String, name: String = "Windows PC") {
        serverIp = ip
        serverName = name
        status = "Found $name. Loading printers…"
        val request = Request.Builder().url("http://$ip:$SERVER_PORT/printers").get().build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                mainHandler.post { status = "Found PC but could not connect: ${e.message}" }
            }
            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val body = it.body?.string().orEmpty()
                    if (!it.isSuccessful) {
                        mainHandler.post { status = "Print Hub error: $body" }
                        return
                    }
                    val array = JSONObject(body).getJSONArray("printers")
                    val list = (0 until array.length()).map { i -> array.getString(i) }
                    mainHandler.post {
                        printers = list
                        selectedPrinter = list.firstOrNull().orEmpty()
                        status = if (list.isEmpty()) "Connected to $name, but no printer was found" else "Connected to $name"
                    }
                }
            }
        })
    }

    fun discover() {
        status = "Searching on hotspot / local network…"
        Thread {
            try {
                DatagramSocket(null).use { socket ->
                    socket.reuseAddress = true
                    socket.broadcast = true
                    socket.soTimeout = 6000
                    socket.bind(java.net.InetSocketAddress(DISCOVERY_PORT))
                    val requestBytes = "DISCOVER_PHONE_PRINTER".toByteArray()
                    try {
                        socket.send(DatagramPacket(requestBytes, requestBytes.size, InetAddress.getByName("255.255.255.255"), DISCOVERY_PORT))
                    } catch (_: Exception) { }
                    val buffer = ByteArray(2048)
                    val packet = DatagramPacket(buffer, buffer.size)
                    socket.receive(packet)
                    val text = String(packet.data, 0, packet.length)
                    val json = JSONObject(text)
                    if (json.optString("service") == "PHONE_PRINTER") {
                        val ip = packet.address.hostAddress ?: return@use
                        val name = json.optString("name", "Windows PC")
                        mainHandler.post { loadPrinters(ip, name) }
                    }
                }
            } catch (_: Exception) {
                mainHandler.post {
                    status = "Automatic discovery failed. Tap Search Again or use Advanced manual IP."
                }
            }
        }.start()
    }

    fun pollJob(id: String) {
        val request = Request.Builder().url("${baseUrl()}/jobs/$id").get().build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                mainHandler.post { status = "Job $id sent; status check failed" }
            }
            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val body = it.body?.string().orEmpty()
                    if (!it.isSuccessful) return
                    val json = JSONObject(body)
                    val state = json.optString("status")
                    val error = json.optString("error")
                    mainHandler.post {
                        status = when (state) {
                            "queued" -> "Job $id queued"
                            "printing" -> "Job $id is printing…"
                            "completed" -> "Job $id completed"
                            "failed" -> "Job $id failed: $error"
                            else -> "Job $id: $state"
                        }
                    }
                    if (state == "queued" || state == "printing") {
                        mainHandler.postDelayed({ pollJob(id) }, 1800)
                    }
                }
            }
        })
    }

    fun sendPrint() {
        val uri = selectedUri ?: run { status = "Select a PDF or image first"; return }
        if (serverIp.isBlank()) { status = "Windows Print Hub is not connected"; return }
        if (selectedPrinter.isBlank()) { status = "Select a printer"; return }
        val copyCount = copies.toIntOrNull()?.coerceIn(1, 99) ?: 1
        status = "Uploading print job…"

        Thread {
            val bytes = contentResolver.openInputStream(uri)?.use { it.readBytes() }
            if (bytes == null) {
                mainHandler.post { status = "Could not read selected file" }
                return@Thread
            }
            val mime = contentResolver.getType(uri) ?: "application/octet-stream"
            val body = MultipartBody.Builder().setType(MultipartBody.FORM)
                .addFormDataPart("printer", selectedPrinter)
                .addFormDataPart("copies", copyCount.toString())
                .addFormDataPart("color", (color == "Color").toString())
                .addFormDataPart("duplex", duplex)
                .addFormDataPart("orientation", orientation)
                .addFormDataPart("paper_size", paperSize)
                .addFormDataPart("source", android.os.Build.MODEL)
                .addFormDataPart("file", selectedName, bytes.toRequestBody(mime.toMediaTypeOrNull()))
                .build()
            val request = Request.Builder().url("${baseUrl()}/print").post(body).build()
            client.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    mainHandler.post { status = "Print failed: ${e.message}" }
                }
                override fun onResponse(call: Call, response: Response) {
                    response.use {
                        val text = it.body?.string().orEmpty()
                        if (!it.isSuccessful) {
                            mainHandler.post { status = "Print failed: $text" }
                            return
                        }
                        val id = JSONObject(text).getString("job_id")
                        mainHandler.post {
                            jobId = id
                            status = "Job $id queued"
                            pollJob(id)
                        }
                    }
                }
            })
        }.start()
    }

    LaunchedEffect(Unit) { discover() }

    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        selectedUri = uri
        if (uri != null) {
            selectedName = displayName(contentResolver, uri)
            preview = makePreview(contentResolver, uri)
        } else {
            selectedName = "No file selected"
            preview = null
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text("Phone Printer", style = MaterialTheme.typography.headlineMedium)
        Text("Hotspot / LAN → Windows Print Hub → USB printer")

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(if (serverIp.isBlank()) "Computer: searching…" else "Computer: $serverName ✓")
                if (serverIp.isNotBlank()) Text("Connected", style = MaterialTheme.typography.bodySmall)
                Button(onClick = { discover() }, modifier = Modifier.fillMaxWidth()) { Text("SEARCH AGAIN") }
                TextButton(onClick = { showAdvanced = !showAdvanced }) { Text("Advanced") }
                if (showAdvanced) {
                    OutlinedTextField(manualIp, { manualIp = it }, label = { Text("Manual PC IP") }, modifier = Modifier.fillMaxWidth())
                    OutlinedButton(onClick = { if (manualIp.isNotBlank()) loadPrinters(manualIp.trim(), "Manual PC") }, modifier = Modifier.fillMaxWidth()) { Text("CONNECT MANUALLY") }
                }
            }
        }

        DropdownField("Printer", selectedPrinter, printers) { selectedPrinter = it }

        OutlinedButton(onClick = { picker.launch(arrayOf("application/pdf", "image/*")) }, modifier = Modifier.fillMaxWidth()) {
            Text("SELECT PDF / IMAGE")
        }
        Text(selectedName)

        preview?.let { bitmap ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(10.dp)) {
                    Text("Preview", style = MaterialTheme.typography.titleMedium)
                    Spacer(Modifier.height(8.dp))
                    Image(bitmap.asImageBitmap(), contentDescription = "Print preview", modifier = Modifier.fillMaxWidth().heightIn(max = 420.dp), contentScale = ContentScale.Fit)
                    Text("Preview shows the first PDF page or selected image.", style = MaterialTheme.typography.bodySmall)
                }
            }
        }

        Text("Print settings", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(copies, { copies = it.filter(Char::isDigit) }, label = { Text("Copies") }, modifier = Modifier.fillMaxWidth())
        DropdownField("Color", color, listOf("Color", "Black & White")) { color = it }
        DropdownField("Duplex", duplex, listOf("Simplex", "Long edge", "Short edge")) { duplex = it }
        DropdownField("Orientation", orientation, listOf("Portrait", "Landscape")) { orientation = it }
        DropdownField("Paper size", paperSize, listOf("A4", "Letter", "Legal", "A5")) { paperSize = it }

        Button(onClick = { sendPrint() }, enabled = selectedUri != null && selectedPrinter.isNotBlank() && serverIp.isNotBlank(), modifier = Modifier.fillMaxWidth().height(54.dp)) {
            Text("PRINT")
        }

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.padding(14.dp)) {
                Text("Status", style = MaterialTheme.typography.titleMedium)
                Text(status)
                if (jobId.isNotBlank()) Text("Job ID: $jobId", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun DropdownField(label: String, value: String, options: List<String>, onSelect: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Column(modifier = Modifier.fillMaxWidth()) {
        Text(label, style = MaterialTheme.typography.labelLarge)
        Box(modifier = Modifier.fillMaxWidth()) {
            OutlinedButton(onClick = { expanded = true }, enabled = options.isNotEmpty(), modifier = Modifier.fillMaxWidth()) {
                Text(if (value.isBlank()) "Select $label" else value)
            }
            DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                options.forEach { option ->
                    DropdownMenuItem(text = { Text(option) }, onClick = { onSelect(option); expanded = false })
                }
            }
        }
    }
}
