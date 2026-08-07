package com.example.jainpanchang.ui.calendar

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.jainpanchang.data.PanchangRepository
import com.example.jainpanchang.data.UserPreferencesRepository
import com.example.jainpanchang.data.dataStore
import com.example.jainpanchang.data.local.DailyPanchangEntity
import com.example.jainpanchang.data.local.PanchangDatabase
import java.time.format.TextStyle
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CalendarScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val database = PanchangDatabase.getDatabase(context)
    val repository = PanchangRepository(database.panchangDao())
    val userPrefsRepo = UserPreferencesRepository(context.dataStore)
    val viewModel: CalendarViewModel = viewModel { CalendarViewModel(repository, userPrefsRepo) }

    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Monthly Calendar", fontWeight = FontWeight.Bold) },
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
                is CalendarUiState.Loading -> {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                }
                is CalendarUiState.Success -> {
                    val successState = state as CalendarUiState.Success
                    Column {
                        MonthHeader(
                            monthName = "${successState.month.month.getDisplayName(TextStyle.FULL, Locale.getDefault())} ${successState.month.year}",
                            onPrev = { viewModel.loadPreviousMonth() },
                            onNext = { viewModel.loadNextMonth() }
                        )
                        CalendarGrid(days = successState.days, firstDayOfWeek = successState.month.atDay(1).dayOfWeek.value)
                    }
                }
                is CalendarUiState.Error -> {
                    Text(
                        text = "Error loading calendar",
                        color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.align(Alignment.Center)
                    )
                }
            }
        }
    }
}

@Composable
fun MonthHeader(monthName: String, onPrev: () -> Unit, onNext: () -> Unit) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        IconButton(onClick = onPrev) {
            Icon(Icons.Default.KeyboardArrowLeft, contentDescription = "Previous Month")
        }
        Text(text = monthName, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        IconButton(onClick = onNext) {
            Icon(Icons.Default.KeyboardArrowRight, contentDescription = "Next Month")
        }
    }
}

@Composable
fun CalendarGrid(days: List<DailyPanchangEntity>, firstDayOfWeek: Int) {
    // firstDayOfWeek: 1 = Monday, 7 = Sunday. We want Sunday = 0
    val startPadding = if (firstDayOfWeek == 7) 0 else firstDayOfWeek
    val totalCells = startPadding + days.size
    val weeks = Math.ceil(totalCells / 7.0).toInt()

    val dayNames = listOf("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")

    Column(modifier = Modifier.padding(8.dp)) {
        Row(modifier = Modifier.fillMaxWidth()) {
            dayNames.forEach { dayName ->
                Text(
                    text = dayName,
                    modifier = Modifier.weight(1f),
                    textAlign = TextAlign.Center,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
        Spacer(modifier = Modifier.height(8.dp))

        LazyVerticalGrid(
            columns = GridCells.Fixed(7),
            modifier = Modifier.fillMaxSize()
        ) {
            items(startPadding) {
                Box(modifier = Modifier.aspectRatio(0.8f)) // Empty box
            }
            items(days) { day ->
                CalendarDayCell(day = day)
            }
        }
    }
}

@Composable
fun CalendarDayCell(day: DailyPanchangEntity) {
    val dateNum = day.dateString.substringAfterLast("-")
    
    // Highlight Ashtami (8) and Chaturdashi (14) for Jain importance (roughly based on tithi name)
    // Tithis are 1-30. 8, 14, 23, 29 are typically Ashtami and Chaturdashi
    val isImportantJainTithi = day.tithiName.contains("Ashtami") || day.tithiName.contains("Chaturdashi")
    
    Card(
        modifier = Modifier
            .padding(2.dp)
            .aspectRatio(0.7f),
        colors = CardDefaults.cardColors(
            containerColor = if (isImportantJainTithi) MaterialTheme.colorScheme.secondary else MaterialTheme.colorScheme.surfaceVariant
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Column(
            modifier = Modifier.padding(4.dp).fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                text = dateNum,
                fontWeight = FontWeight.Bold,
                fontSize = 14.sp,
                color = if (isImportantJainTithi) MaterialTheme.colorScheme.onSecondary else MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                text = day.tithiName.take(3), // Abbreviated Tithi
                fontSize = 10.sp,
                lineHeight = 12.sp,
                textAlign = TextAlign.Center,
                color = if (isImportantJainTithi) MaterialTheme.colorScheme.onSecondary else MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
