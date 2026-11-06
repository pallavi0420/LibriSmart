package com.librismart.app.presentation.student.mybooks

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.dto.BookLoanDto
import com.librismart.app.data.remote.dto.FineRecordDto
import com.librismart.app.data.repository.LoanRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class MyBooksViewModel(
    private val loanRepository: LoanRepository
) : ViewModel() {

    private val _selectedTabIndex = MutableStateFlow(0)
    val selectedTabIndex: StateFlow<Int> = _selectedTabIndex.asStateFlow()

    private val _activeLoansState = MutableStateFlow<NetworkResult<List<BookLoanDto>>>(NetworkResult.Loading)
    val activeLoansState: StateFlow<NetworkResult<List<BookLoanDto>>> = _activeLoansState.asStateFlow()

    private val _historyState = MutableStateFlow<NetworkResult<List<BookLoanDto>>>(NetworkResult.Loading)
    val historyState: StateFlow<NetworkResult<List<BookLoanDto>>> = _historyState.asStateFlow()

    private val _finesState = MutableStateFlow<NetworkResult<List<FineRecordDto>>>(NetworkResult.Loading)
    val finesState: StateFlow<NetworkResult<List<FineRecordDto>>> = _finesState.asStateFlow()

    private val _renewalInProgressLoanId = MutableStateFlow<String?>(null)
    val renewalInProgressLoanId: StateFlow<String?> = _renewalInProgressLoanId.asStateFlow()

    init {
        refreshAll()
    }

    fun selectTab(index: Int) {
        _selectedTabIndex.value = index
        when (index) {
            0 -> loadActiveLoans()
            1 -> loadHistory()
            2 -> loadFines()
        }
    }

    fun refreshAll() {
        loadActiveLoans()
        loadHistory()
        loadFines()
    }

    fun loadActiveLoans() {
        viewModelScope.launch {
            _activeLoansState.value = NetworkResult.Loading
            _activeLoansState.value = loanRepository.getMyActiveLoans()
        }
    }

    fun loadHistory() {
        viewModelScope.launch {
            _historyState.value = NetworkResult.Loading
            _historyState.value = loanRepository.getMyHistory()
        }
    }

    fun loadFines() {
        viewModelScope.launch {
            _finesState.value = NetworkResult.Loading
            _finesState.value = loanRepository.getMyFines()
        }
    }

    fun renewLoan(loanId: String, onCompleted: (success: Boolean, message: String) -> Unit) {
        viewModelScope.launch {
            _renewalInProgressLoanId.value = loanId
            when (val res = loanRepository.renewLoan(loanId)) {
                is NetworkResult.Success -> {
                    _renewalInProgressLoanId.value = null
                    loadActiveLoans()
                    onCompleted(true, res.data.message)
                }
                is NetworkResult.Error -> {
                    _renewalInProgressLoanId.value = null
                    onCompleted(false, res.message)
                }
                is NetworkResult.Loading -> {}
            }
        }
    }
}
