@echo off
chcp 65001 >nul
title CodeQuizHub - 创建题目：有效的括号

echo ==============================================
echo   CodeQuizHub - 题目创建脚本
echo   题目: 有效的括号 (Valid Parentheses)
echo ==============================================
echo.

:: 执行 PowerShell 脚本
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0seed_problem.ps1" %*

:: 检查退出码
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 脚本执行出错，退出码: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

pause
