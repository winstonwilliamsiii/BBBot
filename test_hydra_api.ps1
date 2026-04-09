param(
    [ValidateSet("Health", "Bootstrap", "Analyze")]
    [string]$Action = "Health",

    [string]$BaseUrl = "http://127.0.0.1:5001",

    [string]$Ticker = "UNH"
)

$endpoint = switch ($Action) {
    "Health" { "/hydra/health" }
    "Bootstrap" { "/hydra/bootstrap" }
    "Analyze" { "/hydra/analyze" }
}

$uri = "$($BaseUrl.TrimEnd('/'))$endpoint"

try {
    if ($Action -eq "Analyze") {
        $body = @{
            ticker = $Ticker
            news_headlines = @(
                "Healthcare leaders upgraded after strong guidance",
                "Momentum remains positive across managed-care names"
            )
        } | ConvertTo-Json -Depth 5

        $response = Invoke-RestMethod -Method Post -Uri $uri -Body $body -ContentType "application/json"
    }
    elseif ($Action -eq "Bootstrap") {
        $response = Invoke-RestMethod -Method Post -Uri $uri
    }
    else {
        $response = Invoke-RestMethod -Method Get -Uri $uri
    }

    $response | ConvertTo-Json -Depth 10
}
catch {
    Write-Error "Hydra API $Action failed: $($_.Exception.Message)"
    exit 1
}