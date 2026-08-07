package com.example.jainpanchang.ui.location

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation3.runtime.NavKey
import com.example.jainpanchang.data.UserPreferencesRepository
import com.example.jainpanchang.data.dataStore
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LocationScreen(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val userPrefsRepo = UserPreferencesRepository(context.dataStore)
    val scope = rememberCoroutineScope()
    
    val currentLocation by userPrefsRepo.userLocationFlow.collectAsStateWithLifecycle(
        initialValue = null
    )

    var cityName by remember(currentLocation) { mutableStateOf(currentLocation?.cityName ?: "") }
    var latitude by remember(currentLocation) { mutableStateOf(currentLocation?.latitude?.toString() ?: "") }
    var longitude by remember(currentLocation) { mutableStateOf(currentLocation?.longitude?.toString() ?: "") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Set Location", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                )
            )
        }
    ) { padding ->
        Column(
            modifier = modifier
                .padding(padding)
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            OutlinedTextField(
                value = cityName,
                onValueChange = { cityName = it },
                label = { Text("City Name") },
                modifier = Modifier.fillMaxWidth()
            )

            OutlinedTextField(
                value = latitude,
                onValueChange = { latitude = it },
                label = { Text("Latitude") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth()
            )

            OutlinedTextField(
                value = longitude,
                onValueChange = { longitude = it },
                label = { Text("Longitude") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                modifier = Modifier.fillMaxWidth()
            )

            Button(
                onClick = {
                    val lat = latitude.toDoubleOrNull() ?: 0.0
                    val lon = longitude.toDoubleOrNull() ?: 0.0
                    scope.launch {
                        userPrefsRepo.updateLocation(lat, lon, cityName)
                    }
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Save Location")
            }
        }
    }
}
