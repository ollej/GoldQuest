package com.jxdevelopment.goldquest;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class ViewGoldQuest extends Activity {
    /** Called when the activity is first created. */
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);
        
        // Setup web view
        WebView myWebView = (WebView) findViewById(R.id.webview);
        
        // Activate JavaScript
        WebSettings webSettings = myWebView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        
        // Make sure links open inside the app.
        myWebView.setWebViewClient(new WebViewClient());
        
        // Load Gold Quest
        myWebView.loadUrl("http://gold-quest.appspot.com/mobile.html?game=goldquest");
    }
}