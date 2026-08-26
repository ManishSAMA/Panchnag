package com.example.jainpanchang.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(
    tableName = "daily_panchang",
    primaryKeys = ["dateString", "latitude", "longitude"]
)
data class DailyPanchangEntity(
    val dateString: String, // Format: YYYY-MM-DD
    val latitude: Double = 0.0,
    val longitude: Double = 0.0,
    val julianDate: Double,
    val sunriseJd: Double,
    val sunsetJd: Double,
    val tithiIndex: Int,
    val tithiName: String,
    val tithiEndJd: Double,
    val nakshatraIndex: Int,
    val nakshatraName: String,
    val nakshatraEndJd: Double,
    val nakshatraPada: Int,
    val yogaIndex: Int,
    val yogaName: String,
    val yogaEndJd: Double,
    val karanaIndex: Int,
    val karanaName: String,
    val karanaStartJd: Double,
    val karanaEndJd: Double,
    val varaIndex: Int,
    val varaName: String,
    val hinduMonthSanskrit: String,
    val hinduMonthCommon: String
)
