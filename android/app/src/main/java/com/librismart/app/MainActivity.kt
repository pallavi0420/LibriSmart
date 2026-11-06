package com.librismart.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.librismart.app.core.datastore.UserPreferencesManager
import com.librismart.app.core.network.ApiClient
import com.librismart.app.core.theme.LibriSmartTheme
import com.librismart.app.data.repository.AnalyticsRepository
import com.librismart.app.data.repository.AuthRepository
import com.librismart.app.data.repository.BookRepository
import com.librismart.app.data.repository.LoanRepository
import com.librismart.app.data.repository.NotificationRepository
import com.librismart.app.data.repository.SeatReservationRepository
import com.librismart.app.data.repository.StudentCardRepository
import com.librismart.app.presentation.auth.AuthViewModel
import com.librismart.app.presentation.auth.LoginScreen
import com.librismart.app.presentation.auth.RegisterScreen
import com.librismart.app.presentation.librarian.analytics.LibraryAnalyticsScreen
import com.librismart.app.presentation.librarian.analytics.LibraryAnalyticsViewModel
import com.librismart.app.presentation.librarian.circulation.CirculationDeskScreen
import com.librismart.app.presentation.librarian.dashboard.LibrarianDashboardScreen
import com.librismart.app.presentation.librarian.inventory.AddEditBookScreen
import com.librismart.app.presentation.librarian.inventory.ManageBooksScreen
import com.librismart.app.presentation.navigation.Screen
import com.librismart.app.presentation.notification.NotificationCenterScreen
import com.librismart.app.presentation.notification.NotificationViewModel
import com.librismart.app.presentation.student.card.DigitalIdCardScreen
import com.librismart.app.presentation.student.card.DigitalIdCardViewModel
import com.librismart.app.presentation.student.explore.BookCatalogScreen
import com.librismart.app.presentation.student.explore.BookDetailScreen
import com.librismart.app.presentation.student.explore.BookSearchViewModel
import com.librismart.app.presentation.student.home.StudentHomeScreen
import com.librismart.app.presentation.student.mybooks.MyBooksScreen
import com.librismart.app.presentation.student.mybooks.MyBooksViewModel
import com.librismart.app.presentation.student.reserve.QrScannerScreen
import com.librismart.app.presentation.student.reserve.SeatReservationScreen
import com.librismart.app.presentation.student.reserve.SeatViewModel

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            LibriSmartTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    LibriSmartAppNavigation()
                }
            }
        }
    }
}

