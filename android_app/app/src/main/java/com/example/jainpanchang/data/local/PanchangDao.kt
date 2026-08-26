package com.example.jainpanchang.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface PanchangDao {
    @Query("SELECT * FROM daily_panchang WHERE dateString = :date AND ABS(latitude - :lat) < 0.01 AND ABS(longitude - :lon) < 0.01 LIMIT 1")
    suspend fun getDailyPanchang(date: String, lat: Double, lon: Double): DailyPanchangEntity?

    @Query("SELECT * FROM daily_panchang WHERE dateString BETWEEN :startDate AND :endDate AND ABS(latitude - :lat) < 0.01 AND ABS(longitude - :lon) < 0.01 ORDER BY dateString ASC")
    fun getPanchangForDateRange(startDate: String, endDate: String, lat: Double, lon: Double): Flow<List<DailyPanchangEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDailyPanchang(panchang: DailyPanchangEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPanchangList(panchangList: List<DailyPanchangEntity>)
}
