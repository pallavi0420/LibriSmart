package com.librismart.app.presentation.librarian.circulation

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.AssignmentReturned
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.LocalAtm
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.QrCode
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.librismart.app.core.network.NetworkResult
import com.librismart.app.core.theme.AlertError
import com.librismart.app.core.theme.AlertSuccess
import com.librismart.app.core.theme.AlertWarning
import com.librismart.app.core.theme.NavyPrimary
import com.librismart.app.core.theme.SageGreen
import com.librismart.app.data.remote.dto.BookLoanDto
import com.librismart.app.data.repository.LoanRepository
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CirculationDeskScreen(
    loanRepository: LoanRepository,
    onNavigateBack: () -> Unit
) {
    var selectedTab by remember { mutableIntStateOf(0) }
    val snackbarHostState = remember { SnackbarHostState() }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Circulation Desk",
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
                                Icon(Icons.Default.QrCodeScanner, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Issue Book")
                            }
                        }
                    )

                    Tab(
                        selected = selectedTab == 1,
                        onClick = { selectedTab = 1 },
                        text = {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.AssignmentReturned, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Process Return")
                            }
                        }
                    )
                }

                when (selectedTab) {
                    0 -> IssueBookTab(loanRepository, snackbarHostState)
                    1 -> ProcessReturnTab(loanRepository, snackbarHostState)
                }
            }
        }
    }
}

@Composable
fun IssueBookTab(
    loanRepository: LoanRepository,
    snackbarHostState: SnackbarHostState
) {
    var studentIdOrEmail by remember { mutableStateOf("STU-2026-001") }
    var barcode by remember { mutableStateOf("") }
    var durationDays by remember { mutableStateOf("14") }
    var isSubmitting by remember { mutableStateOf(false) }
    var issuedLoan by remember { mutableStateOf<BookLoanDto?>(null) }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    val scope = rememberCoroutineScope()
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(14.dp),
            colors = CardDefaults.cardColors(containerColor = SageGreen.copy(alpha = 0.12f))
        ) {
            Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.QrCodeScanner, contentDescription = null, tint = SageGreen)
                Spacer(modifier = Modifier.width(12.dp))
                Text(
                    text = "Scan or type student ID and physical copy barcode to execute immediate loan issue.",
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }

        if (errorMessage != null) {
            Text(text = errorMessage!!, color = AlertError, fontWeight = FontWeight.SemiBold)
        }

        OutlinedTextField(
            value = studentIdOrEmail,
            onValueChange = { studentIdOrEmail = it },
            label = { Text("Student ID Number or Email *") },
            leadingIcon = { Icon(Icons.Default.Person, contentDescription = null) },
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(10.dp)
        )

        OutlinedTextField(
            value = barcode,
            onValueChange = { barcode = it },
            label = { Text("Physical Copy Barcode *") },
            placeholder = { Text("e.g. BAR-350884-C01 or LS-...") },
            leadingIcon = { Icon(Icons.Default.QrCode, contentDescription = null) },
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(10.dp)
        )

        OutlinedTextField(
            value = durationDays,
            onValueChange = { durationDays = it },
            label = { Text("Loan Duration (Days)") },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            leadingIcon = { Icon(Icons.Default.Schedule, contentDescription = null) },
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(10.dp)
        )

        Button(
            onClick = {
                if (studentIdOrEmail.isBlank() || barcode.isBlank()) {
                    errorMessage = "Please enter student ID and copy barcode."
                    return@Button
                }
                errorMessage = null
                isSubmitting = true
                scope.launch {
                    val res = loanRepository.issueBook(
                        studentIdOrEmail = studentIdOrEmail,
                        barcode = barcode,
                        durationDays = durationDays.toIntOrNull() ?: 14
                    )
                    isSubmitting = false
                    when (res) {
                        is NetworkResult.Success -> {
                            issuedLoan = res.data
                            barcode = ""
                            snackbarHostState.showSnackbar("Book successfully issued!")
                        }
                        is NetworkResult.Error -> {
                            errorMessage = res.message
                            snackbarHostState.showSnackbar("Error: ${res.message}")
                        }
                        is NetworkResult.Loading -> {}
                    }
                }
            },
            modifier = Modifier.fillMaxWidth().height(50.dp),
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.buttonColors(containerColor = NavyPrimary),
            enabled = !isSubmitting
        ) {
            if (isSubmitting) {
                CircularProgressIndicator(color = MaterialTheme.colorScheme.surface, modifier = Modifier.size(18.dp))
            } else {
                Icon(Icons.Default.Check, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Authorize & Issue Book", fontWeight = FontWeight.Bold)
            }
        }

        // Issued Confirmation Card
        issuedLoan?.let { loan ->
            Spacer(modifier = Modifier.height(10.dp))
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = AlertSuccess.copy(alpha = 0.12f))
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.CheckCircle, contentDescription = null, tint = AlertSuccess)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Loan Authorized & Confirmed",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = AlertSuccess
                        )
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(text = "Title: ${loan.bookTitle}", fontWeight = FontWeight.Bold)
                    Text(text = "Borrower: ${loan.studentName ?: loan.studentUserId}")
                    Text(text = "Barcode: ${loan.barcode}")
                    Text(text = "Return Due Date: ${loan.dueDate.take(10)}", fontWeight = FontWeight.SemiBold, color = NavyPrimary)
                }
            }
        }
    }
}

