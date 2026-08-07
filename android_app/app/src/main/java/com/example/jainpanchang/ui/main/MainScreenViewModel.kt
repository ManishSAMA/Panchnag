package com.example.jainpanchang.ui.main

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

class MainScreenViewModel(
    private val panchangRepository: PanchangRepository,
    private val userPrefsRepository: UserPreferencesRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow<MainScreenUiState>(MainScreenUiState.Loading)
    val uiState: StateFlow<MainScreenUiState> = _uiState.asStateFlow()

    init {
        observeLocationAndLoadPanchang()
    }

    private fun observeLocationAndLoadPanchang() {
        viewModelScope.launch {
            userPrefsRepository.userLocationFlow.collectLatest { locationPrefs ->
                _uiState.value = MainScreenUiState.Loading
                try {
                    val panchang = panchangRepository.getDailyPanchang(
                        date = LocalDate.now(),
                        lat = locationPrefs.latitude,
                        lon = locationPrefs.longitude
                    )
                    _uiState.value = MainScreenUiState.Success(panchang, locationPrefs.cityName)
                } catch (e: Exception) {
                    _uiState.value = MainScreenUiState.Error(e)
                }
            }
        }
    }
}

sealed interface MainScreenUiState {
    object Loading : MainScreenUiState
    data class Error(val throwable: Throwable) : MainScreenUiState
    data class Success(val data: DailyPanchangEntity, val cityName: String) : MainScreenUiState
}
