package com.librismart.app.presentation.student.card

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.dto.DigitalStudentCardDto
import com.librismart.app.data.repository.StudentCardRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class DigitalIdCardViewModel(
    private val studentCardRepository: StudentCardRepository
) : ViewModel() {

    private val _cardState = MutableStateFlow<NetworkResult<DigitalStudentCardDto>>(NetworkResult.Loading)
    val cardState: StateFlow<NetworkResult<DigitalStudentCardDto>> = _cardState.asStateFlow()

    init {
        loadDigitalCard()
    }

    fun loadDigitalCard() {
        viewModelScope.launch {
            _cardState.value = NetworkResult.Loading
            _cardState.value = studentCardRepository.getMyDigitalCard()
        }
    }
}
