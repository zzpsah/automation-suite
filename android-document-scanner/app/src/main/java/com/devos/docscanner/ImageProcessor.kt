package com.devos.docscanner

import android.graphics.Bitmap
import android.graphics.PointF
import org.opencv.android.Utils
import org.opencv.core.*
import org.opencv.imgproc.Imgproc
import kotlin.math.hypot

object ImageProcessor {
    fun detectDocument(bitmap: Bitmap): Quad? {
        if (bitmap.width < 80 || bitmap.height < 80) return null
        val scale = minOf(1.0, 1600.0 / maxOf(bitmap.width, bitmap.height).toDouble())
        val working = if (scale < 0.999) Bitmap.createScaledBitmap(bitmap, (bitmap.width * scale).toInt(), (bitmap.height * scale).toInt(), true) else bitmap
        val src = Mat(); val gray = Mat(); val edges = Mat(); val kernel = Mat(); val hierarchy = Mat()
        return try {
            Utils.bitmapToMat(working, src)
            Imgproc.cvtColor(src, gray, Imgproc.COLOR_RGBA2GRAY)
            Imgproc.GaussianBlur(gray, gray, Size(5.0, 5.0), 0.0)
            Imgproc.Canny(gray, edges, 45.0, 160.0)
            kernel.create(3, 3, CvType.CV_8U)
            Imgproc.morphologyEx(edges, edges, Imgproc.MORPH_CLOSE, kernel)
            val contours = ArrayList<MatOfPoint>()
            Imgproc.findContours(edges, contours, hierarchy, Imgproc.RETR_LIST, Imgproc.CHAIN_APPROX_SIMPLE)
            val imageArea = src.width() * src.height().toDouble()
            var best: Quad? = null
            var bestScore = 0.0
            contours.sortedByDescending { Imgproc.contourArea(it) }.take(80).forEach { contour ->
                val area = Imgproc.contourArea(contour)
                if (area < imageArea * 0.10) { contour.release(); return@forEach }
                val source = MatOfPoint2f(*contour.toArray().map { Point(it.x, it.y) }.toTypedArray())
                val approx = MatOfPoint2f()
                val perimeter = Imgproc.arcLength(source, true)
                Imgproc.approxPolyDP(source, approx, 0.018 * perimeter, true)
                if (approx.total() == 4L) {
                    val points = order(approx.toArray().map { PointF((it.x / scale).toFloat(), (it.y / scale).toFloat()) })
                    if (isConvex(points) && goodAngles(points)) {
                        val rectangularity = area / maxOf(1.0, boundingArea(points))
                        val edgePenalty = points.count { it.x < bitmap.width * .01f || it.x > bitmap.width * .99f || it.y < bitmap.height * .01f || it.y > bitmap.height * .99f } * .015
                        val score = (area / imageArea) * .72 + rectangularity * .28 - edgePenalty
                        if (score > bestScore) { bestScore = score; best = Quad(points) }
                    }
                }
                source.release(); approx.release(); contour.release()
            }
            if (bestScore >= .18) best else null
        } finally {
            src.release(); gray.release(); edges.release(); kernel.release(); hierarchy.release()
            if (working !== bitmap) working.recycle()
        }
    }

    private fun order(p: List<PointF>): List<PointF> {
        val tl = p.minBy { it.x + it.y }; val br = p.maxBy { it.x + it.y }
        val tr = p.minBy { it.y - it.x }; val bl = p.maxBy { it.y - it.x }
        return listOf(tl, tr, br, bl)
    }

    private fun boundingArea(p: List<PointF>): Double {
        val width = maxOf(hypot((p[1].x - p[0].x).toDouble(), (p[1].y - p[0].y).toDouble()), hypot((p[2].x - p[3].x).toDouble(), (p[2].y - p[3].y).toDouble()))
        val height = maxOf(hypot((p[3].x - p[0].x).toDouble(), (p[3].y - p[0].y).toDouble()), hypot((p[2].x - p[1].x).toDouble(), (p[2].y - p[1].y).toDouble()))
        return width * height
    }

