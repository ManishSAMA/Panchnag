package com.example.jainpanchang.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.jainpanchang.data.PanchangRepository
import com.example.jainpanchang.data.local.DailyPanchangEntity
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalDate

class MainScreenViewModel(private val panchangRepository: PanchangRepository) : ViewModel() {
    private val _uiState = MutableStateFlow<MainScreenUiState>(MainScreenUiState.Loading)
    val uiState: StateFlow<MainScreenUiState> = _uiState.asStateFlow()

    init {
        loadTodayPanchang()
    }

    private fun loadTodayPanchang() {
        viewModelScope.launch {
            try {
                // Hardcoded lat/lon for demo (Mumbai)
                val panchang = panchangRepository.getDailyPanchang(
                    date = LocalDate.now(),
                    lat = 19.0760,
                    lon = 72.8777
                )
                _uiState.value = MainScreenUiState.Success(panchang)
            } catch (e: Exception) {
                _uiState.value = MainScreenUiState.Error(e)
            }
        }
    }
}

sealed interface MainScreenUiState {
    object Loading : MainScreenUiState
    data class Error(val throwable: Throwable) : MainScreenUiState
    data class Success(val data: DailyPanchangEntity) : MainScreenUiState
}
