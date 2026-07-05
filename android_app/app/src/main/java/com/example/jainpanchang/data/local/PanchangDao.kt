package com.example.jainpanchang.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface PanchangDao {
    @Query("SELECT * FROM daily_panchang WHERE dateString = :date")
    suspend fun getDailyPanchang(date: String): DailyPanchangEntity?

    @Query("SELECT * FROM daily_panchang WHERE dateString BETWEEN :startDate AND :endDate ORDER BY dateString ASC")
    fun getPanchangForDateRange(startDate: String, endDate: String): Flow<List<DailyPanchangEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDailyPanchang(panchang: DailyPanchangEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPanchangList(panchangList: List<DailyPanchangEntity>)
}
