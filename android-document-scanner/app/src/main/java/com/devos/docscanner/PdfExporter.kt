package com.devos.docscanner

import android.content.Context
import android.graphics.pdf.PdfDocument
import android.net.Uri
import java.io.File

object PdfExporter {
    fun createTempPdf(context: Context, pages: List<ScanPage>): File? {
        if (pages.isEmpty()) return null
        val file = File(context.cacheDir, "DevOS-Scan-${System.currentTimeMillis()}.pdf")
        writePdf(pages, file.outputStream())
        return file
    }

    fun writeToUri(context: Context, pages: List<ScanPage>, uri: Uri): Boolean {
        if (pages.isEmpty()) return false
        return runCatching {
            context.contentResolver.openOutputStream(uri)?.use { writePdf(pages, it) } ?: error("Unable to open destination")
            true
        }.getOrDefault(false)
    }

    private fun writePdf(pages: List<ScanPage>, output: java.io.OutputStream) {
        val doc = PdfDocument()
        try {
            pages.forEachIndexed { index, page ->
                val bitmap = page.bitmap
                val info = PdfDocument.PageInfo.Builder(bitmap.width, bitmap.height, index + 1).create()
                val pdfPage = doc.startPage(info)
                pdfPage.canvas.drawBitmap(bitmap, 0f, 0f, null)
                doc.finishPage(pdfPage)
            }
            doc.writeTo(output)
        } finally { doc.close() }
    }
}
