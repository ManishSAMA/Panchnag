package com.example.jainpanchang.ui.choghadiya

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.jainpanchang.data.PanchangRepository
import com.example.jainpanchang.data.UserPreferencesRepository
import com.example.jainpanchang.domain.ChoghadiyaSlot
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import java.time.LocalDate

class ChoghadiyaViewModel(
    private val panchangRepository: PanchangRepository,
    private val userPrefsRepository: UserPreferencesRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<ChoghadiyaUiState>(ChoghadiyaUiState.Loading)
    val uiState: StateFlow<ChoghadiyaUiState> = _uiState.asStateFlow()

    private var currentDate = LocalDate.now()
    private var currentLat = 0.0
    private var currentLon = 0.0

    init {
        viewModelScope.launch {
            userPrefsRepository.userLocationFlow.collectLatest { locationPrefs ->
                currentLat = locationPrefs.latitude
                currentLon = locationPrefs.longitude
                loadChoghadiyaData()
            }
        }
    }

    fun loadPreviousDay() {
        currentDate = currentDate.minusDays(1)
        loadChoghadiyaData()
    }

    fun loadNextDay() {
        currentDate = currentDate.plusDays(1)
        loadChoghadiyaData()
    }

    private fun loadChoghadiyaData() {
        viewModelScope.launch {
            _uiState.value = ChoghadiyaUiState.Loading
            try {
                val slots = panchangRepository.getChoghadiyaSlots(
                    date = currentDate,
                    lat = currentLat,
                    lon = currentLon
                )
                
                val daySlots = slots.filter { it.period == "day" }
                val nightSlots = slots.filter { it.period == "night" }

                _uiState.value = ChoghadiyaUiState.Success(
                    date = currentDate,
                    daySlots = daySlots,
                    nightSlots = nightSlots
                )
            } catch (e: Exception) {
                _uiState.value = ChoghadiyaUiState.Error(e)
            }
        }
    }
}

sealed interface ChoghadiyaUiState {
    object Loading : ChoghadiyaUiState
    data class Error(val throwable: Throwable) : ChoghadiyaUiState
    data class Success(val date: LocalDate, val daySlots: List<ChoghadiyaSlot>, val nightSlots: List<ChoghadiyaSlot>) : ChoghadiyaUiState
}
