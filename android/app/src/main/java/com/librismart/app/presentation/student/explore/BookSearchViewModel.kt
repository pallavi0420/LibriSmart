package com.librismart.app.presentation.student.explore

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.librismart.app.core.network.NetworkResult
import com.librismart.app.data.remote.dto.BookDto
import com.librismart.app.data.remote.dto.CategoryDto
import com.librismart.app.data.repository.BookRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class BookSearchViewModel(
    private val bookRepository: BookRepository
) : ViewModel() {

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    private val _selectedCategoryId = MutableStateFlow<Int?>(null)
    val selectedCategoryId: StateFlow<Int?> = _selectedCategoryId.asStateFlow()

    private val _availableOnly = MutableStateFlow(false)
    val availableOnly: StateFlow<Boolean> = _availableOnly.asStateFlow()

    private val _bookListState = MutableStateFlow<NetworkResult<List<BookDto>>>(NetworkResult.Loading)
    val bookListState: StateFlow<NetworkResult<List<BookDto>>> = _bookListState.asStateFlow()

    private val _categoriesState = MutableStateFlow<NetworkResult<List<CategoryDto>>>(NetworkResult.Loading)
    val categoriesState: StateFlow<NetworkResult<List<CategoryDto>>> = _categoriesState.asStateFlow()

    private var searchJob: Job? = null

    init {
        loadCategories()
        searchBooks()
    }

    fun onSearchQueryChanged(newQuery: String) {
        _searchQuery.value = newQuery
        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            delay(350) // Debounce search keystrokes
            searchBooks()
        }
    }

    fun onCategorySelected(categoryId: Int?) {
        if (_selectedCategoryId.value == categoryId) {
            _selectedCategoryId.value = null // Toggle off
        } else {
            _selectedCategoryId.value = categoryId
        }
        searchBooks()
    }

    fun onAvailableOnlyToggled(available: Boolean) {
        _availableOnly.value = available
        searchBooks()
    }

    fun refresh() {
        loadCategories()
        searchBooks()
    }

    private fun loadCategories() {
        viewModelScope.launch {
            when (val result = bookRepository.getCategories()) {
                is NetworkResult.Success -> {
                    _categoriesState.value = NetworkResult.Success(result.data)
                }
                is NetworkResult.Error -> {
                    _categoriesState.value = NetworkResult.Error(result.message)
                }
                is NetworkResult.Loading -> {}
            }
        }
    }

    fun searchBooks() {
        viewModelScope.launch {
            _bookListState.value = NetworkResult.Loading
            when (val result = bookRepository.getBooks(
                query = _searchQuery.value,
                categoryId = _selectedCategoryId.value,
                availableOnly = _availableOnly.value,
                page = 1,
                size = 50
            )) {
                is NetworkResult.Success -> {
                    _bookListState.value = NetworkResult.Success(result.data.items)
                }
                is NetworkResult.Error -> {
                    _bookListState.value = NetworkResult.Error(result.message)
                }
                is NetworkResult.Loading -> {}
            }
        }
    }
}
