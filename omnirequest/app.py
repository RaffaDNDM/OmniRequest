from flask import Flask, request, render_template_string, jsonify
import json

app = Flask(__name__)


# ============================================================
# HTTP REQUEST PARSER
# ============================================================

def parse_raw_http(raw_request, base_url="http://localhost"):

    if not raw_request or not raw_request.strip():
        raise ValueError("Empty or invalid HTTP request")

    lines = raw_request.replace("\r\n", "\n").split("\n")

    request_line = lines[0].strip().split(None, 2)

    if len(request_line) < 2:
        raise ValueError("Invalid HTTP request line")

    method = request_line[0].upper()
    path = request_line[1]

    headers = {}
    body_lines = []
    is_body = False

    for line in lines[1:]:

        if not is_body and line == "":
            is_body = True
            continue

        if is_body:
            body_lines.append(line)

        elif ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

    host = next(
        (v for k, v in headers.items() if k.lower() == "host"),
        ""
    )

    if path.startswith(("http://", "https://")):
        full_url = path

    elif host:
        if host.lower().endswith(":443"):
            scheme = "https"
        else:
            scheme = "http"

        full_url = f"{scheme}://{host}{path}"

    else:
        full_url = base_url.rstrip("/") + path

    return {
        "method": method,
        "url": full_url,
        "headers": headers,
        "body": "\n".join(body_lines)
    }


# ============================================================
# HEADER FILTER
# ============================================================

def filter_headers(headers):

    ignored = {
        "host",
        "content-length",
        "connection",
        "transfer-encoding"
    }

    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in ignored
    }


# ============================================================
# JAVASCRIPT XMLHttpRequest
# ============================================================

