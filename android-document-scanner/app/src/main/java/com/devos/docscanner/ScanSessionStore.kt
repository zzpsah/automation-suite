package com.devos.docscanner

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.PointF
import java.io.File
import java.util.UUID

object ScanSessionStore {
    private const val DIR = "scan-session"
    private const val INDEX = "index.txt"

    fun save(context: Context, pages: List<ScanPage>) {
        val dir = File(context.filesDir, DIR).apply { mkdirs() }
        dir.listFiles().orEmpty().forEach { it.delete() }
        val index = StringBuilder()
        pages.forEach { page ->
            val id = UUID.randomUUID().toString()
            File(dir, "$id-original.jpg").outputStream().use { page.originalBitmap.compress(Bitmap.CompressFormat.JPEG, 94, it) }
            File(dir, "$id-page.jpg").outputStream().use { page.bitmap.compress(Bitmap.CompressFormat.JPEG, 94, it) }
            index.append(id).append('|').append(page.filter.name).append('|')
            index.append(page.corners.points.joinToString(",") { "${it.x}:${it.y}" }).append('\n')
        }
        File(dir, INDEX).writeText(index.toString())
    }

    fun load(context: Context): List<ScanPage> = runCatching {
        val dir = File(context.filesDir, DIR)
        val index = File(dir, INDEX)
        if (!index.exists()) return emptyList()
        index.readLines().mapNotNull { line ->
            val fields = line.split('|')
            if (fields.size < 3) return@mapNotNull null
            val id = fields[0]
            val original = BitmapFactory.decodeFile(File(dir, "$id-original.jpg").absolutePath) ?: return@mapNotNull null
            val bitmap = BitmapFactory.decodeFile(File(dir, "$id-page.jpg").absolutePath) ?: return@mapNotNull null
            val points = fields[2].split(',').mapNotNull { pair ->
                val xy = pair.split(':')
                if (xy.size != 2) null else {
                    val x = xy[0].toFloatOrNull(); val y = xy[1].toFloatOrNull()
                    if (x == null || y == null) null else PointF(x, y)
                }
            }
            if (points.size != 4) null else ScanPage(original, bitmap, Quad(points), runCatching { ScanFilter.valueOf(fields[1]) }.getOrDefault(ScanFilter.AUTO))
        }
    }.getOrDefault(emptyList())

    fun clear(context: Context) { File(context.filesDir, DIR).deleteRecursively() }
}
