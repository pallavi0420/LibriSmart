package com.librismart.app

import android.app.Application

/**
 * LibriSmart application entry point.
 * Initializes core app-wide Singletons, configuration, and logging policies.
 */
class LibriSmartApp : Application() {

    override fun onCreate() {
        super.onCreate()
        // Initialization hooks for DataStore, Room, and notification channels
    }
}