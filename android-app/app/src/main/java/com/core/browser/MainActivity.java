package com.core.browser;

import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

import javax.crypto.Cipher;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;

public class MainActivity extends AppCompatActivity {
    private WebView webView;
    private EditText urlBar;
    private SecretKeySpec vaultKey = null;

    private static final Set<String> TRACKERS = new HashSet<>(Arrays.asList(
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "msclkid", "mc_eid", "ref", "ref_src"
    ));

    private static final String CORE_HOME_HTML = "<!DOCTYPE html><html><head><meta charset='utf-8'>" +
        "<meta name='viewport' content='width=device-width,initial-scale=1'>" +
        "<style>*{box-sizing:border-box}body{background:#14171c;color:#f0f6fc;font-family:sans-serif;" +
        "margin:0;display:flex;flex-direction:column;align-items:center;justify-content:center;height:85vh;padding:20px}" +
        ".logo{font-size:38px;font-weight:800;letter-spacing:7px;margin-bottom:8px}" +
        ".sub{font-size:11px;color:#38bdf8;letter-spacing:2px;margin-bottom:26px}" +
        "form{display:flex;width:100%;max-width:480px;background:#1c2026;border:1px solid #2d333b;border-radius:24px;padding:4px 8px 4px 16px}" +
        "input{flex:1;background:transparent;border:none;color:#fff;font-size:15px;padding:10px 6px;outline:none}" +
        "button{background:#2d333b;color:#fff;border:none;border-radius:18px;padding:8px 16px;font-weight:600}" +
        "</style></head><body><div class='logo'>CORE</div><div class='sub'>RAM-ONLY &bull; AES-256</div>" +
        "<form action='https://duckduckgo.com' method='get'>" +
        "<input type='hidden' name='kae' value='d'><input type='hidden' name='k1' value='-1'>" +
        "<input type='text' name='q' placeholder='Search privately or enter URL'>" +
        "<button type='submit'>Go</button></form></body></html>";

    private static final String CORE_SKIN_JS =
        "(function(){if(!location.href.includes('duckduckgo.com'))return;" +
        "var s=document.getElementById('core-css')||document.createElement('style');s.id='core-css';" +
        "s.textContent='html,body,.site-wrapper,.header-wrap{background:#14171c!important}" +
        "a[href*=\"duck.ai\"],[data-testid=\"duckai-button\"],.js-badge-link,.badge-link,.footer{display:none!important}';" +
        "if(!s.parentNode&&document.head)document.head.appendChild(s);" +
        "document.querySelectorAll('header a[href=\"/\"],header a[href^=\"/?\"],[data-testid=\"header-logo\"]').forEach(function(l){" +
        "if(!l.dataset.c){l.dataset.c='1';l.innerHTML='<span style=\"color:#f0f6fc;font-weight:800;font-size:17px;letter-spacing:4px;padding:0 6px\">CORE</span>';}});" +
        "document.querySelectorAll('a,button,span').forEach(function(e){if(e.children.length===0&&" +
        "(e.textContent.trim()==='Ask Duck.ai'||e.textContent.trim()==='Share Feedback')){" +
        "var p=e.closest('li,button,a')||e;p.style.display='none';}});})();";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#14171c"));

        LinearLayout topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setBackgroundColor(Color.parseColor("#1c2026"));
        topBar.setPadding(14, 14, 14, 14);
        topBar.setGravity(Gravity.CENTER_VERTICAL);

        Button homeBtn = makeBtn("⌂");
        homeBtn.setOnClickListener(v -> loadCoreHome());

        Button backBtn = makeBtn("←");
        backBtn.setOnClickListener(v -> { if (webView.canGoBack()) webView.goBack(); });

