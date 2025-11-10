# azptu - Azure PTU CLI (PowerShell Script)
# Execute azptu commands directly without "python" prefix

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonScript = Join-Path $scriptPath "azptu.py"

& python $pythonScript @args