package com.example.jainpanchang.ui.main

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation3.runtime.NavKey
import com.example.jainpanchang.data.PanchangRepository
import com.example.jainpanchang.data.UserPreferencesRepository
import com.example.jainpanchang.data.dataStore
import com.example.jainpanchang.data.local.DailyPanchangEntity
import com.example.jainpanchang.data.local.PanchangDatabase

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    onItemClick: (NavKey) -> Unit,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    val database = PanchangDatabase.getDatabase(context)
    val repository = PanchangRepository(database.panchangDao())
    val userPrefsRepo = UserPreferencesRepository(context.dataStore)
    val viewModel: MainScreenViewModel = viewModel { MainScreenViewModel(repository, userPrefsRepo) }

    val state by viewModel.uiState.collectAsStateWithLifecycle()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Jain Panchang", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { padding ->
        Box(modifier = modifier.padding(padding).fillMaxSize()) {
            when (state) {
                MainScreenUiState.Loading -> {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                }
                is MainScreenUiState.Success -> {
                    val successState = state as MainScreenUiState.Success
                    MainScreenContent(data = successState.data, cityName = successState.cityName)
                }
                is MainScreenUiState.Error -> {
                    Text(
                        text = "Error loading data: ${(state as MainScreenUiState.Error).throwable.message}",
                        color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.align(Alignment.Center).padding(16.dp)
                    )
                }
            }
        }
    }
}

@Composable
internal fun MainScreenContent(data: DailyPanchangEntity, cityName: String, modifier: Modifier = Modifier) {
    LazyColumn(
        modifier = modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(imageVector = Icons.Default.LocationOn, contentDescription = "Location")
                    Spacer(modifier = Modifier.width(8.dp))
                    Column {
                        Text(text = cityName, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                        Text(text = data.dateString, style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
        }

        item {
            InfoCard(title = "Core Panchang", items = listOf(
                "Tithi" to data.tithiName,
                "Nakshatra" to "${data.nakshatraName} (Pada ${data.nakshatraPada})",
                "Yoga" to data.yogaName,
                "Karana" to data.karanaName,
                "Vara" to data.varaName
            ))
        }

        item {
            InfoCard(title = "Astrological Details", items = listOf(
                "Hindu Month" to "${data.hinduMonthCommon} (${data.hinduMonthSanskrit})"
            ))
        }
    }
}

@Composable
fun InfoCard(title: String, items: List<Pair<String, String>>) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
            Spacer(modifier = Modifier.height(12.dp))
            items.forEach { (label, value) ->
                Row(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(text = label, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(text = value, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
                }
                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant, thickness = 0.5.dp)
            }
        }
    }
}
