package com.devos.docscanner

import android.graphics.Bitmap
import android.graphics.PointF

data class Quad(val points: List<PointF>) { init { require(points.size == 4) } }
enum class ScanFilter(val label: String) { ORIGINAL("Original"), AUTO("Auto"), GRAYSCALE("Mono"), BINARY("B&W") }
data class ScanPage(val bitmap: Bitmap, val corners: Quad, val filter: ScanFilter = ScanFilter.AUTO)
interface OcrEngine { suspend fun extractText(bitmap: Bitmap): String }
