package com.devos.docscanner

import android.graphics.Bitmap
import android.graphics.PointF
import org.opencv.android.Utils
import org.opencv.core.*
import org.opencv.imgproc.Imgproc
import kotlin.math.hypot

object ImageProcessor {
    fun detectDocument(bitmap: Bitmap): Quad? {
        val src = Mat(); Utils.bitmapToMat(bitmap, src)
        val gray = Mat(); Imgproc.cvtColor(src, gray, Imgproc.COLOR_RGBA2GRAY)
        Imgproc.GaussianBlur(gray, gray, Size(5.0, 5.0), 0.0)
        val edges = Mat(); Imgproc.Canny(gray, edges, 55.0, 170.0)
        val contours = ArrayList<MatOfPoint>(); Imgproc.findContours(edges, contours, Mat(), Imgproc.RETR_LIST, Imgproc.CHAIN_APPROX_SIMPLE)
        val imageArea = src.width() * src.height().toDouble()
        for (c in contours.sortedByDescending { Imgproc.contourArea(it) }.take(20)) {
            val pts = c.toArray().map { Point(it.x, it.y) }.toTypedArray()
            val source = MatOfPoint2f(*pts)
            val approx = MatOfPoint2f(); Imgproc.approxPolyDP(source, approx, 0.02 * Imgproc.arcLength(source, true), true)
            if (approx.total() == 4L && Imgproc.contourArea(approx) > imageArea * 0.12) return Quad(order(approx.toArray().map { PointF(it.x.toFloat(), it.y.toFloat()) }))
        }
        return null
    }
    private fun order(p: List<PointF>): List<PointF> {
        val tl = p.minBy { it.x + it.y }; val br = p.maxBy { it.x + it.y }
        val tr = p.minBy { it.y - it.x }; val bl = p.maxBy { it.y - it.x }
        return listOf(tl, tr, br, bl)
    }
    fun warp(bitmap: Bitmap, quad: Quad): Bitmap {
        val src = Mat(); Utils.bitmapToMat(bitmap, src); val p = quad.points
        fun d(a: PointF, b: PointF) = hypot((a.x - b.x).toDouble(), (a.y - b.y).toDouble())
        val w = maxOf(d(p[0], p[1]), d(p[3], p[2])).coerceAtLeast(1.0).toInt()
        val h = maxOf(d(p[0], p[3]), d(p[1], p[2])).coerceAtLeast(1.0).toInt()
        val from = MatOfPoint2f(Point(p[0].x.toDouble(), p[0].y.toDouble()), Point(p[1].x.toDouble(), p[1].y.toDouble()), Point(p[2].x.toDouble(), p[2].y.toDouble()), Point(p[3].x.toDouble(), p[3].y.toDouble()))
        val to = MatOfPoint2f(Point(0.0, 0.0), Point(w.toDouble(), 0.0), Point(w.toDouble(), h.toDouble()), Point(0.0, h.toDouble()))
        val out = Mat(); Imgproc.warpPerspective(src, out, Imgproc.getPerspectiveTransform(from, to), Size(w.toDouble(), h.toDouble()), Imgproc.INTER_CUBIC)
        return Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888).also { Utils.matToBitmap(out, it) }
    }
    fun applyFilter(bitmap: Bitmap, filter: ScanFilter): Bitmap {
        if (filter == ScanFilter.ORIGINAL) return bitmap.copy(Bitmap.Config.ARGB_8888, false)
        val src = Mat(); Utils.bitmapToMat(bitmap, src)
        when (filter) {
            ScanFilter.GRAYSCALE -> { Imgproc.cvtColor(src, src, Imgproc.COLOR_RGBA2GRAY); Imgproc.cvtColor(src, src, Imgproc.COLOR_GRAY2RGBA) }
            ScanFilter.BINARY -> { Imgproc.cvtColor(src, src, Imgproc.COLOR_RGBA2GRAY); Imgproc.GaussianBlur(src, src, Size(3.0, 3.0), 0.0); Imgproc.adaptiveThreshold(src, src, 255.0, Imgproc.ADAPTIVE_THRESH_GAUSSIAN_C, Imgproc.THRESH_BINARY, 31, 11.0); Imgproc.cvtColor(src, src, Imgproc.COLOR_GRAY2RGBA) }
            ScanFilter.AUTO -> { val gray = Mat(); Imgproc.cvtColor(src, gray, Imgproc.COLOR_RGBA2GRAY); val clahe = Imgproc.createCLAHE(2.0, Size(8.0, 8.0)); clahe.apply(gray, gray); Imgproc.cvtColor(gray, src, Imgproc.COLOR_GRAY2RGBA) }
            else -> Unit
        }
        return Bitmap.createBitmap(src.cols(), src.rows(), Bitmap.Config.ARGB_8888).also { Utils.matToBitmap(src, it) }
    }
}
