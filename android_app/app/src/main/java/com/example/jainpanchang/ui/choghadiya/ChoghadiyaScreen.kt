package com.example.jainpanchang.ui.choghadiya

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowLeft
import androidx.compose.material.icons.filled.KeyboardArrowRight
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
import com.example.jainpanchang.data.PanchangRepository
import com.example.jainpanchang.data.UserPreferencesRepository
import com.example.jainpanchang.data.dataStore
import com.example.jainpanchang.data.local.PanchangDatabase
import com.example.jainpanchang.domain.ChoghadiyaSlot
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChoghadiyaScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val database = PanchangDatabase.getDatabase(context)
    val repository = PanchangRepository(database.panchangDao())
    val userPrefsRepo = UserPreferencesRepository(context.dataStore)
    val viewModel: ChoghadiyaViewModel = viewModel { ChoghadiyaViewModel(repository, userPrefsRepo) }

    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Choghadiya Muhurat", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { padding ->
        Box(
            modifier = modifier
                .padding(padding)
                .fillMaxSize()
        ) {
            when (state) {
                is ChoghadiyaUiState.Loading -> {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                }
                is ChoghadiyaUiState.Success -> {
                    val successState = state as ChoghadiyaUiState.Success
                    Column(modifier = Modifier.fillMaxSize()) {
                        DateHeader(
                            dateString = successState.date.format(DateTimeFormatter.ofPattern("EEEE, dd MMM yyyy")),
                            onPrev = { viewModel.loadPreviousDay() },
                            onNext = { viewModel.loadNextDay() }
                        )
                        LazyColumn(
                            modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            item { 
                                Text("Day Choghadiya", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, modifier = Modifier.padding(vertical = 8.dp))
                            }
                            items(successState.daySlots) { slot ->
                                ChoghadiyaCard(slot)
                            }
                            item { 
                                Spacer(modifier = Modifier.height(16.dp))
                                Text("Night Choghadiya", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, modifier = Modifier.padding(vertical = 8.dp))
                            }
                            items(successState.nightSlots) { slot ->
                                ChoghadiyaCard(slot)
                            }
                            item { Spacer(modifier = Modifier.height(16.dp)) }
                        }
                    }
                }
                is ChoghadiyaUiState.Error -> {
                    Text(
                        text = "Error loading Choghadiya data",
                        color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.align(Alignment.Center)
                    )
                }
            }
        }
    }
}

@Composable
fun DateHeader(dateString: String, onPrev: () -> Unit, onNext: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        IconButton(onClick = onPrev) {
            Icon(Icons.Default.KeyboardArrowLeft, contentDescription = "Previous Day")
        }
        Text(text = dateString, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        IconButton(onClick = onNext) {
            Icon(Icons.Default.KeyboardArrowRight, contentDescription = "Next Day")
        }
    }
}

@Composable
fun ChoghadiyaCard(slot: ChoghadiyaSlot) {
    val containerColor = when (slot.nature) {
        "auspicious" -> Color(0xFFE8F5E9) // Light Green
        "inauspicious" -> Color(0xFFFFEBEE) // Light Red
        else -> MaterialTheme.colorScheme.surfaceVariant
    }
    
    val textColor = when (slot.nature) {
        "auspicious" -> Color(0xFF2E7D32)
        "inauspicious" -> Color(0xFFC62828)
        else -> MaterialTheme.colorScheme.onSurfaceVariant
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = containerColor),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Row(
            modifier = Modifier.padding(16.dp).fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(text = slot.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = textColor)
                Text(text = slot.meaning, style = MaterialTheme.typography.bodySmall, color = textColor.copy(alpha = 0.8f))
            }
            Text(
                text = "${formatTimeFromJd(slot.startJd)} - ${formatTimeFromJd(slot.endJd)}",
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium,
                color = textColor
            )
        }
    }
}

// Basic formatter. Ideally uses Astronomy.jdToLocalTimeString but it's hard to inject here without moving logic to ViewModel
// A quick approximation for demo:
fun formatTimeFromJd(jd: Double): String {
    val jdOffset = jd + 0.5 + (5.5 / 24.0) // add IST offset
    val fraction = jdOffset - jdOffset.toLong()
    val totalSeconds = (fraction * 24 * 3600).toLong()
    val hours = totalSeconds / 3600
    val minutes = (totalSeconds % 3600) / 60
    val period = if (hours >= 12) "PM" else "AM"
    val h12 = if (hours % 12 == 0L) 12 else hours % 12
    return String.format("%02d:%02d %s", h12, minutes, period)
}