        urlBar = new EditText(this);
        urlBar.setHint("Search or URL");
        urlBar.setHintTextColor(Color.parseColor("#6e7681"));
        urlBar.setTextColor(Color.parseColor("#e6edf3"));
        urlBar.setTextSize(13f);
        urlBar.setSingleLine(true);
        urlBar.setImeOptions(EditorInfo.IME_ACTION_GO);
        urlBar.setPadding(28, 16, 28, 16);
        GradientDrawable pill = new GradientDrawable();
        pill.setColor(Color.parseColor("#111317"));
        pill.setCornerRadius(36f);
        pill.setStroke(2, Color.parseColor("#2b313a"));
        urlBar.setBackground(pill);
        urlBar.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO || (event != null && event.getKeyCode() == KeyEvent.KEYCODE_ENTER)) {
                navigateInput(urlBar.getText().toString().trim());
                return true;
            }
            return false;
        });

        LinearLayout.LayoutParams urlParams = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        urlParams.setMargins(10, 0, 10, 0);

        Button vaultBtn = makeBtn("Vault");
        vaultBtn.setOnClickListener(v -> openVaultDialog());

        Button srcBtn = makeBtn("</>");
        srcBtn.setOnClickListener(v -> inspectHtml());

        topBar.addView(homeBtn);
        topBar.addView(backBtn);
        topBar.addView(urlBar, urlParams);
        topBar.addView(vaultBtn);
        topBar.addView(srcBtn);

        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#14171c"));
        WebSettings ws = webView.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(false);
        ws.setSaveFormData(false);
        ws.setCacheMode(WebSettings.LOAD_NO_CACHE);
        CookieManager.getInstance().setAcceptCookie(false);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                String cleaned = cleanUrl(req.getUrl().toString());
                if (!cleaned.equals(req.getUrl().toString())) {
                    view.loadUrl(cleaned);
                    return true;
                }
                return false;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                view.evaluateJavascript(CORE_SKIN_JS, null);
                updateDisplayUrl(url);
            }
        });
        webView.setWebChromeClient(new WebChromeClient());

        root.addView(topBar);
        root.addView(webView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        setContentView(root);
        loadCoreHome();
    }

    private Button makeBtn(String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setTextColor(Color.parseColor("#e6edf3"));
        b.setBackgroundColor(Color.TRANSPARENT);
        b.setTextSize(13f);
        b.setPadding(16, 8, 16, 8);
        b.setMinWidth(0);
        b.setMinimumWidth(0);
        return b;
    }

    private void loadCoreHome() {
        webView.loadDataWithBaseURL("about:blank", CORE_HOME_HTML, "text/html", "UTF-8", null);
        urlBar.setText("core://home");
    }

    private void updateDisplayUrl(String url) {
        if (url == null || url.equals("about:blank") || url.startsWith("data:")) {
            urlBar.setText("core://home");
        } else if (url.contains("duckduckgo.com") && url.contains("q=")) {
            String q = Uri.parse(url).getQueryParameter("q");
            urlBar.setText("core://search?q=" + (q != null ? q : ""));
        } else {
            urlBar.setText(url);
        }
    }

    private void navigateInput(String input) {
        if (input.isEmpty() || input.equals("core://home")) {
            loadCoreHome();
            return;
        }
        try {
            if (input.startsWith("core://search?q=")) {
                String q = input.substring("core://search?q=".length());
                webView.loadUrl("https://duckduckgo.com" + URLEncoder.encode(q, "UTF-8") + "&kae=d&k1=-1");
                return;
            }
            if (input.contains(" ") || !input.contains(".")) {
                webView.loadUrl("https://duckduckgo.com" + URLEncoder.encode(input, "UTF-8") + "&kae=d&k1=-1");
                return;
            }
            webView.loadUrl(cleanUrl(input));
        } catch (Exception e) {
            Toast.makeText(this, "Invalid input", Toast.LENGTH_SHORT).show();
        }
    }

    private String cleanUrl(String raw) {
        if (!raw.startsWith("http://") && !raw.startsWith("https://")) raw = "https://" + raw;
        Uri uri = Uri.parse(raw);
        Uri.Builder b = uri.buildUpon().clearQuery();
        for (String key : uri.getQueryParameterNames()) {
            if (!TRACKERS.contains(key.toLowerCase())) {
                for (String val : uri.getQueryParameters(key)) b.appendQueryParameter(key, val);
            }
        }
        return b.build().toString();
    }

    private void inspectHtml() {
        webView.evaluateJavascript("document.documentElement.outerHTML", html -> {
            ScrollView sv = new ScrollView(this);
            TextView tv = new TextView(this);
            tv.setText(html);
            tv.setTextColor(Color.parseColor("#e6edf3"));
            tv.setPadding(24, 24, 24, 24);
            tv.setTextIsSelectable(true);
            sv.addView(tv);
            new AlertDialog.Builder(this).setTitle("Page HTML").setView(sv).setPositiveButton("Close", null).show();
        });
    }

    private void openVaultDialog() {
        if (vaultKey == null) {
            EditText pwdInput = new EditText(this);
            pwdInput.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
            pwdInput.setHint("Master Password");
            new AlertDialog.Builder(this)
                .setTitle("CORE AES-256 Vault")
                .setView(pwdInput)
                .setPositiveButton("Unlock / Create", (d, w) -> {
                    if (unlockVault(pwdInput.getText().toString())) openVaultEditor();
                    else Toast.makeText(this, "Wrong password", Toast.LENGTH_SHORT).show();
                })
                .setNegativeButton("Cancel", null)
                .show();
        } else {
            openVaultEditor();
        }
    }

    private void openVaultEditor() {
        EditText notesBox = new EditText(this);
        notesBox.setMinLines(6);
        notesBox.setGravity(Gravity.TOP);
        notesBox.setText(readVaultText());
        new AlertDialog.Builder(this)
            .setTitle("Encrypted Notes & Links")
            .setView(notesBox)
            .setPositiveButton("Encrypt & Save", (d, w) -> saveVaultText(notesBox.getText().toString()))
            .setNeutralButton("+ Current URL", (d, w) -> {
                String updated = notesBox.getText().toString() + "\n" + webView.getUrl();
                saveVaultText(updated.trim());
            })
            .setNegativeButton("Close", null)
            .show();
    }

    private boolean unlockVault(String password) {
        try {
            File saltFile = new File(getFilesDir(), "core.salt");
            byte[] salt = java.nio.ByteBuffer.allocate(16).array();
            if (saltFile.exists()) {
                try (FileInputStream fis = new FileInputStream(saltFile)) { fis.read(salt); }
            } else {
                new SecureRandom().nextBytes(salt);
                try (FileOutputStream fos = new FileOutputStream(saltFile)) { fos.write(salt); }
            }
            PBEKeySpec spec = new PBEKeySpec(password.toCharArray(), salt, 120000, 256);
            byte[] keyBytes = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded();
            vaultKey = new SecretKeySpec(keyBytes, "AES");
            readVaultText();
            return true;
        } catch (Exception e) {
            vaultKey = null;
            return false;
        }
    }

    private String readVaultText() {
        try {
            File encFile = new File(getFilesDir(), "core.vault");
            if (!encFile.exists()) return "";
            byte[] all = new byte[(int) encFile.length()];
            try (FileInputStream fis = new FileInputStream(encFile)) { fis.read(all); }
            byte[] iv = Arrays.copyOfRange(all, 0, 12);
            byte[] cipherText = Arrays.copyOfRange(all, 12, all.length);
            Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
            c.init(Cipher.DECRYPT_MODE, vaultKey, new GCMParameterSpec(128, iv));
            return new String(c.doFinal(cipherText), StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private void saveVaultText(String plain) {
        try {
            byte[] iv = java.nio.ByteBuffer.allocate(12).array();
            new SecureRandom().nextBytes(iv);
            Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
            c.init(Cipher.ENCRYPT_MODE, vaultKey, new GCMParameterSpec(128, iv));
            byte[] enc = c.doFinal(plain.getBytes(StandardCharsets.UTF_8));
            File encFile = new File(getFilesDir(), "core.vault");
            try (FileOutputStream fos = new FileOutputStream(encFile)) {
                fos.write(iv);
                fos.write(enc);
            }
            Toast.makeText(this, "Encrypted with AES-256", Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(this, "Save failed", Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onDestroy() {
        webView.clearCache(true);
        webView.clearHistory();
        CookieManager.getInstance().removeAllCookies(null);
        super.onDestroy();
    }
}