    private fun isConvex(p: List<PointF>): Boolean {
        val signs = p.indices.map { i ->
            val a = p[i]; val b = p[(i + 1) % 4]; val c = p[(i + 2) % 4]
            (b.x - a.x) * (c.y - b.y) - (b.y - a.y) * (c.x - b.x)
        }
        return signs.all { it > 0 } || signs.all { it < 0 }
    }

    private fun goodAngles(p: List<PointF>): Boolean {
        fun angle(a: PointF, b: PointF, c: PointF): Double {
            val abx = (a.x - b.x).toDouble(); val aby = (a.y - b.y).toDouble()
            val cbx = (c.x - b.x).toDouble(); val cby = (c.y - b.y).toDouble()
            val denom = hypot(abx, aby) * hypot(cbx, cby)
            if (denom == 0.0) return 0.0
            val cosine = ((abx * cbx + aby * cby) / denom).coerceIn(-1.0, 1.0)
            return Math.toDegrees(kotlin.math.acos(cosine))
        }
        return p.indices.all { i -> angle(p[(i + 3) % 4], p[i], p[(i + 1) % 4]) in 45.0..135.0 }
    }

    fun warp(bitmap: Bitmap, quad: Quad): Bitmap {
        val src = Mat(); val from = MatOfPoint2f(); val to = MatOfPoint2f(); val out = Mat()
        return try {
            Utils.bitmapToMat(bitmap, src); val p = quad.points
            fun d(a: PointF, b: PointF) = hypot((a.x - b.x).toDouble(), (a.y - b.y).toDouble())
            val w = maxOf(d(p[0], p[1]), d(p[3], p[2])).coerceAtLeast(1.0).coerceAtMost(8000.0).toInt()
            val h = maxOf(d(p[0], p[3]), d(p[1], p[2])).coerceAtLeast(1.0).coerceAtMost(8000.0).toInt()
            from.fromArray(*p.map { Point(it.x.toDouble(), it.y.toDouble()) }.toTypedArray())
            to.fromArray(Point(0.0, 0.0), Point((w - 1).toDouble(), 0.0), Point((w - 1).toDouble(), (h - 1).toDouble()), Point(0.0, (h - 1).toDouble()))
            val transform = Imgproc.getPerspectiveTransform(from, to)
            try { Imgproc.warpPerspective(src, out, transform, Size(w.toDouble(), h.toDouble()), Imgproc.INTER_CUBIC, Core.BORDER_REPLICATE) }
            finally { transform.release() }
            Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also { Utils.matToBitmap(out, it) }
        } finally { src.release(); from.release(); to.release(); out.release() }
    }

    fun applyFilter(bitmap: Bitmap, filter: ScanFilter): Bitmap {
        if (filter == ScanFilter.ORIGINAL) return bitmap.copy(Bitmap.Config.ARGB_8888, false)
        val src = Mat(); val gray = Mat()
        return try {
            Utils.bitmapToMat(bitmap, src)
            when (filter) {
                ScanFilter.GRAYSCALE -> { Imgproc.cvtColor(src, gray, Imgproc.COLOR_RGBA2GRAY); Imgproc.cvtColor(gray, src, Imgproc.COLOR_GRAY2RGBA) }
                ScanFilter.BINARY -> { Imgproc.cvtColor(src, gray, Imgproc.COLOR_RGBA2GRAY); Imgproc.GaussianBlur(gray, gray, Size(3.0, 3.0), 0.0); Imgproc.adaptiveThreshold(gray, gray, 255.0, Imgproc.ADAPTIVE_THRESH_GAUSSIAN_C, Imgproc.THRESH_BINARY, 31, 9.0); Imgproc.cvtColor(gray, src, Imgproc.COLOR_GRAY2RGBA) }
                ScanFilter.AUTO -> { Imgproc.cvtColor(src, gray, Imgproc.COLOR_RGBA2GRAY); val clahe = Imgproc.createCLAHE(2.2, Size(8.0, 8.0)); clahe.apply(gray, gray); Imgproc.cvtColor(gray, src, Imgproc.COLOR_GRAY2RGBA) }
                ScanFilter.ORIGINAL -> Unit
            }
            Bitmap.createBitmap(src.cols(), src.rows(), Bitmap.Config.ARGB_8888).also { Utils.matToBitmap(src, it) }
        } finally { src.release(); gray.release() }
    }
}