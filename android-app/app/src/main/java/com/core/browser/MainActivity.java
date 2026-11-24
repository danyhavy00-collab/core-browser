package com.core.browser;

import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
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
import android.webkit.WebResourceResponse;
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

import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

import javax.crypto.Cipher;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.PBEKeySpec;
import javax.crypto.spec.SecretKeySpec;

public class MainActivity extends AppCompatActivity {
    private WebView webView;
    private EditText urlBar;
    private LinearLayout topBar;
    private SecretKeySpec vaultKey = null;
    private SharedPreferences prefs;
    private int blockedCount = 0;

    private static final Set<String> TRACKERS = new HashSet<>(Arrays.asList(
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "msclkid", "mc_eid", "ref", "ref_src"
    ));

    private static final Set<String> AD_DOMAINS = new HashSet<>(Arrays.asList(
        "doubleclick.net", "googlesyndication.com", "googleadservices.com",
        "google-analytics.com", "googletagmanager.com", "://google.com",
        "connect.facebook.net", "://facebook.com", "ads-twitter.com",
        "://tiktok.com", "amazon-adsystem.com", "criteo.com",
        "taboola.com", "outbrain.com", "pubmatic.com", "rubiconproject.com",
        "openx.net", "adnxs.com", "hotjar.com", "mixpanel.com", "sentry.io"
    ));

    private Map<String, String> getThemeColors() {
        String th = prefs.getString("theme", "Midnight Slate");
        Map<String, String> c = new HashMap<>();
        if ("Emerald Matrix".equals(th)) {
            c.put("bg", "#0a110d"); c.put("bar", "#111c16"); c.put("border", "#1d3528");
            c.put("text", "#ecfdf5"); c.put("muted", "#7ea38e"); c.put("accent", "#10b981"); c.put("input", "#080e0b");
        } else if ("Crimson Obsidian".equals(th)) {
            c.put("bg", "#130b0e"); c.put("bar", "#1d1216"); c.put("border", "#361d26");
            c.put("text", "#fff1f2"); c.put("muted", "#a3828e"); c.put("accent", "#f43f5e"); c.put("input", "#0e080a");
        } else if ("Arctic Light".equals(th)) {
            c.put("bg", "#f1f5f9"); c.put("bar", "#ffffff"); c.put("border", "#cbd5e1");
            c.put("text", "#0f172a"); c.put("muted", "#64748b"); c.put("accent", "#2563eb"); c.put("input", "#f8fafc");
        } else {
            c.put("bg", "#0f1217"); c.put("bar", "#171c24"); c.put("border", "#252c38");
            c.put("text", "#f1f5f9"); c.put("muted", "#8b949e"); c.put("accent", "#3b82f6"); c.put("input", "#0c0f14");
        }
        return c;
    }

    private String getSearchBase() {
        String eng = prefs.getString("engine", "Chromium");
        if ("Brave".equals(eng)) return "https://brave.com";
        if ("Edge".equals(eng) || "Bing".equals(eng) || "Internet Explorer".equals(eng)) return "https://bing.com";
        if ("DuckDuckGo".equals(eng)) return "https://duckduckgo.com";
        return "https://google.com";
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("core_prefs", MODE_PRIVATE);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.parseColor("#0f1217"));

        topBar = new LinearLayout(this);
        topBar.setOrientation(LinearLayout.HORIZONTAL);
        topBar.setBackgroundColor(Color.parseColor("#171c24"));
        topBar.setPadding(12, 12, 12, 12);
        topBar.setGravity(Gravity.CENTER_VERTICAL);

        Button homeBtn = makeBtn("⌂");
        homeBtn.setOnClickListener(v -> loadCoreHome());

        Button deskBtn = makeBtn("OS");
        deskBtn.setOnClickListener(v -> loadCoreDesktop());

