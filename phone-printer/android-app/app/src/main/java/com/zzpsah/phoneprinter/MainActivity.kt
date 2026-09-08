package com.zzpsah.phoneprinter

import android.content.ContentResolver
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

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

@Composable
fun PrinterScreen(contentResolver: ContentResolver) {
    var serverIp by remember { mutableStateOf("") }
    var printers by remember { mutableStateOf(emptyList<String>()) }
    var selectedPrinter by remember { mutableStateOf("") }
    var selectedUri by remember { mutableStateOf<Uri?>(null) }
    var selectedName by remember { mutableStateOf("No file selected") }
    var status by remember { mutableStateOf("Enter Windows PC IP and connect") }
    var expanded by remember { mutableStateOf(false) }

    val client = remember { OkHttpClient() }

    val picker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        selectedUri = uri
        selectedName = uri?.lastPathSegment ?: "Selected file"
    }

    fun baseUrl(): String = "http://${serverIp.trim()}:8765"

    fun loadPrinters() {
        if (serverIp.isBlank()) {
            status = "Enter the Windows PC IP first"
            return
        }
        status = "Connecting..."
        val request = Request.Builder().url("${baseUrl()}/printers").get().build()
        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                status = "Connection failed: ${e.message}"
            }
            override fun onResponse(call: Call, response: Response) {
                response.use {
                    val body = it.body?.string().orEmpty()
                    if (!it.isSuccessful) {
                        status = "Server error: $body"
                        return
                    }
                    val array = JSONObject(body).getJSONArray("printers")
                    val list = mutableListOf<String>()
                    for (i in 0 until array.length()) list.add(array.getString(i))
                    printers = list
                    selectedPrinter = list.firstOrNull().orEmpty()
                    status = if (list.isEmpty()) "Connected, but no printer found" else "Connected"
                }
            }
        })
    }

    fun sendPrint() {
        val uri = selectedUri
        if (uri == null) {
            status = "Select a PDF or image first"
            return
        }
        if (selectedPrinter.isBlank()) {
            status = "Select a printer"
            return
        }

        status = "Sending print job..."
        val bytes = contentResolver.openInputStream(uri)?.use { it.readBytes() }
        if (bytes == null) {
            status = "Could not read selected file"
            return
        }

        val mime = contentResolver.getType(uri) ?: "application/octet-stream"
        val fileBody = bytes.toRequestBody(mime.toMediaTypeOrNull())
        val requestBody = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("printer", selectedPrinter)
            .addFormDataPart("file", selectedName, fileBody)
            .build()

        val request = Request.Builder()
            .url("${baseUrl()}/print")
            .post(requestBody)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                status = "Print failed: ${e.message}"
            }
            override fun onResponse(call: Call, response: Response) {
                response.use {
                    status = if (it.isSuccessful) {
                        "Print job sent successfully"
                    } else {
                        "Print failed: ${it.body?.string().orEmpty()}"
                    }
                }
            }
        })
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Text("Phone Printer", style = MaterialTheme.typography.headlineMedium)
        Text("Phone hotspot → Windows PC → USB printer")

        OutlinedTextField(
            value = serverIp,
            onValueChange = { serverIp = it },
            label = { Text("Windows PC IP") },
            placeholder = { Text("Example: 192.168.43.120") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
            modifier = Modifier.fillMaxWidth()
        )

        Button(onClick = { loadPrinters() }, modifier = Modifier.fillMaxWidth()) {
            Text("Connect / Refresh Printers")
        }

        Box(modifier = Modifier.fillMaxWidth()) {
            OutlinedButton(
                onClick = { expanded = true },
                enabled = printers.isNotEmpty(),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(if (selectedPrinter.isBlank()) "Select Printer" else selectedPrinter)
            }
            DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                printers.forEach { printer ->
                    DropdownMenuItem(
                        text = { Text(printer) },
                        onClick = {
                            selectedPrinter = printer
                            expanded = false
                        }
                    )
                }
            }
        }

        OutlinedButton(
            onClick = { picker.launch(arrayOf("application/pdf", "image/*")) },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Select PDF / Image")
        }

        Text(selectedName)

        Button(
            onClick = { sendPrint() },
            enabled = selectedUri != null && selectedPrinter.isNotBlank(),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("PRINT")
        }

        HorizontalDivider()
        Text("Status: $status")
    }
}
