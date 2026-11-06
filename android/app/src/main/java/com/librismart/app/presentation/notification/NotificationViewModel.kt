package com.librismart.app.presentation.notification

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.dto.NotificationDto
import com.librismart.app.data.repository.NotificationRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class NotificationViewModel(
    private val notificationRepository: NotificationRepository
) : ViewModel() {

    private val _notificationsState = MutableStateFlow<NetworkResult<List<NotificationDto>>>(NetworkResult.Loading)
    val notificationsState: StateFlow<NetworkResult<List<NotificationDto>>> = _notificationsState.asStateFlow()

    private val _selectedFilter = MutableStateFlow("ALL") // "ALL", "UNREAD"
    val selectedFilter: StateFlow<String> = _selectedFilter.asStateFlow()

    init {
        loadNotifications()
    }

    fun loadNotifications() {
        viewModelScope.launch {
            _notificationsState.value = NetworkResult.Loading
            _notificationsState.value = notificationRepository.getNotifications()
        }
    }

    fun setFilter(filter: String) {
        _selectedFilter.value = filter
    }

    fun markAsRead(notificationId: String) {
        viewModelScope.launch {
            notificationRepository.markAsRead(notificationId)
            // Update in-memory state smoothly
            val current = _notificationsState.value
            if (current is NetworkResult.Success) {
                val updated = current.data.map {
                    if (it.id == notificationId) it.copy(isRead = true) else it
                }
                _notificationsState.value = NetworkResult.Success(updated)
            }
        }
    }

    fun markAllAsRead() {
        viewModelScope.launch {
            notificationRepository.markAllAsRead()
            loadNotifications()
        }
    }
}
