package com.example.jainpanchang.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.doublePreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "user_prefs")

data class UserLocationPrefs(
    val latitude: Double,
    val longitude: Double,
    val cityName: String
)

class UserPreferencesRepository(private val dataStore: DataStore<Preferences>) {
    
    companion object {
        val LATITUDE_KEY = doublePreferencesKey("latitude")
        val LONGITUDE_KEY = doublePreferencesKey("longitude")
        val CITY_NAME_KEY = stringPreferencesKey("city_name")
        val AYANAMSA_KEY = stringPreferencesKey("ayanamsa")
        
        // Default to Mumbai
        const val DEFAULT_LAT = 19.0760
        const val DEFAULT_LON = 72.8777
        const val DEFAULT_CITY = "Mumbai"
        const val DEFAULT_AYANAMSA = "Lahiri"
    }

    val userLocationFlow: Flow<UserLocationPrefs> = dataStore.data.map { preferences ->
        UserLocationPrefs(
            latitude = preferences[LATITUDE_KEY] ?: DEFAULT_LAT,
            longitude = preferences[LONGITUDE_KEY] ?: DEFAULT_LON,
            cityName = preferences[CITY_NAME_KEY] ?: DEFAULT_CITY
        )
    }

    val ayanamsaFlow: Flow<String> = dataStore.data.map { preferences ->
        preferences[AYANAMSA_KEY] ?: DEFAULT_AYANAMSA
    }

    suspend fun updateLocation(lat: Double, lon: Double, city: String) {
        dataStore.edit { preferences ->
            preferences[LATITUDE_KEY] = lat
            preferences[LONGITUDE_KEY] = lon
            preferences[CITY_NAME_KEY] = city
        }
    }

    suspend fun updateAyanamsa(ayanamsa: String) {
        dataStore.edit { preferences ->
            preferences[AYANAMSA_KEY] = ayanamsa
        }
    }
}
