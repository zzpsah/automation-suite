package com.devos.docscanner

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.graphics.PointF
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
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
import androidx.compose.material.icons.filled.Share
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
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.exifinterface.media.ExifInterface
import androidx.lifecycle.compose.LocalLifecycleOwner
import org.opencv.android.OpenCVLoader
import java.io.File
import java.util.concurrent.Executors

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val opencvAvailable = runCatching { OpenCVLoader.initLocal() }.getOrDefault(false)
        setContent { DevOSTheme { ScannerApp(opencvAvailable) } }
    }

    @Composable
    private fun ScannerApp(opencvAvailable: Boolean) {
        var granted by remember { mutableStateOf(checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) }
        val request = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted = it }
        if (granted) ScannerScreen(opencvAvailable) else PermissionScreen { request.launch(Manifest.permission.CAMERA) }
    }

    @Composable
    private fun PermissionScreen(onRequest: () -> Unit) {
        Surface(Modifier.fillMaxSize(), color = Color(0xFF090B10)) {
            Column(Modifier.fillMaxSize().padding(28.dp), verticalArrangement = Arrangement.Center) {
                Text("DEVOS SCAN", color = Color.White, fontSize = 32.sp)
                Spacer(Modifier.height(12.dp)); Text("Premium document capture for real paperwork.", color = Color(0xFF9CA3AF), fontSize = 16.sp)
                Spacer(Modifier.height(28.dp)); Button(onClick = onRequest, shape = RoundedCornerShape(18.dp), modifier = Modifier.fillMaxWidth().height(56.dp)) { Text("Enable Camera") }
            }
        }
    }

    @Composable
    private fun ScannerScreen(opencvAvailable: Boolean) {
        val context = LocalContext.current
        var pages by remember { mutableStateOf(ScanSessionStore.load(context)) }
        var selected by remember { mutableIntStateOf(if (pages.isEmpty()) -1 else pages.lastIndex) }
        var screen by remember { mutableStateOf(if (pages.isEmpty()) "camera" else "review") }
        var flash by remember { mutableStateOf(false) }
        var processing by remember { mutableStateOf(false) }
        var error by remember { mutableStateOf<String?>(null) }
        val workExecutor = remember { Executors.newSingleThreadExecutor() }
        DisposableEffect(Unit) { onDispose { workExecutor.shutdown() } }
        val savePdf = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/pdf")) { uri ->
            if (uri != null) {
                processing = true
                workExecutor.execute { val ok = PdfExporter.writeToUri(context, pages, uri); runOnUiThread { processing = false; if (!ok) error = "PDF export failed" } }
            }
        }

        Box(Modifier.fillMaxSize()) {
            when (screen) {
                "camera" -> CameraView(flash, { flash = !flash }, processing, { msg -> error = msg }) { bitmap ->
                    processing = true
                    workExecutor.execute {
                        val quad = if (opencvAvailable) ImageProcessor.detectDocument(bitmap) ?: fullQuad(bitmap.width, bitmap.height) else fullQuad(bitmap.width, bitmap.height)
                        val cropped = runCatching { if (opencvAvailable) ImageProcessor.warp(bitmap, quad) else bitmap.copy(Bitmap.Config.ARGB_8888, false) }.getOrElse { bitmap.copy(Bitmap.Config.ARGB_8888, false) }
                        val page = ScanPage(bitmap, cropped, quad)
                        val next = pages + page
                        ScanSessionStore.save(context, next)
                        runOnUiThread { pages = next; selected = next.lastIndex; processing = false; screen = "review" }
                    }
                }
                "review" -> ReviewView(pages, selected, { selected = it }, { screen = "camera" }, { if (selected >= 0) screen = "edit" }, { savePdf.launch("DevOS-Scan-${System.currentTimeMillis()}.pdf") }, {
                    val file = PdfExporter.createTempPdf(context, pages)
                    if (file != null) runCatching {
                        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
                        startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply { type = "application/pdf"; putExtra(Intent.EXTRA_STREAM, uri); addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION) }, "Share scan"))
                    }.onFailure { error = "Unable to share PDF" }
                }, { pages = emptyList(); selected = -1; ScanSessionStore.clear(context); screen = "camera" })
                "edit" -> if (selected >= 0) EditorView(pages[selected], opencvAvailable, { updated -> val next = pages.toMutableList().also { it[selected] = updated }; ScanSessionStore.save(context, next); pages = next; screen = "review" }, { screen = "review" }, { error = it })
            }
            if (processing) ProcessingOverlay()
            error?.let { message -> AlertDialog(onDismissRequest = { error = null }, title = { Text("Scanner error") }, text = { Text(message) }, confirmButton = { TextButton(onClick = { error = null }) { Text("OK") } }) }
        }
    }

    private fun fullQuad(width: Int, height: Int) = Quad(listOf(PointF(0f, 0f), PointF(width.toFloat(), 0f), PointF(width.toFloat(), height.toFloat()), PointF(0f, height.toFloat())))

    @Composable
    private fun ProcessingOverlay() {
        Box(Modifier.fillMaxSize().background(Color.Black.copy(alpha = .45f)), contentAlignment = Alignment.Center) {
            Surface(shape = RoundedCornerShape(20.dp), color = Color(0xFF171B24)) { Row(Modifier.padding(horizontal = 22.dp, vertical = 16.dp), verticalAlignment = Alignment.CenterVertically) { CircularProgressIndicator(Modifier.size(24.dp), strokeWidth = 2.dp); Spacer(Modifier.width(12.dp)); Text("Processing scan…", color = Color.White) } }
        }
    }

    @Composable
    private fun CameraView(flash: Boolean, onFlash: () -> Unit, disabled: Boolean, onError: (String) -> Unit, onCapture: (Bitmap) -> Unit) {
        val context = LocalContext.current
        val lifecycleOwner = LocalLifecycleOwner.current
        val executor = remember { Executors.newSingleThreadExecutor() }
        var imageCapture by remember { mutableStateOf<ImageCapture?>(null) }
        DisposableEffect(Unit) { onDispose { executor.shutdown() } }
        LaunchedEffect(flash) { imageCapture?.flashMode = if (flash) ImageCapture.FLASH_MODE_ON else ImageCapture.FLASH_MODE_OFF }
        Box(Modifier.fillMaxSize().background(Color.Black)) {
            AndroidView(
                factory = { viewContext ->
                    PreviewView(viewContext).also { previewView ->
                        val future = ProcessCameraProvider.getInstance(viewContext)
                        future.addListener({
                            runCatching {
                                val provider = future.get()
                                val preview = Preview.Builder().build().also { it.setSurfaceProvider(previewView.surfaceProvider) }
                                val capture = ImageCapture.Builder().setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY).setJpegQuality(98).setFlashMode(if (flash) ImageCapture.FLASH_MODE_ON else ImageCapture.FLASH_MODE_OFF).build()
                                imageCapture = capture
                                provider.unbindAll()
                                provider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, capture)
                            }.onFailure { ContextCompat.getMainExecutor(viewContext).execute { onError("Camera could not start: ${it.message ?: "unknown error"}") } }
                        }, ContextCompat.getMainExecutor(viewContext))
                    }
                },
                modifier = Modifier.fillMaxSize()
            )
            Column(Modifier.fillMaxSize().padding(22.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) { Text("DEVOS SCAN", color = Color.White, fontSize = 22.sp); IconButton(onClick = onFlash, enabled = !disabled) { Icon(if (flash) Icons.Default.FlashOn else Icons.Default.FlashOff, "Flash", tint = Color.White) } }
                Spacer(Modifier.weight(1f)); Text("Align the full page inside the frame", color = Color.White.copy(alpha = .9f), modifier = Modifier.align(Alignment.CenterHorizontally)); Spacer(Modifier.height(20.dp))
                FloatingActionButton(onClick = {
                    if (disabled) return@FloatingActionButton
                    val capture = imageCapture ?: run { onError("Camera is still starting"); return@FloatingActionButton }
                    runCatching {
                        val file = File.createTempFile("scan-", ".jpg", context.cacheDir)
                        capture.takePicture(ImageCapture.OutputFileOptions.Builder(file).build(), executor, object : ImageCapture.OnImageSavedCallback {
                            override fun onError(exception: ImageCaptureException) { ContextCompat.getMainExecutor(context).execute { onError("Capture failed: ${exception.message ?: "unknown error"}") } }
                            override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                                val bitmap = decodeOriented(file)
                                file.delete()
                                ContextCompat.getMainExecutor(context).execute { if (bitmap != null) onCapture(bitmap) else onError("Captured image could not be decoded") }
                            }
                        })
                    }.onFailure { onError("Unable to capture: ${it.message ?: "unknown error"}") }
                }, containerColor = Color.White, contentColor = Color.Black, shape = CircleShape, modifier = Modifier.size(78.dp).align(Alignment.CenterHorizontally)) { Icon(Icons.Default.DocumentScanner, "Scan", Modifier.size(34.dp)) }
            }
        }
    }

    private fun decodeOriented(file: File): Bitmap? = runCatching {
        val bitmap = BitmapFactory.decodeFile(file.absolutePath) ?: return null
        val exif = ExifInterface(file.absolutePath)
        val orientation = exif.getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL)
        val matrix = Matrix()
        when (orientation) {
            ExifInterface.ORIENTATION_ROTATE_90 -> matrix.postRotate(90f)
            ExifInterface.ORIENTATION_ROTATE_180 -> matrix.postRotate(180f)
            ExifInterface.ORIENTATION_ROTATE_270 -> matrix.postRotate(270f)
            ExifInterface.ORIENTATION_FLIP_HORIZONTAL -> matrix.preScale(-1f, 1f)
            ExifInterface.ORIENTATION_FLIP_VERTICAL -> matrix.preScale(1f, -1f)
            ExifInterface.ORIENTATION_TRANSPOSE -> { matrix.postRotate(90f); matrix.preScale(-1f, 1f) }
            ExifInterface.ORIENTATION_TRANSVERSE -> { matrix.postRotate(270f); matrix.preScale(-1f, 1f) }
        }
        if (matrix.isIdentity) bitmap else Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true).also { if (it !== bitmap) bitmap.recycle() }
    }.getOrNull()

    @Composable
    private fun ReviewView(pages: List<ScanPage>, selected: Int, onSelect: (Int) -> Unit, onAdd: () -> Unit, onEdit: () -> Unit, onPdf: () -> Unit, onShare: () -> Unit, onClear: () -> Unit) {
        Column(Modifier.fillMaxSize().padding(18.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) { Text("Review · ${pages.size}", color = Color.White, fontSize = 28.sp, modifier = Modifier.weight(1f)); IconButton(onClick = onShare, enabled = pages.isNotEmpty()) { Icon(Icons.Default.Share, "Share PDF", tint = Color.White) }; IconButton(onClick = onPdf, enabled = pages.isNotEmpty()) { Icon(Icons.Default.PictureAsPdf, "Save PDF", tint = Color.White) } }
            Spacer(Modifier.height(14.dp)); Box(Modifier.weight(1f).fillMaxWidth().clip(RoundedCornerShape(24.dp)).background(Color(0xFF12151C)), contentAlignment = Alignment.Center) { if (selected >= 0) Image(pages[selected].bitmap.asImageBitmap(), null, Modifier.fillMaxSize().padding(10.dp), contentScale = ContentScale.Fit) else Text("Start scanning", color = Color.White.copy(alpha = .7f)) }
            Spacer(Modifier.height(14.dp)); LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) { itemsIndexed(pages) { index, page -> Image(page.bitmap.asImageBitmap(), null, Modifier.size(72.dp, 96.dp).clip(RoundedCornerShape(12.dp)).border(if (index == selected) 2.dp else 0.dp, Color.White, RoundedCornerShape(12.dp)).clickable { onSelect(index) }, contentScale = ContentScale.Crop) } }
            Spacer(Modifier.height(14.dp)); Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) { Button(onClick = onAdd, modifier = Modifier.weight(1f)) { Icon(Icons.Default.Add, null); Spacer(Modifier.width(6.dp)); Text("Add page") }; OutlinedButton(onClick = onEdit, enabled = selected >= 0, modifier = Modifier.weight(1f)) { Icon(Icons.Default.Tune, null); Spacer(Modifier.width(6.dp)); Text("Adjust") } }
            TextButton(onClick = onClear, modifier = Modifier.align(Alignment.End)) { Text("Clear session") }
        }
    }

    @Composable
    private fun EditorView(page: ScanPage, opencvAvailable: Boolean, onSave: (ScanPage) -> Unit, onCancel: () -> Unit, onError: (String) -> Unit) {
        var filter by remember { mutableStateOf(page.filter) }; var corners by remember { mutableStateOf(page.corners) }
        Column(Modifier.fillMaxSize().padding(18.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) { Text("Fine tune", color = Color.White, fontSize = 26.sp, modifier = Modifier.weight(1f)); TextButton(onClick = onCancel) { Text("Cancel") } }
            Spacer(Modifier.height(10.dp)); Box(Modifier.weight(1f).fillMaxWidth().clip(RoundedCornerShape(24.dp)).background(Color(0xFF12151C)), contentAlignment = Alignment.Center) { Image(page.originalBitmap.asImageBitmap(), null, Modifier.fillMaxSize().padding(8.dp), contentScale = ContentScale.Fit); CornerEditor(corners, page.originalBitmap.width, page.originalBitmap.height) { corners = it } }
            Spacer(Modifier.height(12.dp)); LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) { items(ScanFilter.values().toList()) { f -> FilterChip(selected = f == filter, onClick = { filter = f }, label = { Text(f.label) }) } }
            Spacer(Modifier.height(12.dp)); Button(onClick = {
                runCatching {
                    val corrected = if (opencvAvailable) ImageProcessor.warp(page.originalBitmap, corners) else page.originalBitmap.copy(Bitmap.Config.ARGB_8888, false)
                    val output = if (opencvAvailable) ImageProcessor.applyFilter(corrected, filter) else corrected
                    onSave(page.copy(bitmap = output, corners = corners, filter = filter))
                }.onFailure { onError("Could not apply adjustments: ${it.message ?: "unknown error"}") }
            }, modifier = Modifier.fillMaxWidth().height(54.dp), shape = RoundedCornerShape(18.dp)) { Text("Apply & Save") }
        }
    }

    @Composable
    private fun CornerEditor(quad: Quad, imageWidth: Int, imageHeight: Int, onChange: (Quad) -> Unit) {
        Canvas(Modifier.fillMaxSize().pointerInput(quad, imageWidth, imageHeight) { detectDragGestures { change, drag ->
            change.consume()
            val content = fitRect(size.width.toFloat(), size.height.toFloat(), imageWidth.toFloat(), imageHeight.toFloat())
            val sourcePoint = PointF(((change.position.x - content.left) / content.width * imageWidth).coerceIn(0f, imageWidth.toFloat()), ((change.position.y - content.top) / content.height * imageHeight).coerceIn(0f, imageHeight.toFloat()))
            val index = quad.points.indices.minBy { i -> val dx = quad.points[i].x - sourcePoint.x; val dy = quad.points[i].y - sourcePoint.y; dx * dx + dy * dy }
            val next = quad.points.toMutableList(); next[index] = PointF((next[index].x + drag.x / content.width * imageWidth).coerceIn(0f, imageWidth.toFloat()), (next[index].y + drag.y / content.height * imageHeight).coerceIn(0f, imageHeight.toFloat())); onChange(Quad(next))
        } }) {
            val content = fitRect(size.width, size.height, imageWidth.toFloat(), imageHeight.toFloat())
            fun map(p: PointF) = androidx.compose.ui.geometry.Offset(content.left + p.x / imageWidth * content.width, content.top + p.y / imageHeight * content.height)
            fun DrawScope.line(a: PointF, b: PointF) = drawLine(Color.White, map(a), map(b), strokeWidth = 4f)
            line(quad.points[0], quad.points[1]); line(quad.points[1], quad.points[2]); line(quad.points[2], quad.points[3]); line(quad.points[3], quad.points[0]); quad.points.forEach { drawCircle(Color.White, 14f, map(it)) }
        }
    }

    private data class RectF(val left: Float, val top: Float, val width: Float, val height: Float)
    private fun fitRect(viewW: Float, viewH: Float, imageW: Float, imageH: Float): RectF { val scale = minOf(viewW / imageW, viewH / imageH); val w = imageW * scale; val h = imageH * scale; return RectF((viewW - w) / 2f, (viewH - h) / 2f, w, h) }
}

@Composable
private fun DevOSTheme(content: @Composable () -> Unit) = MaterialTheme(colorScheme = darkColorScheme(primary = Color(0xFFB7C7FF), secondary = Color(0xFF8DE8D0), surface = Color(0xFF0F1218), background = Color(0xFF090B10)), content = content)