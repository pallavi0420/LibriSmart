package com.librismart.app.presentation.navigation

sealed class Screen(val route: String) {
    object Login : Screen("login")
    object Register : Screen("register")
    object StudentHome : Screen("student_home")
    object LibrarianDashboard : Screen("librarian_dashboard")
    object BookCatalog : Screen("book_catalog")
    object BookDetail : Screen("book_detail/{bookId}") {
        fun createRoute(bookId: String) = "book_detail/$bookId"
    }
    object ManageBooks : Screen("manage_books")
    object AddBook : Screen("add_book")
    object MyBooks : Screen("my_books")
    object CirculationDesk : Screen("circulation_desk")
    object SeatReservation : Screen("seat_reservation")
    object QrScanner : Screen("qr_scanner/{reservationId}/{deskNumber}") {
        fun createRoute(reservationId: String, deskNumber: String) = "qr_scanner/$reservationId/$deskNumber"
    }
    object DigitalIdCard : Screen("digital_id_card")
    object NotificationCenter : Screen("notification_center")
    object LibraryAnalytics : Screen("library_analytics")
}
