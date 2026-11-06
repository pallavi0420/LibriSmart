package com.librismart.app.presentation.student.reserve

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.dto.FloorDto
import com.librismart.app.data.remote.dto.OccupancyDto
import com.librismart.app.data.remote.dto.SeatReservationDto
import com.librismart.app.data.remote.dto.StudyAreaDto
import com.librismart.app.data.remote.dto.StudySeatDto
import com.librismart.app.data.repository.SeatReservationRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import java.util.TimeZone

class SeatViewModel(
    private val seatRepository: SeatReservationRepository
) : ViewModel() {

    private val _occupancyState = MutableStateFlow<NetworkResult<OccupancyDto>>(NetworkResult.Loading)
    val occupancyState: StateFlow<NetworkResult<OccupancyDto>> = _occupancyState.asStateFlow()

    private val _floorsState = MutableStateFlow<NetworkResult<List<FloorDto>>>(NetworkResult.Loading)
    val floorsState: StateFlow<NetworkResult<List<FloorDto>>> = _floorsState.asStateFlow()

    private val _selectedFloor = MutableStateFlow<FloorDto?>(null)
    val selectedFloor: StateFlow<FloorDto?> = _selectedFloor.asStateFlow()

    private val _selectedArea = MutableStateFlow<StudyAreaDto?>(null)
    val selectedArea: StateFlow<StudyAreaDto?> = _selectedArea.asStateFlow()

    private val _seatMapState = MutableStateFlow<NetworkResult<List<StudySeatDto>>>(NetworkResult.Loading)
    val seatMapState: StateFlow<NetworkResult<List<StudySeatDto>>> = _seatMapState.asStateFlow()

    private val _myReservationsState = MutableStateFlow<NetworkResult<List<SeatReservationDto>>>(NetworkResult.Loading)
    val myReservationsState: StateFlow<NetworkResult<List<SeatReservationDto>>> = _myReservationsState.asStateFlow()

    private val _selectedSeatForBooking = MutableStateFlow<StudySeatDto?>(null)
    val selectedSeatForBooking: StateFlow<StudySeatDto?> = _selectedSeatForBooking.asStateFlow()

    private val _bookingDurationHours = MutableStateFlow(2)
    val bookingDurationHours: StateFlow<Int> = _bookingDurationHours.asStateFlow()

    private val _isBooking = MutableStateFlow(false)
    val isBooking: StateFlow<Boolean> = _isBooking.asStateFlow()

    init {
        refreshAll()
    }

    fun refreshAll() {
        loadOccupancy()
        loadFloorsAndMap()
        loadMyReservations()
    }

    fun loadOccupancy() {
        viewModelScope.launch {
            _occupancyState.value = NetworkResult.Loading
            _occupancyState.value = seatRepository.getOccupancy()
        }
    }

    fun loadFloorsAndMap() {
        viewModelScope.launch {
            _floorsState.value = NetworkResult.Loading
            when (val res = seatRepository.getFloors()) {
                is NetworkResult.Success -> {
                    _floorsState.value = NetworkResult.Success(res.data)
                    if (res.data.isNotEmpty()) {
                        val firstFloor = res.data.first()
                        _selectedFloor.value = firstFloor
                        if (firstFloor.areas.isNotEmpty()) {
                            _selectedArea.value = firstFloor.areas.first()
                            loadSeatMap(areaId = firstFloor.areas.first().id)
                        }
                    }
                }
                is NetworkResult.Error -> {
                    _floorsState.value = NetworkResult.Error(res.message)
                }
                is NetworkResult.Loading -> {}
            }
        }
    }

    fun selectFloor(floor: FloorDto) {
        _selectedFloor.value = floor
        if (floor.areas.isNotEmpty()) {
            _selectedArea.value = floor.areas.first()
            loadSeatMap(areaId = floor.areas.first().id)
        } else {
            _selectedArea.value = null
            _seatMapState.value = NetworkResult.Success(emptyList())
        }
    }

    fun selectArea(area: StudyAreaDto) {
        _selectedArea.value = area
        loadSeatMap(areaId = area.id)
    }

    fun loadSeatMap(areaId: Int? = _selectedArea.value?.id) {
        viewModelScope.launch {
            _seatMapState.value = NetworkResult.Loading
            _seatMapState.value = seatRepository.getSeatMap(areaId = areaId)
        }
    }

    fun selectSeatForBooking(seat: StudySeatDto?) {
        _selectedSeatForBooking.value = seat
    }

    fun setBookingDurationHours(hours: Int) {
        _bookingDurationHours.value = hours.coerceIn(1, 4)
    }

    fun reserveSelectedSeat(onCompleted: (success: Boolean, message: String) -> Unit) {
        val seat = _selectedSeatForBooking.value ?: return
        viewModelScope.launch {
            _isBooking.value = true

            val sdf = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply {
                timeZone = TimeZone.getTimeZone("UTC")
            }

            val cal = Calendar.getInstance()
            val startIso = sdf.format(cal.time)
            cal.add(Calendar.HOUR_OF_DAY, _bookingDurationHours.value)
            val endIso = sdf.format(cal.time)

            when (val res = seatRepository.reserveSeat(seat.id, startIso, endIso)) {
                is NetworkResult.Success -> {
                    _isBooking.value = false
                    _selectedSeatForBooking.value = null
                    loadOccupancy()
                    loadSeatMap()
                    loadMyReservations()
                    onCompleted(true, "Desk ${seat.seatNumber} reserved successfully!")
                }
                is NetworkResult.Error -> {
                    _isBooking.value = false
                    onCompleted(false, res.message)
                }
                is NetworkResult.Loading -> {}
            }
        }
    }

    fun loadMyReservations() {
        viewModelScope.launch {
            _myReservationsState.value = NetworkResult.Loading
            _myReservationsState.value = seatRepository.getMyReservations()
        }
    }

    fun cancelReservation(reservationId: String, onCompleted: (success: Boolean, message: String) -> Unit) {
        viewModelScope.launch {
            when (val res = seatRepository.cancelReservation(reservationId)) {
                is NetworkResult.Success -> {
                    loadOccupancy()
                    loadSeatMap()
                    loadMyReservations()
                    onCompleted(true, res.data.message)
                }
                is NetworkResult.Error -> {
                    onCompleted(false, res.message)
                }
                is NetworkResult.Loading -> {}
            }
        }
    }

    fun checkInWithQr(
        reservationId: String,
        qrIdentifier: String,
        onCompleted: (success: Boolean, message: String) -> Unit
    ) {
        viewModelScope.launch {
            when (val res = seatRepository.checkIn(reservationId, qrIdentifier.trim())) {
                is NetworkResult.Success -> {
                    loadOccupancy()
                    loadSeatMap()
                    loadMyReservations()
                    onCompleted(true, "Successfully checked in to desk ${res.data.seatNumber}!")
                }
                is NetworkResult.Error -> {
                    onCompleted(false, res.message)
                }
                is NetworkResult.Loading -> {}
            }
        }
    }

    fun checkOutEarly(
        reservationId: String,
        onCompleted: (success: Boolean, message: String) -> Unit
    ) {
        viewModelScope.launch {
            when (val res = seatRepository.checkOut(reservationId)) {
                is NetworkResult.Success -> {
                    loadOccupancy()
                    loadSeatMap()
                    loadMyReservations()
                    onCompleted(true, "Checked out successfully. Desk ${res.data.seatNumber} is now released.")
                }
                is NetworkResult.Error -> {
                    onCompleted(false, res.message)
                }
                is NetworkResult.Loading -> {}
            }
        }
    }
}
