package com.haven.ai

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {

    const val DEFAULT_BASE_URL = "http://100.102.81.112:8000/"

    @Volatile
    var currentBaseUrl: String = DEFAULT_BASE_URL
        private set

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .addInterceptor(loggingInterceptor)
        .build()

    @Volatile
    var api: HavenApi = createApi(DEFAULT_BASE_URL)
        private set

    private fun createApi(url: String): HavenApi {
        val formattedUrl = if (url.endsWith("/")) url else "$url/"
        return Retrofit.Builder()
            .baseUrl(formattedUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(HavenApi::class.java)
    }

    fun updateBaseUrl(newUrl: String): HavenApi {
        currentBaseUrl = if (newUrl.endsWith("/")) newUrl else "$newUrl/"
        api = createApi(currentBaseUrl)
        return api
    }
}
