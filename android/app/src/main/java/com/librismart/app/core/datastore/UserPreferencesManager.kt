package com.librismart.app.core.datastore

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "librismart_user_prefs")

class UserPreferencesManager(private val context: Context) {

    companion object {
        val KEY_ACCESS_TOKEN = stringPreferencesKey("access_token")
        val KEY_REFRESH_TOKEN = stringPreferencesKey("refresh_token")
        val KEY_USER_ROLE = stringPreferencesKey("user_role")
        val KEY_USER_ID = stringPreferencesKey("user_id")
        val KEY_USER_EMAIL = stringPreferencesKey("user_email")
        val KEY_FULL_NAME = stringPreferencesKey("full_name")
    }

    val accessTokenFlow: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[KEY_ACCESS_TOKEN]
    }

    val userRoleFlow: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[KEY_USER_ROLE]
    }

    val fullNameFlow: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[KEY_FULL_NAME]
    }

    val isLoggedInFlow: Flow<Boolean> = context.dataStore.data.map { prefs ->
        !prefs[KEY_ACCESS_TOKEN].isNullOrBlank()
    }

    suspend fun saveAuthSession(
        accessToken: String,
        refreshToken: String,
        role: String,
        userId: String,
        email: String,
        fullName: String
    ) {
        context.dataStore.edit { prefs ->
            prefs[KEY_ACCESS_TOKEN] = accessToken
            prefs[KEY_REFRESH_TOKEN] = refreshToken
            prefs[KEY_USER_ROLE] = role
            prefs[KEY_USER_ID] = userId
            prefs[KEY_USER_EMAIL] = email
            prefs[KEY_FULL_NAME] = fullName
        }
    }

    suspend fun clearSession() {
        context.dataStore.edit { prefs ->
            prefs.clear()
        }
    }
}