@Composable
fun LibriSmartAppNavigation() {
    val navController = rememberNavController()

    // Dependency injection setup (Scoped to Activity context)
    val context = androidx.compose.ui.platform.LocalContext.current
    val authViewModel = remember {
        val prefs = UserPreferencesManager(context.applicationContext)
        val api = ApiClient.getAuthApiService(context.applicationContext)
        val repo = AuthRepository(api, prefs)
        AuthViewModel(repo)
    }

    val bookRepository = remember {
        val bookApi = ApiClient.getBookApiService(context.applicationContext)
        BookRepository(bookApi)
    }

    val bookSearchViewModel = remember {
        BookSearchViewModel(bookRepository)
    }

    val loanRepository = remember {
        val loanApi = ApiClient.getLoanApiService(context.applicationContext)
        LoanRepository(loanApi)
    }

    val myBooksViewModel = remember {
        MyBooksViewModel(loanRepository)
    }

    val seatRepository = remember {
        val seatApi = ApiClient.getSeatApiService(context.applicationContext)
        SeatReservationRepository(seatApi)
    }

    val seatViewModel = remember {
        SeatViewModel(seatRepository)
    }

    val studentCardRepository = remember {
        val studentApi = ApiClient.getStudentApiService(context.applicationContext)
        StudentCardRepository(studentApi)
    }

    val digitalIdCardViewModel = remember {
        DigitalIdCardViewModel(studentCardRepository)
    }

    val notificationRepository = remember {
        val notifApi = ApiClient.getNotificationApiService(context.applicationContext)
        NotificationRepository(notifApi)
    }

    val notificationViewModel = remember {
        NotificationViewModel(notificationRepository)
    }

    val analyticsRepository = remember {
        val analyticsApi = ApiClient.getAnalyticsApiService(context.applicationContext)
        AnalyticsRepository(analyticsApi)
    }

    val libraryAnalyticsViewModel = remember {
        LibraryAnalyticsViewModel(analyticsRepository)
    }

    val isLoggedIn by authViewModel.isLoggedIn.collectAsState()
    val userRole by authViewModel.userRole.collectAsState()

    // Determine initial destination dynamically based on stored session
    val startDestination = remember(isLoggedIn, userRole) {
        if (isLoggedIn) {
            if (userRole == "LIBRARIAN" || userRole == "ADMIN") {
                Screen.LibrarianDashboard.route
            } else {
                Screen.StudentHome.route
            }
        } else {
            Screen.Login.route
        }
    }

    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        // 1. Sign In Screen
        composable(Screen.Login.route) {
            LoginScreen(
                viewModel = authViewModel,
                onLoginSuccess = { role ->
                    val destination = if (role == "LIBRARIAN" || role == "ADMIN") {
                        Screen.LibrarianDashboard.route
                    } else {
                        Screen.StudentHome.route
                    }
                    navController.navigate(destination) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                },
                onNavigateToRegister = {
                    navController.navigate(Screen.Register.route)
                }
            )
        }

        // 2. Student Self-Registration Screen
        composable(Screen.Register.route) {
            RegisterScreen(
                viewModel = authViewModel,
                onRegisterSuccess = {
                    navController.navigate(Screen.StudentHome.route) {
                        popUpTo(Screen.Register.route) { inclusive = true }
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                },
                onNavigateToLogin = {
                    navController.popBackStack()
                }
            )
        }

        // 3. Student / Member Main Dashboard
        composable(Screen.StudentHome.route) {
            StudentHomeScreen(
                viewModel = authViewModel,
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(Screen.StudentHome.route) { inclusive = true }
                    }
                },
                onNavigateToCatalog = {
                    navController.navigate(Screen.BookCatalog.route)
                },
                onNavigateToMyBooks = {
                    myBooksViewModel.refreshAll()
                    navController.navigate(Screen.MyBooks.route)
                },
                onNavigateToReserveSpace = {
                    seatViewModel.refreshAll()
                    navController.navigate(Screen.SeatReservation.route)
                },
                onNavigateToDigitalCard = {
                    digitalIdCardViewModel.loadDigitalCard()
                    navController.navigate(Screen.DigitalIdCard.route)
                },
                onNavigateToNotifications = {
                    notificationViewModel.loadNotifications()
                    navController.navigate(Screen.NotificationCenter.route)
                }
            )
        }

        // 4. Librarian / Administration Dashboard
        composable(Screen.LibrarianDashboard.route) {
            LibrarianDashboardScreen(
                viewModel = authViewModel,
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(Screen.LibrarianDashboard.route) { inclusive = true }
                    }
                },
                onNavigateToManageBooks = {
                    navController.navigate(Screen.ManageBooks.route)
                },
                onNavigateToCirculationDesk = {
                    navController.navigate(Screen.CirculationDesk.route)
                },
                onNavigateToAnalytics = {
                    libraryAnalyticsViewModel.loadDashboardAnalytics()
                    navController.navigate(Screen.LibraryAnalytics.route)
                }
            )
        }

        // 5. Book Catalogue & Academic Search (Student/Public)
        composable(Screen.BookCatalog.route) {
            BookCatalogScreen(
                viewModel = bookSearchViewModel,
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToBookDetail = { bookId ->
                    navController.navigate(Screen.BookDetail.createRoute(bookId))
                }
            )
        }

        // 6. Book Detail & Physical Barcode Breakdown
        composable(
            route = Screen.BookDetail.route,
            arguments = listOf(navArgument("bookId") { type = NavType.StringType })
        ) { backStackEntry ->
            val bookId = backStackEntry.arguments?.getString("bookId") ?: ""
            BookDetailScreen(
                bookId = bookId,
                bookRepository = bookRepository,
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }

        // 7. Librarian Inventory Management
        composable(Screen.ManageBooks.route) {
            ManageBooksScreen(
                bookRepository = bookRepository,
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToAddBook = {
                    navController.navigate(Screen.AddBook.route)
                },
                onNavigateToBookDetail = { bookId ->
                    navController.navigate(Screen.BookDetail.createRoute(bookId))
                }
            )
        }

        // 8. Librarian Add New Book Acquisition
        composable(Screen.AddBook.route) {
            AddEditBookScreen(
                bookRepository = bookRepository,
                onNavigateBack = {
                    navController.popBackStack()
                },
                onBookCreated = {
                    navController.popBackStack()
                }
            )
        }

        // 9. Student My Books, Loans, Renewals & Fines
        composable(Screen.MyBooks.route) {
            MyBooksScreen(
                viewModel = myBooksViewModel,
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }

        // 10. Librarian Circulation Desk (Issue & Return Barcode Scanner)
        composable(Screen.CirculationDesk.route) {
            CirculationDeskScreen(
                loanRepository = loanRepository,
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }

        // 11. Student Smart Study-Spot Reservation & Interactive 2D Seat Map
        composable(Screen.SeatReservation.route) {
            SeatReservationScreen(
                viewModel = seatViewModel,
                onNavigateBack = {
                    navController.popBackStack()
                },
                onScanQrClick = { resId, deskNumber ->
                    navController.navigate(Screen.QrScanner.createRoute(resId, deskNumber))
                }
            )
        }

        // 12. CameraX & QR Code Attendance Check-In Screen
        composable(
            route = Screen.QrScanner.route,
            arguments = listOf(
                navArgument("reservationId") { type = NavType.StringType },
                navArgument("deskNumber") { type = NavType.StringType }
            )
        ) { backStackEntry ->
            val reservationId = backStackEntry.arguments?.getString("reservationId") ?: ""
            val deskNumber = backStackEntry.arguments?.getString("deskNumber") ?: ""

            QrScannerScreen(
                reservationId = reservationId,
                deskNumber = deskNumber,
                onQrScanned = { qrCode ->
                    seatViewModel.checkInWithQr(reservationId, qrCode) { _, _ ->
                        navController.popBackStack()
                    }
                },
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }

        // 13. Student Digital Library Membership Card
        composable(Screen.DigitalIdCard.route) {
            DigitalIdCardScreen(
                viewModel = digitalIdCardViewModel,
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }

        // 14. Student & Academic In-App Notification Center
        composable(Screen.NotificationCenter.route) {
            NotificationCenterScreen(
                viewModel = notificationViewModel,
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }

        // 15. Librarian & Administrative Analytics Dashboard
        composable(Screen.LibraryAnalytics.route) {
            LibraryAnalyticsScreen(
                viewModel = libraryAnalyticsViewModel,
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}