package com.devos.docscanner

import android.content.Context
import android.graphics.pdf.PdfDocument
import android.net.Uri
import java.io.File

object PdfExporter {
    fun export(context: Context, pages: List<ScanPage>): Uri? {
        if (pages.isEmpty()) return null
        val doc = PdfDocument()
        pages.forEachIndexed { index, page ->
            val bitmap = page.bitmap
            val info = PdfDocument.PageInfo.Builder(bitmap.width, bitmap.height, index + 1).create()
            val pdfPage = doc.startPage(info)
            pdfPage.canvas.drawBitmap(bitmap, 0f, 0f, null)
            doc.finishPage(pdfPage)
        }
        val file = File(context.cacheDir, "DevOS-Scan-${System.currentTimeMillis()}.pdf")
        file.outputStream().use { doc.writeTo(it) }
        doc.close()
        return Uri.fromFile(file)
    }
}
