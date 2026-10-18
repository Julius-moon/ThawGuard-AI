param([int]$Port = 8017, [switch]$OpenBrowser)
$ErrorActionPreference = 'Stop'
$demoFile = Join-Path $PSScriptRoot 'index.html'
if (-not (Test-Path -LiteralPath $demoFile)) { throw 'index.html is missing. Extract the complete ZIP first.' }
$demoBytes = [System.IO.File]::ReadAllBytes($demoFile)
$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
$listener.Start()
$boundPort = ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
$demoUrl = 'http://127.0.0.1:' + $boundPort + '/'
Write-Host ('ThawGuard offline demo: ' + $demoUrl)
Write-Host 'Keep this window open. Press Ctrl+C to stop. No internet or administrator rights required.'
if ($OpenBrowser) { Start-Process -FilePath $demoUrl }
try {
 while ($true) {
  $client = $listener.AcceptTcpClient()
  try {
   $client.ReceiveTimeout = 4000; $client.SendTimeout = 8000
   $stream = $client.GetStream()
   $reader = [System.IO.StreamReader]::new($stream,[System.Text.Encoding]::ASCII,$false,1024,$true)
   $firstLine = $reader.ReadLine(); $headerLength = 0
   do { $line = $reader.ReadLine(); if ($null -eq $line) { break }; $headerLength += $line.Length; if ($headerLength -gt 16384) { throw 'Request headers too large' } } while ($line.Length -gt 0)
   $parts = $firstLine -split ' '
   $valid = $parts.Length -ge 2 -and $parts[0] -in @('GET','HEAD') -and ($parts[1].Split('?')[0]) -in @('/','/index.html')
   if ($valid) {
    $payload = $demoBytes; $status = '200 OK'; $contentType = 'text/html; charset=utf-8'
   } else {
    $payload = [System.Text.Encoding]::UTF8.GetBytes('Not found'); $status = '404 Not Found'; $contentType = 'text/plain; charset=utf-8'
   }
   $header = 'HTTP/1.1 ' + $status + "`r`nContent-Type: " + $contentType + "`r`nContent-Length: " + $payload.Length + "`r`nCache-Control: no-store`r`nConnection: close`r`n`r`n"
   $headerBytes = [System.Text.Encoding]::ASCII.GetBytes($header)
   $stream.Write($headerBytes,0,$headerBytes.Length)
   if ($parts[0] -ne 'HEAD') { $stream.Write($payload,0,$payload.Length) }
   $stream.Flush(); $reader.Dispose()
  } catch { Write-Verbose 'A local browser request ended before completion.' }
  finally { $client.Dispose() }
 }
} finally { $listener.Stop() }
