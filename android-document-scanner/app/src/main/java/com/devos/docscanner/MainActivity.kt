package com.devos.docscanner

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.PointF
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.DocumentScanner
import androidx.compose.material.icons.filled.FlashOff
import androidx.compose.material.icons.filled.FlashOn
import androidx.compose.material.icons.filled.PictureAsPdf
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.layout.ContentScale
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.core.content.ContextCompat
import androidx.compose.ui.platform.LocalContext
import org.opencv.android.OpenCVLoader
import java.io.File
import java.util.concurrent.Executors

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        OpenCVLoader.initLocal()
        setContent { DevOSTheme { ScannerApp() } }
    }

    @Composable
    private fun ScannerApp() {
        var granted by remember { mutableStateOf(checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) }
        val request = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted = it }
        if (granted) ScannerScreen() else PermissionScreen { request.launch(Manifest.permission.CAMERA) }
    }

    @Composable
    private fun PermissionScreen(onRequest: () -> Unit) {
        Surface(Modifier.fillMaxSize(), color = Color(0xFF090B10)) {
            Column(Modifier.fillMaxSize().padding(28.dp), verticalArrangement = Arrangement.Center) {
                Text("DEVOS SCAN", color = Color.White, fontSize = 32.sp)
                Spacer(Modifier.height(12.dp))
                Text("Premium document capture for real paperwork.", color = Color(0xFF9CA3AF), fontSize = 16.sp)
                Spacer(Modifier.height(28.dp))
                Button(onClick = onRequest, shape = RoundedCornerShape(18.dp), modifier = Modifier.fillMaxWidth().height(56.dp)) { Text("Enable Camera") }
            }
        }
    }

    @Composable
    private fun ScannerScreen() {
        var pages by remember { mutableStateOf(emptyList<ScanPage>()) }
        var selected by remember { mutableIntStateOf(-1) }
        var screen by remember { mutableStateOf("camera") }
        var flash by remember { mutableStateOf(false) }
        val context = LocalContext.current
        when (screen) {
            "camera" -> CameraView(flash = flash, onFlash = { flash = !flash }) { bitmap ->
                val detected = ImageProcessor.detectDocument(bitmap)
                val quad = detected ?: Quad(listOf(PointF(0f, 0f), PointF(bitmap.width.toFloat(), 0f), PointF(bitmap.width.toFloat(), bitmap.height.toFloat()), PointF(0f, bitmap.height.toFloat())))
                val cropped = ImageProcessor.warp(bitmap, quad)
                pages = pages + ScanPage(cropped, Quad(listOf(PointF(0f, 0f), PointF(cropped.width.toFloat(), 0f), PointF(cropped.width.toFloat(), cropped.height.toFloat()), PointF(0f, cropped.height.toFloat()))))
                selected = pages.lastIndex
                screen = "review"
            }
            "review" -> ReviewView(
                pages = pages, selected = selected,
                onSelect = { selected = it },
                onAdd = { screen = "camera" },
                onEdit = { if (selected >= 0) screen = "edit" },
                onPdf = { PdfExporter.export(context, pages) }
            )
            "edit" -> if (selected >= 0) EditorView(pages[selected], onSave = { updated -> pages = pages.toMutableList().also { it[selected] = updated }; screen = "review" }, onCancel = { screen = "review" })
        }
    }

    @Composable
    private fun CameraView(flash: Boolean, onFlash: () -> Unit, onCapture: (Bitmap) -> Unit) {
        val context = LocalContext.current
        val lifecycleOwner = LocalLifecycleOwner.current
        val executor = remember { Executors.newSingleThreadExecutor() }
        var imageCapture by remember { mutableStateOf<ImageCapture?>(null) }
        Box(Modifier.fillMaxSize().background(Color.Black)) {
            AndroidView(
                modifier = Modifier.fillMaxSize(),
                factory = { viewContext ->
                    PreviewView(viewContext).also { previewView ->
                        val providerFuture = ProcessCameraProvider.getInstance(viewContext)
                        providerFuture.addListener({
                            val provider = providerFuture.get()
                            val preview = Preview.Builder().build().also { it.setSurfaceProvider(previewView.surfaceProvider) }
                            val capture = ImageCapture.Builder().setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY).build()
                            imageCapture = capture
                            provider.unbindAll()
                            provider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, capture)
                        }, ContextCompat.getMainExecutor(viewContext))
                    }
                }
            )
            Column(Modifier.fillMaxSize().padding(22.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text("DEVOS SCAN", color = Color.White, fontSize = 22.sp)
                    IconButton(onClick = onFlash) { Icon(if (flash) Icons.Default.FlashOn else Icons.Default.FlashOff, "Flash", tint = Color.White) }
                }
                Spacer(Modifier.weight(1f))
                Text("Capture a document", color = Color.White.copy(alpha = .9f), modifier = Modifier.align(Alignment.CenterHorizontally))
                Spacer(Modifier.height(20.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
                    FloatingActionButton(
                        onClick = {
                            imageCapture?.let { capture ->
                                val file = File.createTempFile("scan-", ".jpg", context.cacheDir)
                                val options = ImageCapture.OutputFileOptions.Builder(file).build()
                                capture.takePicture(options, executor, object : ImageCapture.OnImageSavedCallback {
                                    override fun onError(exception: ImageCaptureException) = Unit
                                    override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                                        val bitmap = BitmapFactory.decodeFile(file.absolutePath)
                                        runOnUiThread { onCapture(bitmap) }
                                    }
                                })
                            }
                        }, containerColor = Color.White, contentColor = Color.Black, shape = CircleShape, modifier = Modifier.size(78.dp)
                    ) { Icon(Icons.Default.DocumentScanner, "Scan", modifier = Modifier.size(34.dp)) }
                }
            }
        }
    }

    @Composable
    private fun ReviewView(pages: List<ScanPage>, selected: Int, onSelect: (Int) -> Unit, onAdd: () -> Unit, onEdit: () -> Unit, onPdf: () -> Unit) {
        Column(Modifier.fillMaxSize().padding(18.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text("Review", color = Color.White, fontSize = 28.sp, modifier = Modifier.weight(1f))
                IconButton(onClick = onPdf) { Icon(Icons.Default.PictureAsPdf, "Export PDF", tint = Color.White) }
            }
            Spacer(Modifier.height(14.dp))
            Box(Modifier.weight(1f).fillMaxWidth().clip(RoundedCornerShape(24.dp)).background(Color(0xFF12151C)), contentAlignment = Alignment.Center) {
                if (selected >= 0) Image(pages[selected].bitmap.asImageBitmap(), null, Modifier.fillMaxSize().padding(10.dp), contentScale = ContentScale.Fit)
                else Text("Start scanning", color = Color.White.copy(alpha = .7f))
            }
            Spacer(Modifier.height(14.dp))
            LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                itemsIndexed(pages) { index, page ->
                    Image(page.bitmap.asImageBitmap(), null, Modifier.size(72.dp, 96.dp).clip(RoundedCornerShape(12.dp)).border(if (index == selected) 2.dp else 0.dp, Color.White, RoundedCornerShape(12.dp)).clickable { onSelect(index) }, contentScale = ContentScale.Crop)
                }
            }
            Spacer(Modifier.height(14.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                Button(onClick = onAdd, modifier = Modifier.weight(1f)) { Icon(Icons.Default.Add, null); Spacer(Modifier.width(6.dp)); Text("Add page") }
                OutlinedButton(onClick = onEdit, modifier = Modifier.weight(1f)) { Icon(Icons.Default.Tune, null); Spacer(Modifier.width(6.dp)); Text("Adjust") }
            }
        }
    }

    @Composable
    private fun EditorView(page: ScanPage, onSave: (ScanPage) -> Unit, onCancel: () -> Unit) {
        var filter by remember { mutableStateOf(page.filter) }
        var corners by remember { mutableStateOf(page.corners) }
        Column(Modifier.fillMaxSize().padding(18.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text("Fine tune", color = Color.White, fontSize = 26.sp, modifier = Modifier.weight(1f))
                TextButton(onClick = onCancel) { Text("Cancel") }
            }
            Spacer(Modifier.height(10.dp))
            Box(Modifier.weight(1f).fillMaxWidth().clip(RoundedCornerShape(24.dp)).background(Color(0xFF12151C)), contentAlignment = Alignment.Center) {
                Image(page.bitmap.asImageBitmap(), null, Modifier.fillMaxSize().padding(8.dp), contentScale = ContentScale.Fit)
                CornerEditor(corners) { corners = it }
            }
            Spacer(Modifier.height(12.dp))
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) { items(ScanFilter.values().toList()) { f -> FilterChip(selected = f == filter, onClick = { filter = f }, label = { Text(f.label) }) } }
            Spacer(Modifier.height(12.dp))
            Button(onClick = { onSave(page.copy(bitmap = ImageProcessor.applyFilter(page.bitmap, filter), corners = corners, filter = filter)) }, modifier = Modifier.fillMaxWidth().height(54.dp), shape = RoundedCornerShape(18.dp)) { Text("Apply & Save") }
        }
    }

    @Composable
    private fun CornerEditor(quad: Quad, onChange: (Quad) -> Unit) {
        Canvas(Modifier.fillMaxSize().pointerInput(quad) {
            detectDragGestures { change, drag ->
                change.consume()
                val index = quad.points.indices.minBy { i ->
                    val dx = quad.points[i].x - change.position.x; val dy = quad.points[i].y - change.position.y; dx * dx + dy * dy
                }
                val next = quad.points.toMutableList()
                next[index] = PointF((next[index].x + drag.x).coerceIn(0f, size.width.toFloat()), (next[index].y + drag.y).coerceIn(0f, size.height.toFloat()))
                onChange(Quad(next))
            }
        }) {
            fun DrawScope.line(a: PointF, b: PointF) { drawLine(Color.White, androidx.compose.ui.geometry.Offset(a.x, a.y), androidx.compose.ui.geometry.Offset(b.x, b.y), strokeWidth = 4f) }
            line(quad.points[0], quad.points[1]); line(quad.points[1], quad.points[2]); line(quad.points[2], quad.points[3]); line(quad.points[3], quad.points[0])
            quad.points.forEach { drawCircle(Color.White, 14f, androidx.compose.ui.geometry.Offset(it.x, it.y)) }
        }
    }
}

@Composable
private fun DevOSTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = darkColorScheme(primary = Color(0xFFB7C7FF), secondary = Color(0xFF8DE8D0), surface = Color(0xFF0F1218), background = Color(0xFF090B10)), content = content)
}
