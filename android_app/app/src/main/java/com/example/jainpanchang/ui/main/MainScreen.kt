package com.example.jainpanchang.ui.main

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.jainpanchang.data.PanchangRepository
import com.example.jainpanchang.data.local.DailyPanchangEntity
import com.example.jainpanchang.data.local.PanchangDatabase
import com.example.jainpanchang.theme.JainPanchangTheme

@Composable
fun MainScreen(
  onItemClick: (NavKey) -> Unit,
  modifier: Modifier = Modifier,
) {
  val context = LocalContext.current
  // In a real app, use Hilt or Dagger for DI
  val database = PanchangDatabase.getDatabase(context)
  val repository = PanchangRepository(database.panchangDao())
  val viewModel: MainScreenViewModel = viewModel { MainScreenViewModel(repository) }

  val state by viewModel.uiState.collectAsStateWithLifecycle()
  when (state) {
    MainScreenUiState.Loading -> {
      Text("Loading Panchang...", modifier = modifier)
    }
    is MainScreenUiState.Success -> {
      MainScreenContent(data = (state as MainScreenUiState.Success).data, modifier = modifier)
    }
    is MainScreenUiState.Error -> {
      Text("Error loading data: ${(state as MainScreenUiState.Error).throwable.message}")
    }
  }
}

@Composable
internal fun MainScreenContent(data: DailyPanchangEntity, modifier: Modifier = Modifier) {
  Column(modifier = modifier.padding(16.dp)) { 
      Text(text = "Date: ${data.dateString}")
      Text(text = "Tithi: ${data.tithiName}")
      Text(text = "Nakshatra: ${data.nakshatraName} (Pada ${data.nakshatraPada})")
      Text(text = "Yoga: ${data.yogaName}")
      Text(text = "Karana: ${data.karanaName}")
      Text(text = "Vara: ${data.varaName}")
      Text(text = "Hindu Month: ${data.hinduMonthCommon} (${data.hinduMonthSanskrit})")
  }
}
