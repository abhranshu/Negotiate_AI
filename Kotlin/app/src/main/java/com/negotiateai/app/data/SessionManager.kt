package com.negotiateai.app.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.sessionDataStore by preferencesDataStore(name = "negotiate_ai_session")

class SessionManager(private val context: Context) {
    private object Keys {
        val TOKEN = stringPreferencesKey("auth_token")
        val USER_ID = stringPreferencesKey("user_id")
        val ROLE = stringPreferencesKey("user_role")
    }

    val authToken: Flow<String?> = context.sessionDataStore.data.map { it[Keys.TOKEN] }
    val userId: Flow<String?> = context.sessionDataStore.data.map { it[Keys.USER_ID] }
    val userRole: Flow<String?> = context.sessionDataStore.data.map { it[Keys.ROLE] }

    suspend fun saveAuthToken(token: String) {
        context.sessionDataStore.edit { it[Keys.TOKEN] = token }
    }

    suspend fun saveUserId(userId: String) {
        context.sessionDataStore.edit { it[Keys.USER_ID] = userId }
    }

    suspend fun saveUserRole(role: String) {
        context.sessionDataStore.edit { it[Keys.ROLE] = role }
    }

    suspend fun clearAuthToken() {
        context.sessionDataStore.edit { it.remove(Keys.TOKEN) }
    }

    suspend fun clearUserId() {
        context.sessionDataStore.edit { it.remove(Keys.USER_ID) }
    }

    suspend fun clearUserRole() {
        context.sessionDataStore.edit { it.remove(Keys.ROLE) }
    }
}