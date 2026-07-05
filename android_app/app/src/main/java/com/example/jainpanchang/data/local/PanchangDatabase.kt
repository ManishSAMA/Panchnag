package com.example.jainpanchang.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(entities = [DailyPanchangEntity::class], version = 1, exportSchema = false)
abstract class PanchangDatabase : RoomDatabase() {
    abstract fun panchangDao(): PanchangDao

    companion object {
        @Volatile
        private var INSTANCE: PanchangDatabase? = null

        fun getDatabase(context: Context): PanchangDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    PanchangDatabase::class.java,
                    "panchang_database"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
