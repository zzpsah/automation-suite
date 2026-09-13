package com.devos.docscanner

import android.graphics.PointF
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class ScannerModelsTest {
    @Test
    fun quad_requires_exactly_four_points() {
        assertThrows(IllegalArgumentException::class.java) { Quad(emptyList()) }
        assertThrows(IllegalArgumentException::class.java) {
            Quad(listOf(PointF(), PointF(), PointF()))
        }
        assertEquals(4, Quad(listOf(PointF(), PointF(), PointF(), PointF())).points.size)
    }
}
