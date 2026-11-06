package com.librismart.app.presentation.librarian.analytics

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.dto.DashboardAnalyticsDto
import com.librismart.app.data.repository.AnalyticsRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class LibraryAnalyticsViewModel(
    private val analyticsRepository: AnalyticsRepository
) : ViewModel() {

    private val _analyticsState = MutableStateFlow<NetworkResult<DashboardAnalyticsDto>>(NetworkResult.Loading)
    val analyticsState: StateFlow<NetworkResult<DashboardAnalyticsDto>> = _analyticsState.asStateFlow()

    init {
        loadDashboardAnalytics()
    }

    fun loadDashboardAnalytics() {
        viewModelScope.launch {
            _analyticsState.value = NetworkResult.Loading
            _analyticsState.value = analyticsRepository.getDashboardAnalytics()
        }
    }
}
