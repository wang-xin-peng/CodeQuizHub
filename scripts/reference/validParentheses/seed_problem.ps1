<#
.SYNOPSIS
    向 CodeQuizHub 系统添加"有效的括号"题目
.DESCRIPTION
    通过 API 登录并创建题目，支持自定义后端地址、邮箱和密码。
.PARAMETER Url
    后端服务地址，默认 http://localhost:8000
.PARAMETER Email
    教师邮箱，默认 teacher@test.com
.PARAMETER Password
    教师密码，默认 Test1234
.EXAMPLE
    .\seed_problem.ps1
    .\seed_problem.ps1 -Email "teacher@test.com" -Password "Test1234"
    .\seed_problem.ps1 -Url "http://192.168.1.100:8000" -Email "admin@school.edu" -Password "abc123"
#>

param(
    [string]$Url = "http://localhost:8000",
    [string]$Email = "",
    [string]$Password = ""
)

# ─── 配置 ────────────────────────────────────────────────────────────
$PayloadFile = Join-Path $PSScriptRoot "valid_parentheses_payload.json"
$ApiBase = $Url.TrimEnd('/')

# ─── 获取凭据 ────────────────────────────────────────────────────────
if ([string]::IsNullOrEmpty($Email)) {
    $Email = Read-Host "请输入教师邮箱" -ErrorAction Stop
    if ([string]::IsNullOrEmpty($Email)) {
        $Email = "teacher@test.com"
    }
}

if ([string]::IsNullOrEmpty($Password)) {
    $Password = Read-Host "请输入教师密码" -ErrorAction Stop
    if ([string]::IsNullOrEmpty($Password)) {
        $Password = "Test1234"
    }
}

# ─── 检测 payload 文件 ───────────────────────────────────────────────
if (-not (Test-Path $PayloadFile)) {
    Write-Host "[错误] 找不到 payload 文件: $PayloadFile" -ForegroundColor Red
    exit 1
}

Write-Host "`n[1/2] 正在登录 $Email ...`n" -ForegroundColor Cyan

# ─── 登录 ────────────────────────────────────────────────────────────
try {
    $LoginBody = @{ email = $Email; password = $Password } | ConvertTo-Json
    $LoginResp = Invoke-RestMethod -Uri "${ApiBase}/api/auth/login" `
        -Method Post `
        -Body $LoginBody `
        -ContentType "application/json; charset=utf-8" `
        -ErrorAction Stop
} catch {
    Write-Host "[错误] 登录失败，无法连接到 ${ApiBase}" -ForegroundColor Red
    Write-Host "        $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$Token = $LoginResp.data.access_token
if ([string]::IsNullOrEmpty($Token)) {
    Write-Host "[错误] 登录失败，请检查邮箱和密码是否正确" -ForegroundColor Red
    Write-Host "       响应内容: $(($LoginResp | ConvertTo-Json -Compress))" -ForegroundColor DarkGray
    exit 1
}

Write-Host "  ✓ 登录成功" -ForegroundColor Green
Write-Host "`n[2/2] 正在创建题目 ...`n" -ForegroundColor Cyan

# ─── 读取 payload 并以 UTF-8 编码发送 ────────────────────────────────
$ProblemPayload = Get-Content $PayloadFile -Raw -Encoding UTF8
# 明确以 UTF-8 字节发送，避免编码猜测
$Utf8Body = [System.Text.Encoding]::UTF8.GetBytes($ProblemPayload)

# ─── 创建题目 ────────────────────────────────────────────────────────
try {
    $CreateResp = Invoke-RestMethod -Uri "${ApiBase}/api/problems" `
        -Method Post `
        -Body $Utf8Body `
        -ContentType "application/json; charset=utf-8" `
        -Headers @{ Authorization = "Bearer $Token" } `
        -ErrorAction Stop
} catch {
    Write-Host "[错误] 创建题目失败" -ForegroundColor Red
    if ($_.Exception.Response) {
        $Reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $ErrBody = $Reader.ReadToEnd() | ConvertFrom-Json
        Write-Host "       $($ErrBody.message)" -ForegroundColor Red
    } else {
        Write-Host "       $($_.Exception.Message)" -ForegroundColor Red
    }
    exit 1
}

$ProblemId = $CreateResp.data.id
$ProblemTitle = $CreateResp.data.title

Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅ 题目创建成功！                          ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  标题: 有效的括号                           ║" -ForegroundColor Green
Write-Host "║  ID:   $($ProblemId.PadRight(36))║" -ForegroundColor Green
Write-Host "║  难度: easy                                 ║" -ForegroundColor Green
Write-Host "║  语言: python / java / cpp                  ║" -ForegroundColor Green
Write-Host "║  用例: 8 个 (4公开 + 4隐藏)                 ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green

Write-Host "`n现在学生可以提交答案了。`n" -ForegroundColor Cyan
Write-Host "参考解答文件位置:" -ForegroundColor Yellow
Write-Host "  $PSScriptRoot\reference\python\valid_parentheses.py"
Write-Host "  $PSScriptRoot\reference\java\ValidParentheses.java"
Write-Host "  $PSScriptRoot\reference\cpp\valid_parentheses.cpp"
Write-Host ""

exit 0
