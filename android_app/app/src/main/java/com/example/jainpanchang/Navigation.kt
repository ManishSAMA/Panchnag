package com.example.jainpanchang

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.example.jainpanchang.ui.calendar.CalendarScreen
import com.example.jainpanchang.ui.choghadiya.ChoghadiyaScreen
import com.example.jainpanchang.ui.location.LocationScreen
import com.example.jainpanchang.ui.main.MainScreen

@Composable
fun MainNavigation() {
    var selectedItem by rememberSaveable { mutableStateOf(0) }
    val items = listOf("Daily", "Calendar", "Choghadiya", "Location")
    val icons = listOf(
        Icons.Filled.Home,
        Icons.Filled.DateRange,
        Icons.Filled.Warning, // Replace with proper icon later
        Icons.Filled.LocationOn
    )

    Scaffold(
        bottomBar = {
            NavigationBar {
                items.forEachIndexed { index, item ->
                    NavigationBarItem(
                        icon = { Icon(icons[index], contentDescription = item) },
                        label = { Text(item) },
                        selected = selectedItem == index,
                        onClick = { selectedItem = index }
                    )
                }
            }
        }
    ) { paddingValues ->
        Box(modifier = Modifier.padding(paddingValues)) {
            when (selectedItem) {
                0 -> MainScreen(onItemClick = {})
                1 -> CalendarScreen()
                2 -> ChoghadiyaScreen()
                3 -> LocationScreen()
            }
        }
    }
}
