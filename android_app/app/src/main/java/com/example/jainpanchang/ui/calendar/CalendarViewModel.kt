package com.example.jainpanchang.ui.calendar

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.jainpanchang.data.PanchangRepository
import com.example.jainpanchang.data.UserPreferencesRepository
import com.example.jainpanchang.data.local.DailyPanchangEntity
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.YearMonth

class CalendarViewModel(
    private val panchangRepository: PanchangRepository,
    private val userPrefsRepository: UserPreferencesRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<CalendarUiState>(CalendarUiState.Loading)
    val uiState: StateFlow<CalendarUiState> = _uiState.asStateFlow()

    private var currentMonth = YearMonth.now()
    private var currentLat = 0.0
    private var currentLon = 0.0

    init {
        viewModelScope.launch {
            userPrefsRepository.userLocationFlow.collectLatest { locationPrefs ->
                currentLat = locationPrefs.latitude
                currentLon = locationPrefs.longitude
                loadMonthData(currentMonth)
            }
        }
    }

    fun loadPreviousMonth() {
        currentMonth = currentMonth.minusMonths(1)
        loadMonthData(currentMonth)
    }

    fun loadNextMonth() {
        currentMonth = currentMonth.plusMonths(1)
        loadMonthData(currentMonth)
    }

    private fun loadMonthData(month: YearMonth) {
        viewModelScope.launch {
            _uiState.value = CalendarUiState.Loading
            try {
                val daysInMonth = month.lengthOfMonth()
                val panchangList = mutableListOf<DailyPanchangEntity>()

                for (day in 1..daysInMonth) {
                    val date = month.atDay(day)
                    val panchang = panchangRepository.getDailyPanchang(
                        date = date,
                        lat = currentLat,
                        lon = currentLon
                    )
                    panchangList.add(panchang)
                }

                _uiState.value = CalendarUiState.Success(
                    month = month,
                    days = panchangList
                )
            } catch (e: Exception) {
                _uiState.value = CalendarUiState.Error(e)
            }
        }
    }
}

sealed interface CalendarUiState {
    object Loading : CalendarUiState
    data class Error(val throwable: Throwable) : CalendarUiState
    data class Success(val month: YearMonth, val days: List<DailyPanchangEntity>) : CalendarUiState
}
