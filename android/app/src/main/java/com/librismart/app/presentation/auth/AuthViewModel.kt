package com.librismart.app.presentation.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.dto.StudentRegisterRequestDto
import com.librismart.app.data.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

sealed class AuthUiState {
    object Idle : AuthUiState()
    object Loading : AuthUiState()
    data class Success(val role: String, val fullName: String) : AuthUiState()
    data class Error(val message: String) : AuthUiState()
}

class AuthViewModel(
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<AuthUiState>(AuthUiState.Idle)
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    val isLoggedIn: StateFlow<Boolean> = authRepository.isLoggedInFlow
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), false)

    val userRole: StateFlow<String?> = authRepository.userRoleFlow
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)

    val fullName: StateFlow<String?> = authRepository.fullNameFlow
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)

    fun login(email: String, pass: String, expectedRole: String? = null) {
        if (email.isBlank() || pass.isBlank()) {
            _uiState.value = AuthUiState.Error("Please enter both email and password.")
            return
        }

        viewModelScope.launch {
            _uiState.value = AuthUiState.Loading
            when (val result = authRepository.login(email, pass)) {
                is NetworkResult.Success -> {
                    val userRole = result.data.role
                    if (expectedRole != null) {
                        val isLibrarian = userRole.equals("LIBRARIAN", ignoreCase = true) || userRole.equals("ADMIN", ignoreCase = true)
                        val expectedLibrarian = expectedRole.equals("LIBRARIAN", ignoreCase = true) || expectedRole.equals("ADMIN", ignoreCase = true)
                        if (isLibrarian != expectedLibrarian) {
                            authRepository.logout()
                            val actualTitle = if (isLibrarian) "Librarian" else "Student"
                            _uiState.value = AuthUiState.Error(
                                "Role mismatch: This account belongs to a $actualTitle. Please switch the role above to $actualTitle to sign in."
                            )
                            return@launch
                        }
                    }
                    _uiState.value = AuthUiState.Success(
                        role = result.data.role,
                        fullName = result.data.fullName
                    )
                }
                is NetworkResult.Error -> {
                    _uiState.value = AuthUiState.Error(result.message)
                }
                is NetworkResult.Loading -> {
                    _uiState.value = AuthUiState.Loading
                }
            }
        }
    }

    fun registerStudent(request: StudentRegisterRequestDto) {
        viewModelScope.launch {
            _uiState.value = AuthUiState.Loading
            when (val result = authRepository.registerStudent(request)) {
                is NetworkResult.Success -> {
                    _uiState.value = AuthUiState.Success(
                        role = result.data.role,
                        fullName = result.data.fullName
                    )
                }
                is NetworkResult.Error -> {
                    _uiState.value = AuthUiState.Error(result.message)
                }
                is NetworkResult.Loading -> {
                    _uiState.value = AuthUiState.Loading
                }
            }
        }
    }

    fun resetState() {
        _uiState.value = AuthUiState.Idle
    }

    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
            _uiState.value = AuthUiState.Idle
        }
    }

    fun deleteAccount(onComplete: () -> Unit) {
        viewModelScope.launch {
            _uiState.value = AuthUiState.Loading
            when (val result = authRepository.deleteAccount()) {
                is NetworkResult.Success -> {
                    _uiState.value = AuthUiState.Idle
                    onComplete()
                }
                is NetworkResult.Error -> {
                    _uiState.value = AuthUiState.Error(result.message)
                }
                is NetworkResult.Loading -> {}
            }
        }
    }
}