@Composable
fun ProcessReturnTab(
    loanRepository: LoanRepository,
    snackbarHostState: SnackbarHostState
) {
    var barcode by remember { mutableStateOf("") }
    var conditionNotes by remember { mutableStateOf("") }
    var markAsDamaged by remember { mutableStateOf(false) }
    var isSubmitting by remember { mutableStateOf(false) }
    var returnedLoan by remember { mutableStateOf<BookLoanDto?>(null) }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    val scope = rememberCoroutineScope()
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(14.dp),
            colors = CardDefaults.cardColors(containerColor = NavyPrimary.copy(alpha = 0.08f))
        ) {
            Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.AssignmentReturned, contentDescription = null, tint = NavyPrimary)
                Spacer(modifier = Modifier.width(12.dp))
                Text(
                    text = "Scan returned physical barcode to close loan, restore stock, and calculate late fines.",
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }

        if (errorMessage != null) {
            Text(text = errorMessage!!, color = AlertError, fontWeight = FontWeight.SemiBold)
        }

        OutlinedTextField(
            value = barcode,
            onValueChange = { barcode = it },
            label = { Text("Scan / Enter Copy Barcode *") },
            placeholder = { Text("e.g. BAR-350884-C01") },
            leadingIcon = { Icon(Icons.Default.QrCode, contentDescription = null) },
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(10.dp)
        )

        OutlinedTextField(
            value = conditionNotes,
            onValueChange = { conditionNotes = it },
            label = { Text("Physical Condition Notes (Optional)") },
            placeholder = { Text("e.g. Good condition, pages intact") },
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(10.dp)
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(text = "Flag Copy as Damaged", style = MaterialTheme.typography.bodyMedium)
            Switch(checked = markAsDamaged, onCheckedChange = { markAsDamaged = it })
        }

        Button(
            onClick = {
                if (barcode.isBlank()) {
                    errorMessage = "Please enter barcode."
                    return@Button
                }
                errorMessage = null
                isSubmitting = true
                scope.launch {
                    val res = loanRepository.returnBook(
                        barcode = barcode,
                        conditionNotes = conditionNotes,
                        markAsDamaged = markAsDamaged
                    )
                    isSubmitting = false
                    when (res) {
                        is NetworkResult.Success -> {
                            returnedLoan = res.data
                            barcode = ""
                            conditionNotes = ""
                            markAsDamaged = false
                            snackbarHostState.showSnackbar("Return processed successfully!")
                        }
                        is NetworkResult.Error -> {
                            errorMessage = res.message
                            snackbarHostState.showSnackbar("Error: ${res.message}")
                        }
                        is NetworkResult.Loading -> {}
                    }
                }
            },
            modifier = Modifier.fillMaxWidth().height(50.dp),
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.buttonColors(containerColor = SageGreen),
            enabled = !isSubmitting
        ) {
            if (isSubmitting) {
                CircularProgressIndicator(color = MaterialTheme.colorScheme.surface, modifier = Modifier.size(18.dp))
            } else {
                Icon(Icons.Default.AssignmentReturned, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Process Return & Check Fines", fontWeight = FontWeight.Bold)
            }
        }

        // Return Result Card
        returnedLoan?.let { loan ->
            Spacer(modifier = Modifier.height(10.dp))
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.CheckCircle, contentDescription = null, tint = SageGreen)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Book Checked In Successfully",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = SageGreen
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    Text(text = "Title: ${loan.bookTitle}", fontWeight = FontWeight.Bold)
                    Text(text = "Borrower: ${loan.studentName ?: loan.studentUserId}")
                    Text(text = "Barcode: ${loan.barcode}")

                    if (loan.fineAmountCents > 0) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(containerColor = AlertError.copy(alpha = 0.12f))
                        ) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Text(
                                    text = "Late Return Fine Generated",
                                    fontWeight = FontWeight.Bold,
                                    color = AlertError
                                )
                                Text(
                                    text = "Amount: $${loan.fineAmountCents / 100.0}0 (${loan.daysOverdue} days overdue)",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = AlertError
                                )
                            }
                        }
                    } else {
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(text = "Returned on time • Zero late fine", color = AlertSuccess, fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }
}
