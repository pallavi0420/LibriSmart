package com.librismart.app.presentation.student.reserve

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Cancel
import androidx.compose.material.icons.filled.Computer
import androidx.compose.material.icons.filled.EventSeat
import androidx.compose.material.icons.filled.ExitToApp
import androidx.compose.material.icons.filled.Layers
import androidx.compose.material.icons.filled.QrCode
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.librismart.app.core.network.NetworkResult
import com.librismart.app.core.theme.AlertError
import com.librismart.app.core.theme.AlertSuccess
import com.librismart.app.core.theme.AlertWarning
import com.librismart.app.core.theme.NavyPrimary
import com.librismart.app.core.theme.SageGreen
import com.librismart.app.data.remote.dto.FloorDto
import com.librismart.app.data.remote.dto.OccupancyDto
import com.librismart.app.data.remote.dto.SeatReservationDto
import com.librismart.app.data.remote.dto.StudyAreaDto
import com.librismart.app.data.remote.dto.StudySeatDto
import com.librismart.app.presentation.components.OccupancyGaugeCard
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SeatReservationScreen(
    viewModel: SeatViewModel,
    onNavigateBack: () -> Unit,
    onScanQrClick: (reservationId: String, deskNumber: String) -> Unit = { _, _ -> }
) {
    var selectedTab by remember { mutableIntStateOf(0) }
    val occupancyState by viewModel.occupancyState.collectAsState()
    val floorsState by viewModel.floorsState.collectAsState()
    val selectedFloor by viewModel.selectedFloor.collectAsState()
    val selectedArea by viewModel.selectedArea.collectAsState()
    val seatMapState by viewModel.seatMapState.collectAsState()
    val myReservationsState by viewModel.myReservationsState.collectAsState()
    val selectedSeatForBooking by viewModel.selectedSeatForBooking.collectAsState()
    val bookingDurationHours by viewModel.bookingDurationHours.collectAsState()
    val isBooking by viewModel.isBooking.collectAsState()

    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Reserve Study Space",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.surface
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                            tint = MaterialTheme.colorScheme.surface
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.refreshAll() }) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Refresh",
                            tint = MaterialTheme.colorScheme.surface
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = NavyPrimary
                )
            )
        }
    ) { innerPadding ->
        Surface(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding),
            color = MaterialTheme.colorScheme.background
        ) {
            Column(modifier = Modifier.fillMaxSize()) {
                // Tab Selection (Interactive Seat Map vs My Reservations)
                TabRow(
                    selectedTabIndex = selectedTab,
                    containerColor = MaterialTheme.colorScheme.surface,
                    contentColor = NavyPrimary
                ) {
                    Tab(
                        selected = selectedTab == 0,
                        onClick = { selectedTab = 0 },
                        text = {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.EventSeat, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Interactive Seat Map")
                            }
                        }
                    )

                    Tab(
                        selected = selectedTab == 1,
                        onClick = {
                            selectedTab = 1
                            viewModel.loadMyReservations()
                        },
                        text = {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.Schedule, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("My Bookings")
                            }
                        }
                    )
                }

                when (selectedTab) {
                    0 -> InteractiveSeatMapTab(
                        occupancyState = occupancyState,
                        floorsState = floorsState,
                        selectedFloor = selectedFloor,
                        selectedArea = selectedArea,
                        seatMapState = seatMapState,
                        onFloorSelect = { viewModel.selectFloor(it) },
                        onAreaSelect = { viewModel.selectArea(it) },
                        onSeatClick = { seat -> viewModel.selectSeatForBooking(seat) },
                        onRetry = { viewModel.refreshAll() }
                    )

                    1 -> MyReservationsTab(
                        myReservationsState = myReservationsState,
                        onScanQrClick = onScanQrClick,
                        onCheckOutClick = { resId ->
                            viewModel.checkOutEarly(resId) { success, msg ->
                                scope.launch {
                                    snackbarHostState.showSnackbar(msg)
                                }
                            }
                        },
                        onCancelClick = { resId ->
                            viewModel.cancelReservation(resId) { success, msg ->
                                scope.launch {
                                    snackbarHostState.showSnackbar(msg)
                                }
                            }
                        },
                        onRetry = { viewModel.loadMyReservations() }
                    )
                }
            }
        }
    }

    // Booking Confirmation Dialog
    selectedSeatForBooking?.let { seat ->
        AlertDialog(
            onDismissRequest = {
                if (!isBooking) viewModel.selectSeatForBooking(null)
            },
            icon = {
                Icon(
                    imageVector = Icons.Default.EventSeat,
                    contentDescription = null,
                    tint = SageGreen,
                    modifier = Modifier.size(36.dp)
                )
            },
            title = {
                Text(
                    text = "Reserve Desk ${seat.seatNumber}",
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Column {
                    Text(
                        text = "Area: ${selectedArea?.name ?: "Campus Study Zone"}",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.SemiBold
                    )
                    Text(
                        text = "Floor: ${selectedFloor?.floorName ?: "Main Library"}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = "Noise Policy: ${selectedArea?.noisePolicy ?: "Quiet"}",
                        style = MaterialTheme.typography.bodySmall,
                        color = SageGreen,
                        fontWeight = FontWeight.Bold
                    )

                    Spacer(modifier = Modifier.height(14.dp))

                    Text(
                        text = "Select Reservation Duration:",
                        style = MaterialTheme.typography.labelMedium,
                        fontWeight = FontWeight.Bold
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    // Duration Chips (1h, 2h, 3h, 4h)
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        listOf(1, 2, 3, 4).forEach { hours ->
                            FilterChip(
                                selected = bookingDurationHours == hours,
                                onClick = { viewModel.setBookingDurationHours(hours) },
                                label = { Text("${hours}h") },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = NavyPrimary,
                                    selectedLabelColor = MaterialTheme.colorScheme.surface
                                )
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Text(
                        text = "• An authenticated check-in QR code will be generated upon confirmation.\n• You will have a 15-minute grace period to check in at the desk.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.reserveSelectedSeat { success, msg ->
                            scope.launch {
                                snackbarHostState.showSnackbar(msg)
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = NavyPrimary),
                    enabled = !isBooking
                ) {
                    if (isBooking) {
                        CircularProgressIndicator(
                            color = MaterialTheme.colorScheme.surface,
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp
                        )
                    } else {
                        Text("Confirm Space Reservation")
                    }
                }
            },
            dismissButton = {
                TextButton(
                    onClick = { viewModel.selectSeatForBooking(null) },
                    enabled = !isBooking
                ) {
                    Text("Cancel")
                }
            }
        )
    }
}

@Composable
fun InteractiveSeatMapTab(
    occupancyState: NetworkResult<OccupancyDto>,
    floorsState: NetworkResult<List<FloorDto>>,
    selectedFloor: FloorDto?,
    selectedArea: StudyAreaDto?,
    seatMapState: NetworkResult<List<StudySeatDto>>,
    onFloorSelect: (FloorDto) -> Unit,
    onAreaSelect: (StudyAreaDto) -> Unit,
    onSeatClick: (StudySeatDto) -> Unit,
    onRetry: () -> Unit
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // 1. Live Occupancy Gauge Card
        item {
            if (occupancyState is NetworkResult.Success) {
                OccupancyGaugeCard(occupancy = occupancyState.data)
            }
        }

        // 2. Floor Selector Filter Chips
        item {
            Column {
                Text(
                    text = "Select Campus Library Floor",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(modifier = Modifier.height(6.dp))

                if (floorsState is NetworkResult.Success) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        floorsState.data.forEach { floor ->
                            FilterChip(
                                selected = selectedFloor?.id == floor.id,
                                onClick = { onFloorSelect(floor) },
                                label = { Text("Floor ${floor.floorNumber}: ${floor.floorName}") },
                                leadingIcon = {
                                    Icon(
                                        imageVector = Icons.Default.Layers,
                                        contentDescription = null,
                                        modifier = Modifier.size(16.dp)
                                    )
                                },
                                colors = FilterChipDefaults.filterChipColors(
                                    selectedContainerColor = NavyPrimary,
                                    selectedLabelColor = MaterialTheme.colorScheme.surface
                                )
                            )
                        }
                    }
                }
            }
        }

        // 3. Study Area / Zone Selector Chips
        item {
            selectedFloor?.let { floor ->
                if (floor.areas.isNotEmpty()) {
                    Column {
                        Text(
                            text = "Designated Study Zone",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Spacer(modifier = Modifier.height(6.dp))

                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .horizontalScroll(rememberScrollState()),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            floor.areas.forEach { area ->
                                FilterChip(
                                    selected = selectedArea?.id == area.id,
                                    onClick = { onAreaSelect(area) },
                                    label = { Text("${area.name} (${area.availableSeatsCount}/${area.totalSeatsCount} Avail)") },
                                    colors = FilterChipDefaults.filterChipColors(
                                        selectedContainerColor = SageGreen,
                                        selectedLabelColor = MaterialTheme.colorScheme.surface
                                    )
                                )
                            }
                        }
                    }
                }
            }
        }

        // 4. Color Legend Bar
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceAround,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    LegendItem(color = AlertSuccess, label = "Available")
                    LegendItem(color = AlertError, label = "Occupied")
                    LegendItem(color = Color(0xFF1976D2), label = "Reserved")
                    LegendItem(color = Color.Gray, label = "Blocked")
                }
            }
        }

        // 5. 2D Visual Seat Layout Grid
        item {
            Column {
                Text(
                    text = "Interactive Seating Layout (Tap available desk to book)",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(modifier = Modifier.height(10.dp))

                when (seatMapState) {
                    is NetworkResult.Loading -> {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(220.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            CircularProgressIndicator(color = NavyPrimary)
                        }
                    }

                    is NetworkResult.Error -> {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(24.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text(text = seatMapState.message, color = AlertError)
                                Spacer(modifier = Modifier.height(10.dp))
                                Button(onClick = onRetry) { Text("Retry") }
                            }
                        }
                    }

                    is NetworkResult.Success -> {
                        val seats = seatMapState.data
                        if (seats.isEmpty()) {
                            Text(
                                text = "No study spots configured for this zone.",
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        } else {
                            // Render 4-column 2D visual layout
                            val rows = (seats.size + 3) / 4
                            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                                for (r in 0 until rows) {
                                    Row(
                                        modifier = Modifier.fillMaxWidth(),
                                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                                    ) {
                                        for (c in 0 until 4) {
                                            val index = r * 4 + c
                                            if (index < seats.size) {
                                                val seat = seats[index]
                                                Box(modifier = Modifier.weight(1f)) {
                                                    DeskNodeComposable(
                                                        seat = seat,
                                                        onClick = {
                                                            if (seat.currentOccupancyState == "AVAILABLE") {
                                                                onSeatClick(seat)
                                                            }
                                                        }
                                                    )
                                                }
                                            } else {
                                                Spacer(modifier = Modifier.weight(1f))
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun DeskNodeComposable(
    seat: StudySeatDto,
    onClick: () -> Unit
) {
    val state = seat.currentOccupancyState
    val isAvailable = state == "AVAILABLE"

    val statusColor = when (state) {
        "AVAILABLE" -> AlertSuccess
        "OCCUPIED" -> AlertError
        "RESERVED" -> Color(0xFF1976D2) // Blue
        else -> Color.Gray
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(
                width = if (isAvailable) 1.5.dp else 1.dp,
                color = if (isAvailable) AlertSuccess.copy(alpha = 0.6f) else MaterialTheme.colorScheme.outlineVariant,
                shape = RoundedCornerShape(12.dp)
            )
            .clickable(enabled = isAvailable, onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = statusColor.copy(alpha = 0.10f)
        )
    ) {
        Column(
            modifier = Modifier.padding(10.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = Icons.Default.EventSeat,
                contentDescription = null,
                tint = statusColor,
                modifier = Modifier.size(26.dp)
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = seat.seatNumber,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = state,
                style = MaterialTheme.typography.labelSmall,
                color = statusColor,
                fontWeight = FontWeight.SemiBold
            )
        }
    }
}

@Composable
fun LegendItem(color: Color, label: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(
            modifier = Modifier
                .size(10.dp)
                .background(color, CircleShape)
        )
        Spacer(modifier = Modifier.width(6.dp))
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

@Composable
fun MyReservationsTab(
    myReservationsState: NetworkResult<List<SeatReservationDto>>,
    onScanQrClick: (reservationId: String, deskNumber: String) -> Unit,
    onCheckOutClick: (reservationId: String) -> Unit,
    onCancelClick: (String) -> Unit,
    onRetry: () -> Unit
) {
    when (myReservationsState) {
        is NetworkResult.Loading -> {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = NavyPrimary)
            }
        }

        is NetworkResult.Error -> {
            Box(modifier = Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(text = myReservationsState.message, color = AlertError)
                    Spacer(modifier = Modifier.height(12.dp))
                    Button(onClick = onRetry) { Text("Retry") }
                }
            }
        }

        is NetworkResult.Success -> {
            val reservations = myReservationsState.data
            if (reservations.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize().padding(32.dp), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(
                            imageVector = Icons.Default.Schedule,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f),
                            modifier = Modifier.size(56.dp)
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = "No Study Space Reservations",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Switch to the Interactive Seat Map tab to choose a floor and book a desk.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            textAlign = TextAlign.Center
                        )
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    item {
                        Text(
                            text = "Your Campus Space Bookings (${reservations.size})",
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    items(items = reservations, key = { it.id }) { res ->
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.Top
                                ) {
                                    Column(modifier = Modifier.weight(1f)) {
                                        Text(
                                            text = "Study Desk ${res.seatNumber}",
                                            style = MaterialTheme.typography.titleMedium,
                                            fontWeight = FontWeight.Bold
                                        )
                                        Text(
                                            text = "${res.areaName} • ${res.floorName}",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }

                                    Box(
                                        modifier = Modifier
                                            .background(
                                                color = if (res.status == "PENDING_CHECKIN") Color(0xFF1976D2).copy(alpha = 0.12f) else AlertSuccess.copy(alpha = 0.12f),
                                                shape = RoundedCornerShape(6.dp)
                                            )
                                            .padding(horizontal = 8.dp, vertical = 4.dp)
                                    ) {
                                        Text(
                                            text = res.status,
                                            style = MaterialTheme.typography.labelSmall,
                                            color = if (res.status == "PENDING_CHECKIN") Color(0xFF1976D2) else AlertSuccess,
                                            fontWeight = FontWeight.Bold
                                        )
                                    }
                                }

                                Spacer(modifier = Modifier.height(10.dp))

                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(
                                        imageVector = Icons.Default.Schedule,
                                        contentDescription = null,
                                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                        modifier = Modifier.size(14.dp)
                                    )
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(
                                        text = "${res.startTime.take(16).replace("T", " ")} to ${res.endTime.take(16).replace("T", " ")}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }

                                Spacer(modifier = Modifier.height(8.dp))

                                // QR Token Badge
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(
                                        imageVector = Icons.Default.QrCode,
                                        contentDescription = null,
                                        tint = NavyPrimary,
                                        modifier = Modifier.size(14.dp)
                                    )
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(
                                        text = "QR Token: ${res.qrToken}",
                                        style = MaterialTheme.typography.labelSmall,
                                        fontWeight = FontWeight.Bold,
                                        color = NavyPrimary
                                    )
                                }

                                if (res.status == "PENDING_CHECKIN") {
                                    Spacer(modifier = Modifier.height(12.dp))
                                    Button(
                                        onClick = { onScanQrClick(res.id, res.seatNumber) },
                                        modifier = Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(10.dp),
                                        colors = ButtonDefaults.buttonColors(containerColor = SageGreen)
                                    ) {
                                        Icon(Icons.Default.QrCodeScanner, contentDescription = null, modifier = Modifier.size(16.dp))
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Text("Scan Desk QR to Check In")
                                    }

                                    Spacer(modifier = Modifier.height(8.dp))
                                    OutlinedButton(
                                        onClick = { onCancelClick(res.id) },
                                        modifier = Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(10.dp),
                                        colors = ButtonDefaults.outlinedButtonColors(contentColor = AlertError)
                                    ) {
                                        Icon(Icons.Default.Cancel, contentDescription = null, modifier = Modifier.size(16.dp))
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Text("Cancel Reservation")
                                    }
                                } else if (res.status == "CHECKED_IN") {
                                    Spacer(modifier = Modifier.height(12.dp))
                                    Button(
                                        onClick = { onCheckOutClick(res.id) },
                                        modifier = Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(10.dp),
                                        colors = ButtonDefaults.buttonColors(containerColor = NavyPrimary)
                                    ) {
                                        Icon(Icons.Default.ExitToApp, contentDescription = null, modifier = Modifier.size(16.dp))
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Text("Check Out Early (Release Desk)")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