        urlBar = new EditText(this);
        urlBar.setHint("Search or enter URL");
        urlBar.setHintTextColor(Color.parseColor("#6e7681"));
        urlBar.setTextColor(Color.parseColor("#f1f5f9"));
        urlBar.setTextSize(13f);
        urlBar.setSingleLine(true);
        urlBar.setImeOptions(EditorInfo.IME_ACTION_GO);
        urlBar.setPadding(24, 14, 24, 14);
        GradientDrawable pill = new GradientDrawable();
        pill.setColor(Color.parseColor("#0c0f14"));
        pill.setCornerRadius(34f);
        pill.setStroke(2, Color.parseColor("#252c38"));
        urlBar.setBackground(pill);
        urlBar.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_GO || (event != null && event.getKeyCode() == KeyEvent.KEYCODE_ENTER)) {
                navigateInput(urlBar.getText().toString().trim());
                return true;
            }
            return false;
        });

        Button setBtn = makeBtn("⚙");
        setBtn.setOnClickListener(v -> loadCoreSettings());

        Button vaultBtn = makeBtn("🔒");
        vaultBtn.setOnClickListener(v -> openVaultDialog());

        topBar.addView(homeBtn);
        topBar.addView(deskBtn);
        LinearLayout.LayoutParams urlParams = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f);
        urlParams.setMargins(8, 0, 8, 0);
        topBar.addView(urlBar, urlParams);
        topBar.addView(setBtn);
        topBar.addView(vaultBtn);

        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#0f1217"));
        WebSettings ws = webView.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setDatabaseEnabled(true);
        ws.setMediaPlaybackRequiresUserGesture(false);
        ws.setCacheMode(WebSettings.LOAD_DEFAULT);

        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                if (prefs.getBoolean("blocker", true) && request != null && request.getUrl() != null) {
                    String host = request.getUrl().getHost();
                    if (host != null) {
                        String low = host.toLowerCase();
                        for (String ad : AD_DOMAINS) {
                            if (low.equals(ad) || low.endsWith("." + ad)) {
                                blockedCount++;
                                return new WebResourceResponse("text/plain", "utf-8", new ByteArrayInputStream(new byte[0]));
                            }
                        }
                    }
                }
                return super.shouldInterceptRequest(view, request);
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String u = request.getUrl().toString();
                if (u.equals("core://home")) { loadCoreHome(); return true; }
                if (u.equals("core://desktop")) { loadCoreDesktop(); return true; }
                if (u.equals("core://settings")) { loadCoreSettings(); return true; }
                if (u.startsWith("core-engine:")) {
                    try {
                        String eng = URLDecoder.decode(u.substring("core-engine:".length()), "UTF-8");
                        prefs.edit().putString("engine", eng).apply();
                    } catch (Exception ignored) {}
                    loadCoreHome();
                    return true;
                }
                if (u.startsWith("core-save:")) {
                    try {
                        String raw = URLDecoder.decode(u.substring("core-save:".length()), "UTF-8");
                        JSONObject obj = new JSONObject(raw);
                        prefs.edit()
                            .putString("theme", obj.optString("theme", "Midnight Slate"))
                            .putString("engine", obj.optString("engine", "Chromium"))
                            .putBoolean("blocker", obj.optBoolean("blocker", true))
                            .apply();
                        applyNativeTheme();
                    } catch (Exception ignored) {}
                    loadCoreHome();
                    return true;
                }
                if (u.startsWith("core-ext:")) {
                    try {
                        String ext = URLDecoder.decode(u.substring("core-ext:".length()), "UTF-8");
                        startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(ext)));
                    } catch (Exception ignored) {}
                    return true;
                }
                return false;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                if (url != null && !url.startsWith("about:") && !url.startsWith("data:")) {
                    urlBar.setText(url);
                }
            }
        });

        root.addView(topBar);
        root.addView(webView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        setContentView(root);
        applyNativeTheme();
        loadCoreHome();
    }

    private void applyNativeTheme() {
        Map<String, String> c = getThemeColors();
        topBar.setBackgroundColor(Color.parseColor(c.get("bar")));
        urlBar.setTextColor(Color.parseColor(c.get("text")));
        GradientDrawable pill = new GradientDrawable();
        pill.setColor(Color.parseColor(c.get("input")));
        pill.setCornerRadius(34f);
        pill.setStroke(2, Color.parseColor(c.get("border")));
        urlBar.setBackground(pill);
    }

    private Button makeBtn(String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setTextColor(Color.parseColor("#f1f5f9"));
        b.setTextSize(13f);
        b.setBackgroundColor(Color.TRANSPARENT);
        b.setPadding(14, 6, 14, 6);
        b.setMinimumWidth(0);
        b.setMinWidth(0);
        return b;
    }

    private void loadCoreHome() {
        Map<String, String> c = getThemeColors();
        String eng = prefs.getString("engine", "Chromium");
        String[] engines = {"Chromium", "Chrome", "Brave", "Firefox", "Edge", "Bing", "Opera", "DuckDuckGo", "Internet Explorer"};
        StringBuilder pills = new StringBuilder();
        for (String e : engines) {
            String act = e.equals(eng) ? "active" : "";
            pills.append("<a class='pill ").append(act).append("' href='core-engine:").append(e).append("'>").append(e).append("</a>");
        }
        String html = "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><style>" +
            "*{box-sizing:border-box}body{background:" + c.get("bg") + ";color:" + c.get("text") + ";font-family:sans-serif;margin:0;padding:24px 16px;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:86vh}" +
            ".logo{font-size:38px;font-weight:800;letter-spacing:8px;margin-bottom:14px}" +
            ".pills{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-bottom:16px}" +
            ".pill{text-decoration:none;font-size:11px;font-weight:600;padding:5px 11px;border-radius:14px;background:" + c.get("bar") + ";color:" + c.get("muted") + ";border:1px solid " + c.get("border") + "}" +
            ".pill.active{background:" + c.get("accent") + ";color:#fff;border-color:" + c.get("accent") + "}" +
            ".sbar{display:flex;width:100%;max-width:520px;background:" + c.get("bar") + ";border:1px solid " + c.get("border") + ";border-radius:24px;padding:4px 8px 4px 16px}" +
            "input{flex:1;background:transparent;border:none;color:" + c.get("text") + ";font-size:15px;padding:10px 6px;outline:none}" +
            "button{background:" + c.get("accent") + ";color:#fff;border:none;border-radius:18px;padding:8px 18px;font-weight:600}" +
            ".links{margin-top:18px;display:flex;gap:10px;flex-wrap:wrap;justify-content:center}" +
            ".links a{color:" + c.get("muted") + ";text-decoration:none;font-size:12px;padding:7px 14px;background:" + c.get("bar") + ";border:1px solid " + c.get("border") + ";border-radius:16px}" +
            ".card{margin-top:20px;width:100%;max-width:520px;background:" + c.get("bar") + ";border:1px solid " + c.get("border") + ";border-radius:14px;padding:14px 16px;display:flex;justify-content:space-between;align-items:center}" +
            "</style></head><body><div class='logo'>CORE</div><div class='pills'>" + pills + "</div>" +
            "<form class='sbar' onsubmit='go(event)'><input id='q' placeholder='Search with " + eng + " or enter URL'><button type='submit'>Go</button></form>" +
            "<div class='links'><a href='core://desktop'>CORE Desktop</a><a href='core://settings'>Settings</a><a href='https://wikipedia.org'>Wikipedia</a><a href='https://github.com'>GitHub</a></div>" +
            "<div class='card'><div><div style='font-size:10px;color:" + c.get("muted") + ";font-weight:700'>CORE SHIELD</div><div style='font-size:20px;font-weight:700'>" + blockedCount + " Blocked</div></div>" +
            "<div style='text-align:right'><div style='font-size:10px;color:" + c.get("muted") + ";font-weight:700'>SESSION</div><div style='font-size:13px;font-weight:600;color:" + c.get("accent") + "'>Ephemeral + AES-256</div></div></div>" +
            "<script>const BASE='" + getSearchBase() + "';function go(e){e.preventDefault();const v=document.getElementById('q').value.trim();if(!v)return;location.href=(v.includes('.')&&!v.includes(' '))?(v.startsWith('http')?v:'https://'+v):BASE+encodeURIComponent(v);}</script></body></html>";
        urlBar.setText("core://home");
        webView.loadDataWithBaseURL("https://core.local", html, "text/html", "utf-8", null);
    }

    private void loadCoreDesktop() {
        Map<String, String> c = getThemeColors();
        String html = "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><style>" +
            "*{box-sizing:border-box}body{margin:0;background:" + c.get("bg") + ";color:" + c.get("text") + ";font-family:sans-serif;height:90vh;display:flex;flex-direction:column}" +
            ".desk{flex:1;padding:18px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px;align-content:start}" +
            ".app{background:" + c.get("bar") + ";border:1px solid " + c.get("border") + ";border-radius:14px;padding:16px 8px;text-align:center;font-size:12px;font-weight:600}" +
            ".modal{position:fixed;inset:12px;background:" + c.get("bar") + ";border:1px solid " + c.get("border") + ";border-radius:14px;display:none;flex-direction:column;overflow:hidden;z-index:99}" +
            ".mbar{height:40px;background:" + c.get("bg") + ";border-bottom:1px solid " + c.get("border") + ";display:flex;align-items:center;justify-content:space-between;padding:0 14px;font-size:13px;font-weight:700}" +
            ".mbody{flex:1;padding:14px;overflow:auto}" +
            ".scard{background:" + c.get("bg") + ";border:1px solid " + c.get("border") + ";border-radius:10px;padding:12px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;gap:8px}" +
            ".btn{background:" + c.get("accent") + ";color:#fff;border:none;border-radius:14px;padding:6px 14px;font-size:11px;font-weight:700}" +
            ".tbar{height:44px;background:" + c.get("bar") + ";border-top:1px solid " + c.get("border") + ";display:flex;align-items:center;justify-content:space-between;padding:0 16px;font-size:12px}" +
            "</style></head><body><div class='desk'>" +
            "<div class='app' onclick='openWin(\"store\")'>App Store</div>" +
            "<div class='app' onclick='openWin(\"notes\")'>Notes</div>" +
            "<div class='app' onclick='openWin(\"term\")'>Terminal</div>" +
            "<div class='app' onclick='location.href=\"https://now.gg\"'>Roblox Cloud</div>" +
            "<div class='app' onclick='location.href=\"https://xbox.com\"'>Xbox Cloud</div>" +
            "<div class='app' onclick='location.href=\"core://home\"'>Exit Desktop</div></div>" +
            "<div id='win' class='modal'><div class='mbar'><span id='wtitle'>App</span><button class='btn' onclick='closeWin()'>Close</button></div><div id='wbody' class='mbody'></div></div>" +
            "<div class='tbar'><b>CORE OS</b><span>Android Workspace</span></div>" +
            "<script>" +
            "function closeWin(){document.getElementById('win').style.display='none';}" +
            "function openWin(t){const w=document.getElementById('win'),b=document.getElementById('wbody'),ti=document.getElementById('wtitle');w.style.display='flex';" +
            "if(t==='notes'){ti.textContent='Notes';b.innerHTML='<textarea style=\"width:100%;height:100%;background:transparent;color:inherit;border:none;outline:none;font-size:14px\" placeholder=\"Type session notes...\"></textarea>';}" +
            "else if(t==='term'){ti.textContent='Terminal';b.innerHTML='<div style=\"font-family:monospace;font-size:12px\">CORE Android Shell v2.2<br>User-Space Isolated Session</div>';}" +
            "else if(t==='store'){ti.textContent='App Store';b.innerHTML='<input id=\"sq\" placeholder=\"Search millions of Android & open-source apps...\" style=\"width:100%;padding:9px 12px;border-radius:8px;border:1px solid " + c.get("border") + ";background:" + c.get("input") + ";color:" + c.get("text") + ";margin-bottom:12px\" onkeydown=\"if(event.key===\\x27Enter\\x27)searchStore(this.value)\"><div id=\"sgrid\">Loading live catalog...</div>';searchStore('game');}}" +
            "async function searchStore(q){const g=document.getElementById('sgrid');g.textContent='Searching live repositories...';" +
            "try{const r=await fetch('https://github.com(q+' android apk')+'&sort=stars&per_page=12');" +
            "const d=await r.json();g.innerHTML=(d.items||[]).map(it=>'<div class=\"scard\"><div><div style=\"font-weight:700;font-size:13px\">'+it.name+'</div><div style=\"font-size:11px;color:" + c.get("muted") + "\">'+(it.description||'Open-source Android release').slice(0,80)+'</div></div><button class=\"btn\" onclick=\"location.href=\\x27'+it.html_url+'/releases\\x27\">Get</button></div>').join('')||'No results.';}" +
            "catch(e){g.textContent='Offline or rate limited.';}}" +
            "</script></body></html>";
        urlBar.setText("core://desktop");
        webView.loadDataWithBaseURL("https://core.local", html, "text/html", "utf-8", null);
    }

    private void loadCoreSettings() {
        Map<String, String> c = getThemeColors();
        String curTh = prefs.getString("theme", "Midnight Slate");
        String curEn = prefs.getString("engine", "Chromium");
        boolean blk = prefs.getBoolean("blocker", true);
        String[] themes = {"Midnight Slate", "Emerald Matrix", "Crimson Obsidian", "Arctic Light"};
        String[] engines = {"Chromium", "Chrome", "Brave", "Firefox", "Edge", "Bing", "Opera", "DuckDuckGo", "Internet Explorer"};
        StringBuilder thOpts = new StringBuilder();
        for (String t : themes) thOpts.append("<option ").append(t.equals(curTh) ? "selected" : "").append(">").append(t).append("</option>");
        StringBuilder enOpts = new StringBuilder();
        for (String e : engines) enOpts.append("<option ").append(e.equals(curEn) ? "selected" : "").append(">").append(e).append("</option>");

        String html = "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><style>" +
            "body{background:" + c.get("bg") + ";color:" + c.get("text") + ";font-family:sans-serif;padding:20px;margin:0}" +
            ".card{background:" + c.get("bar") + ";border:1px solid " + c.get("border") + ";border-radius:12px;padding:16px;margin-bottom:14px}" +
            "select{width:100%;padding:9px;border-radius:8px;background:" + c.get("input") + ";color:" + c.get("text") + ";border:1px solid " + c.get("border") + ";margin-top:8px}" +
            "button{width:100%;background:" + c.get("accent") + ";color:#fff;border:none;border-radius:10px;padding:12px;font-weight:700;font-size:14px}" +
            "</style></head><body><h2>CORE Settings</h2>" +
            "<div class='card'><b>Interface Theme</b><select id='th'>" + thOpts + "</select></div>" +
            "<div class='card'><b>Default Search Engine</b><select id='en'>" + enOpts + "</select></div>" +
            "<div class='card'><label><input type='checkbox' id='bk' " + (blk ? "checked" : "") + "> Enable Ad &amp; Tracker Blocker (" + blockedCount + " Blocked)</label></div>" +
            "<button onclick='save()'>Save &amp; Apply</button>" +
            "<script>function save(){const p={theme:document.getElementById('th').value,engine:document.getElementById('en').value,blocker:document.getElementById('bk').checked};location.href='core-save:'+encodeURIComponent(JSON.stringify(p));}</script></body></html>";
        urlBar.setText("core://settings");
        webView.loadDataWithBaseURL("https://core.local", html, "text/html", "utf-8", null);
    }

    private void navigateInput(String raw) {
        if (raw.isEmpty() || raw.equals("core://home")) { loadCoreHome(); return; }
        if (raw.equals("core://desktop")) { loadCoreDesktop(); return; }
        if (raw.equals("core://settings")) { loadCoreSettings(); return; }
        try {
            if (raw.contains(" ") || (!raw.contains(".") && !raw.startsWith("localhost"))) {
                webView.loadUrl(getSearchBase() + URLEncoder.encode(raw, "UTF-8"));
                return;
            }
            String full = raw.startsWith("http://") || raw.startsWith("https://") ? raw : "https://" + raw;
            Uri parsed = Uri.parse(full);
            Uri.Builder clean = parsed.buildUpon().clearQuery();
            for (String key : parsed.getQueryParameterNames()) {
                if (!TRACKERS.contains(key.toLowerCase())) {
                    for (String val : parsed.getQueryParameters(key)) clean.appendQueryParameter(key, val);
                }
            }
            webView.loadUrl(clean.build().toString());
        } catch (Exception e) {
            webView.loadUrl(raw);
        }
    }

    private void openVaultDialog() {
        EditText pwdInput = new EditText(this);
        pwdInput.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        pwdInput.setHint("Master Password");
        new AlertDialog.Builder(this)
            .setTitle("CORE Encrypted Vault")
            .setView(pwdInput)
            .setPositiveButton("Unlock", (d, w) -> {
                String pwd = pwdInput.getText().toString();
                if (!pwd.isEmpty()) showVaultEditor(pwd);
            })
            .setNegativeButton("Cancel", null)
            .show();
    }

    private void showVaultEditor(String password) {
        try {
            File saltFile = new File(getFilesDir(), "core_vault.salt");
            byte[] salt = new byte;
            if (saltFile.exists()) {
                try (FileInputStream fis = new FileInputStream(saltFile)) { fis.read(salt); }
            } else {
                new SecureRandom().nextBytes(salt);
                try (FileOutputStream fos = new FileOutputStream(saltFile)) { fos.write(salt); }
            }
            PBEKeySpec spec = new PBEKeySpec(password.toCharArray(), salt, 120000, 256);
            byte[] keyBytes = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded();
            vaultKey = new SecretKeySpec(keyBytes, "AES");

            String existing = "";
            File vaultFile = new File(getFilesDir(), "core_vault.enc");
            if (vaultFile.exists()) {
                byte[] all = new byte[(int) vaultFile.length()];
                try (FileInputStream fis = new FileInputStream(vaultFile)) { fis.read(all); }
                Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
                c.init(Cipher.DECRYPT_MODE, vaultKey, new GCMParameterSpec(128, all, 0, 12));
                existing = new String(c.doFinal(all, 12, all.length - 12), StandardCharsets.UTF_8);
            }

            ScrollView scroll = new ScrollView(this);
            EditText notes = new EditText(this);
            notes.setText(existing);
            notes.setHint("Encrypted Notes & Bookmarks...");
            notes.setMinLines(6);
            scroll.addView(notes);

            new AlertDialog.Builder(this)
                .setTitle("CORE Vault (Unlocked)")
                .setView(scroll)
                .setPositiveButton("Save & Encrypt", (d, w) -> {
                    try {
                        byte[] iv = new byte;
                        new SecureRandom().nextBytes(iv);
                        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
                        c.init(Cipher.ENCRYPT_MODE, vaultKey, new GCMParameterSpec(128, iv));
                        byte[] enc = c.doFinal(notes.getText().toString().getBytes(StandardCharsets.UTF_8));
                        try (FileOutputStream fos = new FileOutputStream(vaultFile)) {
                            fos.write(iv);
                            fos.write(enc);
                        }
                        Toast.makeText(this, "Encrypted to core_vault.enc", Toast.LENGTH_SHORT).show();
                    } catch (Exception ex) {
                        Toast.makeText(this, "Encryption failed", Toast.LENGTH_SHORT).show();
                    }
                })
                .setNegativeButton("Close", null)
                .show();
        } catch (Exception e) {
            Toast.makeText(this, "Wrong master password or corrupted vault.", Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.clearCache(true);
            webView.clearHistory();
            webView.clearFormData();
        }
        CookieManager.getInstance().removeAllCookies(null);
        super.onDestroy();
    }
}
