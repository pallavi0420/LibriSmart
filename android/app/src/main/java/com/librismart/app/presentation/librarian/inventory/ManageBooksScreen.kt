package com.librismart.app.presentation.librarian.inventory

import androidx.compose.foundation.background
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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.AddCircleOutline
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.LibraryBooks
import androidx.compose.material.icons.filled.QrCode
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.librismart.app.core.network.NetworkResult
import com.librismart.app.core.theme.AlertError
import com.librismart.app.core.theme.AlertSuccess
import com.librismart.app.core.theme.NavyPrimary
import com.librismart.app.core.theme.SageGreen
import com.librismart.app.data.remote.dto.BookCopyDto
import com.librismart.app.data.remote.dto.BookDto
import com.librismart.app.data.repository.BookRepository
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ManageBooksScreen(
    bookRepository: BookRepository,
    onNavigateBack: () -> Unit,
    onNavigateToAddBook: () -> Unit,
    onNavigateToBookDetail: (String) -> Unit
) {
    var searchQuery by remember { mutableStateOf("") }
    var booksState by remember { mutableStateOf<NetworkResult<List<BookDto>>>(NetworkResult.Loading) }
    var selectedBookForCopy by remember { mutableStateOf<BookDto?>(null) }
    var conditionNotes by remember { mutableStateOf("") }
    var isAddingCopy by remember { mutableStateOf(false) }
    var addedCopyResult by remember { mutableStateOf<BookCopyDto?>(null) }

    val scope = rememberCoroutineScope()
    val snackbarHostState = remember { SnackbarHostState() }

    fun loadBooks() {
        scope.launch {
            booksState = NetworkResult.Loading
            when (val res = bookRepository.getBooks(query = searchQuery.ifBlank { null }, size = 100)) {
                is NetworkResult.Success -> booksState = NetworkResult.Success(res.data.items)
                is NetworkResult.Error -> booksState = NetworkResult.Error(res.message)
                is NetworkResult.Loading -> {}
            }
        }
    }

    LaunchedEffect(Unit) {
        loadBooks()
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Manage Book Inventory",
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
                    IconButton(onClick = { loadBooks() }) {
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
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = onNavigateToAddBook,
                containerColor = SageGreen,
                contentColor = MaterialTheme.colorScheme.surface
            ) {
                Icon(imageVector = Icons.Default.Add, contentDescription = "Add New Book")
            }
        }
    ) { innerPadding ->
        Surface(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding),
            color = MaterialTheme.colorScheme.background
        ) {
            Column(modifier = Modifier.fillMaxSize()) {
                // Search Field
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = {
                        searchQuery = it
                        loadBooks()
                    },
                    placeholder = { Text("Filter inventory by title or ISBN...") },
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Default.Search,
                            contentDescription = "Search",
                            tint = NavyPrimary
                        )
                    },
                    trailingIcon = {
                        if (searchQuery.isNotEmpty()) {
                            IconButton(onClick = {
                                searchQuery = ""
                                loadBooks()
                            }) {
                                Icon(Icons.Default.Clear, contentDescription = "Clear")
                            }
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 10.dp),
                    shape = RoundedCornerShape(12.dp),
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = NavyPrimary
                    )
                )

                when (val state = booksState) {
                    is NetworkResult.Loading -> {
                        Box(
                            modifier = Modifier.fillMaxSize(),
                            contentAlignment = Alignment.Center
                        ) {
                            CircularProgressIndicator(color = NavyPrimary)
                        }
                    }

                    is NetworkResult.Error -> {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(24.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text(text = state.message, color = AlertError)
                                Spacer(modifier = Modifier.height(12.dp))
                                Button(onClick = { loadBooks() }) {
                                    Text("Retry")
                                }
                            }
                        }
                    }

                    is NetworkResult.Success -> {
                        val books = state.data
                        if (books.isEmpty()) {
                            Box(
                                modifier = Modifier
                                    .fillMaxSize()
                                    .padding(32.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Icon(
                                        imageVector = Icons.Default.LibraryBooks,
                                        contentDescription = null,
                                        tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f),
                                        modifier = Modifier.size(56.dp)
                                    )
                                    Spacer(modifier = Modifier.height(12.dp))
                                    Text(
                                        text = "No inventory records found",
                                        style = MaterialTheme.typography.titleMedium,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                            }
                        } else {
                            LazyColumn(
                                modifier = Modifier.fillMaxSize(),
                                contentPadding = PaddingValues(16.dp),
                                verticalArrangement = Arrangement.spacedBy(12.dp)
                            ) {
                                item {
                                    Text(
                                        text = "Total Catalogue Titles: ${books.size}",
                                        style = MaterialTheme.typography.labelMedium,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        fontWeight = FontWeight.Bold
                                    )
                                }

                                items(items = books, key = { it.id }) { book ->
                                    LibrarianBookItemCard(
                                        book = book,
                                        onViewDetails = { onNavigateToBookDetail(book.id) },
                                        onAddCopy = { selectedBookForCopy = book }
                                    )
                                }

                                item {
                                    Spacer(modifier = Modifier.height(72.dp)) // Clear FAB
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Dialog: Add Physical Barcode Copy
    selectedBookForCopy?.let { book ->
        AlertDialog(
            onDismissRequest = {
                if (!isAddingCopy) selectedBookForCopy = null
            },
            title = {
                Text(
                    text = "Add Physical Copy",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Column {
                    Text(
                        text = "Adding copy to '${book.title}'. A unique institutional barcode will be generated automatically.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    OutlinedTextField(
                        value = conditionNotes,
                        onValueChange = { conditionNotes = it },
                        label = { Text("Condition Notes (Optional)") },
                        placeholder = { Text("e.g. Brand new, Campus grant purchase") },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(10.dp)
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        isAddingCopy = true
                        scope.launch {
                            val res = bookRepository.addCopy(
                                bookId = book.id,
                                condition = conditionNotes.ifBlank { null }
                            )
                            isAddingCopy = false
                            when (res) {
                                is NetworkResult.Success -> {
                                    addedCopyResult = res.data
                                    conditionNotes = ""
                                    selectedBookForCopy = null
                                    loadBooks()
                                }
                                is NetworkResult.Error -> {
                                    snackbarHostState.showSnackbar("Error: ${res.message}")
                                }
                                is NetworkResult.Loading -> {}
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = NavyPrimary),
                    enabled = !isAddingCopy
                ) {
                    if (isAddingCopy) {
                        CircularProgressIndicator(
                            color = MaterialTheme.colorScheme.surface,
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp
                        )
                    } else {
                        Text("Generate Barcode")
                    }
                }
            },
            dismissButton = {
                TextButton(
                    onClick = { selectedBookForCopy = null },
                    enabled = !isAddingCopy
                ) {
                    Text("Cancel")
                }
            }
        )
    }

    // Success Dialog: Barcode Minted Notice
    addedCopyResult?.let { copy ->
        AlertDialog(
            onDismissRequest = { addedCopyResult = null },
            icon = {
                Icon(
                    imageVector = Icons.Default.QrCode,
                    contentDescription = null,
                    tint = AlertSuccess,
                    modifier = Modifier.size(36.dp)
                )
            },
            title = {
                Text(
                    text = "Physical Barcode Generated",
                    fontWeight = FontWeight.Bold
                )
            },
            text = {
                Column {
                    Text(
                        text = "Successfully registered Physical Copy #${copy.copyNumber} with asset barcode:",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(
                                color = MaterialTheme.colorScheme.surfaceVariant,
                                shape = RoundedCornerShape(8.dp)
                            )
                            .padding(12.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = copy.barcode,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = NavyPrimary
                        )
                    }
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = "Status: ${copy.status.uppercase()}",
                        style = MaterialTheme.typography.labelSmall,
                        color = AlertSuccess,
                        fontWeight = FontWeight.Bold
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = { addedCopyResult = null },
                    colors = ButtonDefaults.buttonColors(containerColor = NavyPrimary)
                ) {
                    Text("Done")
                }
            }
        )
    }
}

@Composable
fun LibrarianBookItemCard(
    book: BookDto,
    onViewDetails: () -> Unit,
    onAddCopy: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = book.title,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = "by ${book.author} • ISBN: ${book.isbn}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    if (!book.shelfLocation.isNullOrBlank()) {
                        Text(
                            text = "📍 ${book.shelfLocation}",
                            style = MaterialTheme.typography.labelSmall,
                            color = SageGreen,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                }

                Spacer(modifier = Modifier.width(8.dp))

                // Copies badge
                val isAvailable = book.availableCopiesCount > 0
                val badgeColor = if (isAvailable) AlertSuccess else AlertError
                Box(
                    modifier = Modifier
                        .background(
                            color = badgeColor.copy(alpha = 0.12f),
                            shape = RoundedCornerShape(6.dp)
                        )
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = "${book.availableCopiesCount}/${book.totalCopiesCount} Avail",
                        style = MaterialTheme.typography.labelSmall,
                        color = badgeColor,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Action Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End
            ) {
                OutlinedButton(
                    onClick = onViewDetails,
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("Details", style = MaterialTheme.typography.labelMedium)
                }

                Spacer(modifier = Modifier.width(8.dp))

                Button(
                    onClick = onAddCopy,
                    shape = RoundedCornerShape(8.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = NavyPrimary)
                ) {
                    Icon(
                        imageVector = Icons.Default.AddCircleOutline,
                        contentDescription = null,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text("Add Copy", style = MaterialTheme.typography.labelMedium)
                }
            }
        }
    }
}
