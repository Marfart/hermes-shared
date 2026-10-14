Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = 'Stop'
$homeDir = Join-Path $env:LOCALAPPDATA 'hermes'
$envPath = Join-Path $homeDir '.env'
$env:NOTION_TOKEN_ENTRY_RESULT = 'cancelled'

$form = New-Object System.Windows.Forms.Form
$form.Text = '安全保存 Notion API Token'
$form.Size = New-Object System.Drawing.Size(520, 185)
$form.StartPosition = 'CenterScreen'
$form.TopMost = $true
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.FormBorderStyle = 'FixedDialog'

$label = New-Object System.Windows.Forms.Label
$label.Text = '请粘贴刚刷新生成的 Notion API Token。输入内容仅在本机使用，不会显示或发送到聊天。'
$label.Location = New-Object System.Drawing.Point(18, 15)
$label.Size = New-Object System.Drawing.Size(470, 42)
$form.Controls.Add($label)

$box = New-Object System.Windows.Forms.TextBox
$box.Location = New-Object System.Drawing.Point(18, 63)
$box.Size = New-Object System.Drawing.Size(470, 25)
$box.UseSystemPasswordChar = $true
$form.Controls.Add($box)

$save = New-Object System.Windows.Forms.Button
$save.Text = '本机保存并测试'
$save.Location = New-Object System.Drawing.Point(260, 105)
$save.Size = New-Object System.Drawing.Size(140, 30)
$save.DialogResult = [System.Windows.Forms.DialogResult]::OK
$form.Controls.Add($save)
$form.AcceptButton = $save

$cancel = New-Object System.Windows.Forms.Button
$cancel.Text = '取消'
$cancel.Location = New-Object System.Drawing.Point(410, 105)
$cancel.Size = New-Object System.Drawing.Size(78, 30)
$cancel.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($cancel)
$form.CancelButton = $cancel

$result = $form.ShowDialog()
if ($result -ne [System.Windows.Forms.DialogResult]::OK) { exit 0 }
$token = $box.Text.Trim()
$box.Clear()
$form.Dispose()
if (-not $token) {
  [System.Windows.Forms.MessageBox]::Show('没有输入 Token，未保存。','未保存','OK','Warning') | Out-Null
  exit 2
}
if ($token -match '[\r\n]') {
  [System.Windows.Forms.MessageBox]::Show('输入格式无效，未保存。','未保存','OK','Warning') | Out-Null
  exit 2
}

# Preserve unrelated Hermes environment entries and replace only the Notion key.
$lines = @()
if (Test-Path -LiteralPath $envPath) { $lines = @(Get-Content -LiteralPath $envPath -ErrorAction Stop) }
$lines = @($lines | Where-Object { $_ -notmatch '^\s*NOTION_API_KEY\s*=' })
$lines += "NOTION_API_KEY=$token"
[System.IO.File]::WriteAllLines($envPath, $lines, [System.Text.UTF8Encoding]::new($false))

# Run a minimal read-only authentication check; never print response/token data.
try {
  $headers = @{ Authorization = "Bearer $token"; 'Notion-Version' = '2025-09-03' }
  $null = Invoke-RestMethod -Method Get -Uri 'https://api.notion.com/v1/users/me' -Headers $headers -TimeoutSec 20
  $env:NOTION_TOKEN_ENTRY_RESULT = 'saved_and_valid'
  [System.Windows.Forms.MessageBox]::Show('Token 已保存到 Hermes 本地 .env；Notion API 只读认证测试通过。没有读取或修改页面内容。','完成','OK','Information') | Out-Null
} catch {
  $env:NOTION_TOKEN_ENTRY_RESULT = 'saved_but_test_failed'
  [System.Windows.Forms.MessageBox]::Show('Token 已保存在 Hermes 本地 .env，但只读 API 认证测试未通过。请确认 Token 是否正确，以及 Notion 网络连接是否可用。错误详情未记录。','测试未通过','OK','Warning') | Out-Null
} finally {
  $token = $null
  [GC]::Collect()
}
exit 0
