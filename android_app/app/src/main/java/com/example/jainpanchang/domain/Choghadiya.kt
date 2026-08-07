package com.example.jainpanchang.domain

import java.time.LocalDate

data class ChoghadiyaSlot(
    val name: String,
    val meaning: String,
    val nature: String,
    val startJd: Double,
    val endJd: Double,
    val period: String
)

class Choghadiya {
    
    companion object {
        val DAY_CHOGHADIYA_ORDER = listOf("Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog")
        val NIGHT_CHOGHADIYA_ORDER = listOf("Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg")
        
        val CHOGHADIYA_MEANINGS = mapOf(
            "Udveg" to "Tension", "Amrit" to "Nectar", "Rog" to "Illness",
            "Labh" to "Gain", "Shubh" to "Auspicious", "Char" to "Movement", "Kaal" to "Loss"
        )
        val CHOGHADIYA_NATURE = mapOf(
            "Udveg" to "inauspicious", "Amrit" to "auspicious", "Rog" to "inauspicious",
            "Labh" to "auspicious", "Shubh" to "auspicious", "Char" to "neutral", "Kaal" to "inauspicious"
        )
        
        // Vara index: Sun=0 ... Sat=6 -> starting index in the day/night Choghadiya order
        val DAY_START_IDX = listOf(0, 3, 6, 2, 5, 1, 4)
        val NIGHT_START_IDX = listOf(0, 2, 4, 6, 5, 3, 1)
    }

    fun calculateChoghadiyaSlots(
        sunriseJd: Double,
        sunsetJd: Double,
        nextSunriseJd: Double,
        weekdayIndex: Int
    ): List<ChoghadiyaSlot> {
        val dayStart = DAY_START_IDX[weekdayIndex]
        val nightStart = NIGHT_START_IDX[weekdayIndex]

        val daySlots = makeSlots(sunriseJd, sunsetJd, DAY_CHOGHADIYA_ORDER, dayStart, "day")
        val nightSlots = makeSlots(sunsetJd, nextSunriseJd, NIGHT_CHOGHADIYA_ORDER, nightStart, "night")
        
        return daySlots + nightSlots
    }

    private fun makeSlots(
        startJd: Double,
        endJd: Double,
        choghadiyaOrder: List<String>,
        startIdx: Int,
        period: String
    ): List<ChoghadiyaSlot> {
        val slotDuration = (endJd - startJd) / 8.0
        val slots = mutableListOf<ChoghadiyaSlot>()
        
        for (i in 0 until 8) {
            val name = choghadiyaOrder[(startIdx + i) % 7]
            val slotStart = startJd + (i * slotDuration)
            val slotEnd = startJd + ((i + 1) * slotDuration)
            
            slots.add(
                ChoghadiyaSlot(
                    name = name,
                    meaning = CHOGHADIYA_MEANINGS[name] ?: "",
                    nature = CHOGHADIYA_NATURE[name] ?: "neutral",
                    startJd = slotStart,
                    endJd = slotEnd,
                    period = period
                )
            )
        }
        return slots
    }
}