def http_to_xhr(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"]
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    has_cookies = any(k.lower() == "cookie" for k in headers.keys())

    code = [
        "const xhr = new XMLHttpRequest();",
        "",
        f"xhr.open({json.dumps(method)}, {json.dumps(url)}, true);"
    ]

    if has_cookies:
        code.append("xhr.withCredentials = true; // Included because cookies/credentials were present")

    code.extend([
        "",
        "xhr.onreadystatechange = function () {",
        "    if (xhr.readyState === 4) {",
        "        console.log('Status:', xhr.status);",
        "        console.log('Response:', xhr.responseText);",
        "    }",
        "};",
        ""
    ])

    for key, value in headers.items():
        code.append(
            f"xhr.setRequestHeader("
            f"{json.dumps(key)}, {json.dumps(value)});"
        )

    code.append("")

    if body:
        code.append(f"xhr.send({json.dumps(body)});")
    else:
        code.append("xhr.send();")

    return "\n".join(code)


# ============================================================
# JAVASCRIPT FETCH API
# ============================================================

def http_to_fetch(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"]
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    has_cookies = any(k.lower() == "cookie" for k in headers.keys())

    code = [
        f"const url = {json.dumps(url)};",
        f"const options = {{",
        f"    method: {json.dumps(method)},",
        f"    headers: {json.dumps(headers, indent=8)}"
    ]

    if has_cookies:
        code.append("    , credentials: 'include' // Included because cookies were present")

    if body and method not in ["GET", "HEAD"]:
        code.append(f"    , body: {json.dumps(body)}")

    code.extend([
        "};",
        "",
        "fetch(url, options)",
        "    .then(response => response.text())",
        "    .then(result => console.log(result))",
        "    .catch(error => console.error('Error:', error));"
    ])

    return "\n".join(code)


# ============================================================
# JAVASCRIPT AXIOS
# ============================================================

def http_to_axios(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"]
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    has_cookies = any(k.lower() == "cookie" for k in headers.keys())

    code = [
        "const axios = require('axios');",
        "",
        f"let config = {{",
        f"  method: {json.dumps(method.lower())},",
        f"  maxBodyLength: Infinity,",
        f"  url: {json.dumps(url)},",
        f"  headers: {json.dumps(headers, indent=4)}"
    ]

    if has_cookies:
        code.append("  , withCredentials: true // Included because cookies were present")

    if body and method not in ["GET", "HEAD"]:
        code.append(f"  , data: {json.dumps(body)}")

    code.extend([
        "};",
        "",
        "axios.request(config)",
        "  .then((response) => {",
        "    console.log(JSON.stringify(response.data));",
        "  })",
        "  .catch((error) => {",
        "    console.log(error);",
        "  });"
    ])

    return "\n".join(code)


# ============================================================
# NODE.JS UNDICI
# ============================================================

def http_to_undici(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"]
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    code = [
        "const { request } = require('undici');",
        "",
        "async function run() {",
        f"  const {{ statusCode, headers, body }} = await request({json.dumps(url)}, {{",
        f"    method: {json.dumps(method)},",
        f"    headers: {json.dumps(headers, indent=4)}"
    ]

    if body and method not in ["GET", "HEAD"]:
        code.append(f"    , body: {json.dumps(body)}")

    code.extend([
        "  });",
        "",
        "  console.log('status:', statusCode);",
        "  const data = await body.text();",
        "  console.log('data:', data);",
        "}",
        "",
        "run();"
    ])

    return "\n".join(code)


# ============================================================
# PYTHON REQUESTS
# ============================================================

def http_to_requests(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"]
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    code = [
        "import requests",
        "",
        f"url = {url!r}",
        f"method = {method!r}",
        f"headers = {headers!r}",
        ""
    ]

    if body:
        code.append(f"body = {body!r}")
    else:
        code.append("body = None")

    code.extend([
        "",
        "response = requests.request(",
        "    method=method,",
        "    url=url,",
        "    headers=headers,",
        "    data=body,",
        "    timeout=30",
        ")",
        "",
        "print('Status:', response.status_code)",
        "print('Response:', response.text)"
    ])

    return "\n".join(code)


# ============================================================
# PYTHON HTTPX
# ============================================================

def http_to_httpx(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"]
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    code = [
        "import httpx",
        "",
        f"url = {url!r}",
        f"method = {method!r}",
        f"headers = {headers!r}",
        ""
    ]

    if body:
        code.append(f"body = {body!r}")
    else:
        code.append("body = None")

    code.extend([
        "",
        "with httpx.Client(timeout=30.0) as client:",
        "    response = client.request(",
        "        method=method,",
        "        url=url,",
        "        headers=headers,",
        "        content=body",
        "    )",
        "",
        "print('Status:', response.status_code)",
        "print('Response:', response.text)"
    ])

    return "\n".join(code)


# ============================================================
# PYTHON AIOHTTP
# ============================================================

def http_to_aiohttp(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"]
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    code = [
        "import asyncio",
        "import aiohttp",
        "",
        "async def main():",
        f"    url = {url!r}",
        f"    headers = {headers!r}"
    ]

    if body:
        code.append(f"    data = {body!r}")
    else:
        code.append("    data = None")

    code.extend([
        "    ",
        "    async with aiohttp.ClientSession() as session:",
        f"        async with session.request({method!r}, url, headers=headers, data=data) as response:",
        "            print('Status:', response.status)",
        "            html = await response.text()",
        "            print('Response:', html)",
        "",
        "asyncio.run(main())"
    ])

    return "\n".join(code)


# ============================================================
# PHP cURL
# ============================================================

def http_to_php_curl(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"]
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    header_list = [f"{k}: {v}" for k, v in headers.items()]

    code = [
        "<?php",
        "",
        "$curl = curl_init();",
        "",
        "curl_setopt_array($curl, [",
        f"    CURLOPT_URL => {json.dumps(url)},",
        "    CURLOPT_RETURNTRANSFER => true,",
        "    CURLOPT_ENCODING => '',",
        "    CURLOPT_MAXREDIRS => 10,",
        "    CURLOPT_TIMEOUT => 30,",
        "    CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,",
        f"    CURLOPT_CUSTOMREQUEST => {json.dumps(method)},",
    ]

    if header_list:
        code.append(f"    CURLOPT_HTTPHEADER => {json.dumps(header_list, indent=8)},")

    if body and method not in ["GET", "HEAD"]:
        code.append(f"    CURLOPT_POSTFIELDS => {json.dumps(body)},")

    code.extend([
        "]);",
        "",
        "$response = curl_exec($curl);",
        "$err = curl_error($curl);",
        "",
        "curl_close($curl);",
        "",
        "if ($err) {",
        "    echo 'cURL Error #:' . $err;",
        "} else {",
        "    echo $response;",
        "}"
    ])

    return "\n".join(code)


# ============================================================
# PHP Guzzle
# ============================================================

def http_to_php_guzzle(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"]
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    code = [
        "<?php",
        "require 'vendor/autoload.php';",
        "",
        "use GuzzleHttp\\Client;",
        "",
        "$client = new Client();",
        f"$response = $client->request({json.dumps(method)}, {json.dumps(url)}, [",
        f"    'headers' => {json.dumps(headers, indent=8)},"
    ]

    if body and method not in ["GET", "HEAD"]:
        code.append(f"    'body' => {json.dumps(body)},")

    code.extend([
        "]);",
        "",
        "echo $response->getBody();"
    ])

    return "\n".join(code)


# ============================================================
# GO net/http
# ============================================================

def http_to_go(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"]
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    code = [
        "package main",
        "",
        "import (",
        "    \"fmt\"",
        "    \"io\"",
        "    \"net/http\"",
    ]

    if body:
        code.append("    \"strings\"")

    code.extend([
        ")",
        "",
        "func main() {",
    ])

    if body and method not in ["GET", "HEAD"]:
        code.append(f"    payload := strings.NewReader({json.dumps(body)})")
        code.append(f"    req, _ := http.NewRequest({json.dumps(method)}, {json.dumps(url)}, payload)")
    else:
        code.append(f"    req, _ := http.NewRequest({json.dumps(method)}, {json.dumps(url)}, nil)")

    for k, v in headers.items():
        code.append(f"    req.Header.Add({json.dumps(k)}, {json.dumps(v)})")

    code.extend([
        "    ",
        "    res, err := http.DefaultClient.Do(req)",
        "    if err != nil {",
        "        fmt.Println(err)",
        "        return",
        "    }",
        "    defer res.Body.Close()",
        "",
        "    body, _ := io.ReadAll(res.Body)",
        "    fmt.Println(string(body))",
        "}"
    ])

    return "\n".join(code)


# ============================================================
# JAVA HTTPCLIENT
# ============================================================

def http_to_java(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"].upper()
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    code = [
        "import java.net.URI;",
        "import java.net.http.HttpClient;",
        "import java.net.http.HttpRequest;",
        "import java.net.http.HttpResponse;",
        "",
        "public class Main {",
        "    public static void main(String[] args) throws Exception {",
        "        HttpClient client = HttpClient.newHttpClient();",
        f"        HttpRequest.Builder builder = HttpRequest.newBuilder().uri(URI.create({json.dumps(url)}));"
    ]

    for key, value in headers.items():
        code.append(f"        builder.header({json.dumps(key)}, {json.dumps(value)});")

    if body and method not in ["GET", "HEAD"]:
        code.append(f"        builder.method({json.dumps(method)}, HttpRequest.BodyPublishers.ofString({json.dumps(body)}));")
    else:
        code.append(f"        builder.method({json.dumps(method)}, HttpRequest.BodyPublishers.noBody());")

    code.extend([
        "        ",
        "        HttpResponse<String> response = client.send(builder.build(), HttpResponse.BodyHandlers.ofString());",
        "        System.out.println(response.statusCode());",
        "        System.out.println(response.body());",
        "    }",
        "}"
    ])

    return "\n".join(code)


# ============================================================
# C# HTTPCLIENT
# ============================================================

def http_to_csharp(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"].upper()
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    code = [
        "using System;",
        "using System.Net.Http;",
        "using System.Threading.Tasks;",
        "",
        "class Program",
        "{",
        "    static async Task Main(string[] args)",
        "    {",
        "        var client = new HttpClient();",
        f"        var request = new HttpRequestMessage(HttpMethod.{method.capitalize()}, {json.dumps(url)});"
    ]

    for key, value in headers.items():
        if key.lower() == "content-type" and body:
            continue
        code.append(f"        request.Headers.Add({json.dumps(key)}, {json.dumps(value)});")

    if body and method not in ["GET", "HEAD"]:
        content_type = headers.get("Content-Type", "text/plain")
        code.append(f"        request.Content = new StringContent({json.dumps(body)}, System.Text.Encoding.UTF8, {json.dumps(content_type)});")

    code.extend([
        "",
        "        HttpResponseMessage response = await client.SendAsync(request);",
        "        response.EnsureSuccessStatusCode();",
        "        string responseBody = await response.Content.ReadAsStringAsync();",
        "        Console.WriteLine(responseBody);",
        "    }",
        "}"
    ])

    return "\n".join(code)


# ============================================================
# RUBY Net::HTTP
# ============================================================

def http_to_ruby(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"].capitalize()
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    code = [
        "require 'uri'",
        "require 'net/http'",
        "",
        f"uri = URI({json.dumps(url)})",
        f"http = Net::HTTP.new(uri.host, uri.port)",
        "http.use_ssl = uri.scheme == 'https'",
        "",
        f"request = Net::HTTP::{method}.new(uri)"
    ]

    for k, v in headers.items():
        code.append(f"request[{json.dumps(k)}] = {json.dumps(v)}")

    if body and method not in ["Get", "Head"]:
        code.append(f"request.body = {json.dumps(body)}")

    code.extend([
        "",
        "response = http.request(request)",
        "puts response.read_body"
    ])

    return "\n".join(code)


# ============================================================
# RUST Reqwest
# ============================================================

def http_to_rust(raw_request):

    req = parse_raw_http(raw_request)

    method = req["method"].lower()
    url = req["url"]
    headers = filter_headers(req["headers"])
    body = req["body"]

    code = [
        "use reqwest::header::HeaderMap;",
        "use std::error::Error;",
        "",
        "#[tokio::main]",
        "async fn main() -> Result<(), Box<dyn Error>> {",
        "    let client = reqwest::Client::new();",
        "    let mut headers = HeaderMap::new();"
    ]

    for k, v in headers.items():
        code.append(f"    headers.insert({json.dumps(k)}, {json.dumps(v)}.parse()?);")

    code.append(f"    let res = client.{method}({json.dumps(url)})")
    code.append("        .headers(headers)")

    if body and method not in ["get", "head"]:
        code.append(f"        .body({json.dumps(body)})")

    code.extend([
        "        .send()",
        "        .await?;",
        "",
        "    let body = res.text().await?;",
        "    println!(\"{}\", body);",
        "",
        "    Ok(())",
        "}"
    ])

    return "\n".join(code)


# ============================================================
# HTML TEMPLATE
# ============================================================

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>HTTP Request Converter</title>

<link
href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css"
rel="stylesheet">

<style>

* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, Helvetica, Arial, sans-serif;
    background-color: #121212;
    color: #e0e0e0;
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 1500px;
    margin: auto;
}

header {
    margin-bottom: 25px;
    border-bottom: 1px solid #2d2d2d;
    padding-bottom: 15px;
}

h1 {
    margin: 0;
    font-size: 25px;
    color: white;
}

header p {
    color: #888;
    font-size: 14px;
}

.grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 20px;
}

.panel {
    background: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 8px;
    padding: 15px;
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    height: 35px; /* Ensures vertical alignment matches across columns */
}

h2 {
    font-size: 16px;
    color: #007acc;
    margin: 0;
}

.language-select {
    background: #2d2d2d;
    color: #fff;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 13px;
    cursor: pointer;
}

.language-select:focus {
    outline: none;
    border-color: #007acc;
}

textarea {
    width: 100%;
    height: 450px;
    min-height: 450px;
    background: #2d2d2d;
    color: #f8f8f2;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 12px;
    font-family: Consolas, monospace;
    font-size: 13px;
    resize: none;
    overflow: auto;
    white-space: pre;
}

textarea:focus {
    outline: none;
    border-color: #007acc;
}

.output-box {
    width: 100%;
    height: 450px;
    min-height: 450px;
    background: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    overflow: auto;
}

pre {
    margin: 0 !important;
    padding: 12px !important;
    width: max-content;
    min-width: 100%;
    min-height: 100%;
    background: transparent !important;
}

code {
    font-family: Consolas, monospace !important;
    font-size: 13px !important;
    white-space: pre;
}

.actions {
    margin-top: 15px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

button {
    padding: 8px 14px;
    font-weight: bold;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
}

button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-primary {
    background: #007acc;
    color: white;
}

.btn-primary:hover {
    background: #005999;
}

.btn-success {
    background: #28a745;
    color: white;
}

.btn-success:hover {
    background: #218838;
}

.btn-tab {
    background: #333;
    color: #ccc;
    border: 1px solid #444;
}

.btn-tab:hover {
    background: #444;
}

.status {
    margin-top: 10px;
    font-size: 12px;
    color: #888;
}

@media (max-width: 900px) {
    .grid {
        grid-template-columns: 1fr;
    }
}

</style>
</head>

<body>

<div class="container">

<header>
    <h1>⚡ HTTP Request Converter</h1>
    <p>
        Convert raw HTTP requests into JS, Python, PHP, Go, C#, Java, Ruby, and Rust snippets.
    </p>
</header>

<div class="grid">

    <!-- INPUT -->

    <div class="panel">

        <div class="panel-header">
            <h2>1. Raw HTTP Request</h2>
        </div>

        <textarea
            id="httpInput"
            placeholder="Paste your raw HTTP request here..."
            spellcheck="false"
        ></textarea>

        <div class="actions">

            <button
                type="button"
                class="btn-primary"
                id="convertBtn">
                CONVERT ⚡
            </button>

            <button
                type="button"
                class="btn-tab"
                id="clearBtn">
                CLEAR
            </button>

        </div>

        <div class="status" id="status">
            Ready.
        </div>

    </div>


    <!-- OUTPUT -->

    <div class="panel">

        <div class="panel-header">
            <h2>2. Converted Code</h2>
            <select id="languageSelect" class="language-select">
                <option value="xhr">JavaScript XHR</option>
                <option value="fetch">JavaScript Fetch API</option>
                <option value="axios">JavaScript Axios</option>
                <option value="undici">Node.js Undici</option>
                <option value="requests">Python Requests</option>
                <option value="httpx">Python HTTPX</option>
                <option value="aiohttp">Python Aiohttp</option>
                <option value="php_curl">PHP cURL</option>
                <option value="php_guzzle">PHP Guzzle</option>
                <option value="go">Go net/http</option>
                <option value="java">Java HttpClient</option>
                <option value="csharp">C# HttpClient</option>
                <option value="ruby">Ruby Net::HTTP</option>
                <option value="rust">Rust Reqwest</option>
            </select>
        </div>

        <div class="output-box">

            <pre><code
                id="codeOutput"
                class="language-javascript"
            >// Converted code will appear here...</code></pre>

        </div>

        <div class="actions">

            <button
                type="button"
                class="btn-success"
                id="copyBtn">
                COPY CODE 📋
            </button>

        </div>

    </div>

</div>

</div>


<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-markup-templating.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-php.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-go.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-java.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-csharp.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-ruby.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-rust.min.js"></script>

<script>

document.addEventListener('DOMContentLoaded', function () {

    const convertBtn = document.getElementById('convertBtn');
    const copyBtn = document.getElementById('copyBtn');
    const clearBtn = document.getElementById('clearBtn');

    const inputEl = document.getElementById('httpInput');
    const outputEl = document.getElementById('codeOutput');
    const statusEl = document.getElementById('status');
    const languageSelect = document.getElementById('languageSelect');

    let convertedResults = {};
    let currentLanguage = 'xhr';

    const languageMap = {
        xhr: 'javascript',
        fetch: 'javascript',
        axios: 'javascript',
        undici: 'javascript',
        requests: 'python',
        httpx: 'python',
        aiohttp: 'python',
        php_curl: 'php',
        php_guzzle: 'php',
        go: 'go',
        java: 'java',
        csharp: 'csharp',
        ruby: 'ruby',
        rust: 'rust'
    };

    // SHOW OUTPUT

    function showOutput(language) {

        if (!convertedResults[language]) {
            return;
        }

        currentLanguage = language;
        outputEl.textContent = convertedResults[language];
        outputEl.className = 'language-' + languageMap[language];
        languageSelect.value = language;

        if (window.Prism) {
            Prism.highlightElement(outputEl);
        }

    }

    // LANGUAGE SELECT CHANGE

    languageSelect.addEventListener('change', function () {
        showOutput(this.value);
    });

    // CONVERT REQUEST

    convertBtn.addEventListener('click', async function () {

        const rawHttp = inputEl.value;

        if (!rawHttp.trim()) {
            alert("Please paste an HTTP request first.");
            return;
        }

        convertBtn.disabled = true;
        convertBtn.textContent = "CONVERTING...";
        statusEl.textContent = "Converting request...";

        try {

            const response = await fetch('/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    raw_http: rawHttp
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || response.statusText);
            }

            convertedResults = data;
            showOutput(languageSelect.value);
            statusEl.textContent = "Successfully converted into all formats.";

        } catch (err) {

            console.error("Conversion error:", err);
            statusEl.textContent = "Conversion failed.";
            alert("Error during conversion:\n" + err.message);

        } finally {

            convertBtn.disabled = false;
            convertBtn.textContent = "CONVERT ⚡";

        }

    });

    // COPY CODE

    copyBtn.addEventListener('click', async function () {

        const codeText = outputEl.textContent;

        if (!codeText || codeText.startsWith("// Converted code")) {
            alert("No converted code available.");
            return;
        }

        try {
            await navigator.clipboard.writeText(codeText);
            statusEl.textContent = languageSelect.options[languageSelect.selectedIndex].text + " code copied to clipboard.";
        } catch (err) {
            console.error("Clipboard error:", err);
            alert("Error copying code.");
        }

    });

    // CLEAR

    clearBtn.addEventListener('click', function () {

        inputEl.value = '';
        convertedResults = {};
        outputEl.textContent = "// Converted code will appear here...";
        outputEl.className = 'language-javascript';
        currentLanguage = 'xhr';
        languageSelect.value = 'xhr';

        statusEl.textContent = "Ready.";

    });

});

</script>

</body>
</html>
"""


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route("/convert", methods=["POST"])
def convert():

    try:

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "error": "Invalid or missing JSON"
            }), 400

        raw_http = data.get("raw_http", "")

        results = {
            "xhr": http_to_xhr(raw_http),
            "fetch": http_to_fetch(raw_http),
            "axios": http_to_axios(raw_http),
            "undici": http_to_undici(raw_http),
            "requests": http_to_requests(raw_http),
            "httpx": http_to_httpx(raw_http),
            "aiohttp": http_to_aiohttp(raw_http),
            "php_curl": http_to_php_curl(raw_http),
            "php_guzzle": http_to_php_guzzle(raw_http),
            "go": http_to_go(raw_http),
            "java": http_to_java(raw_http),
            "csharp": http_to_csharp(raw_http),
            "ruby": http_to_ruby(raw_http),
            "rust": http_to_rust(raw_http)
        }

        return jsonify(results)

    except ValueError as e:

        return jsonify({
            "error": str(e)
        }), 400

    except Exception as e:

        app.logger.exception("Conversion failed")

        return jsonify({
            "error": str(e)
        }), 500