$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dictPath = Join-Path (Split-Path -Parent (Split-Path -Parent $root)) 'ask-template\addons\languages\tlhingan\dictionary-data\entries.csv'
$allPath = Join-Path $root 'all-surface-counts.csv'
$weightedPath = Join-Path $root 'raw-weighted-word-frequencies.csv'

$dict = Import-Csv -LiteralPath $dictPath
$nameEntries = @($dict | Where-Object {
    $posTags = @($_.part_of_speech -split ',')
    $posTags -contains 'n:name' -or $posTags -contains 'name' -or $_.pos_subtype -eq 'name'
})
$nameHeads = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
$lexicalHeads = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach ($entry in $dict) {
    $posTags = @($entry.part_of_speech -split ',')
    if ($posTags -notcontains 'n:name' -and $posTags -notcontains 'name' -and $entry.pos_subtype -ne 'name') {
        [void]$lexicalHeads.Add($entry.entry_name)
    }
}
foreach ($entry in $nameEntries) {
    # A headword with a non-name dictionary entry is ambiguous without context.
    if (-not $lexicalHeads.Contains($entry.entry_name)) { [void]$nameHeads.Add($entry.entry_name) }
}
# Qel is also a common noun (doctor) in Klingon; source context is not
# reliable enough here to distinguish the title from a personal name.
[void]$nameHeads.Remove('Qel')

# The comic's accompanying name list includes names absent from the dictionary.
# Only single-token entries are used; multiword name fragments are too ambiguous.
$comicNameFile = Join-Path (Split-Path -Parent $root) 'starfleet-academy-18\known-names.txt'
if (Test-Path -LiteralPath $comicNameFile) {
    foreach ($line in Get-Content -LiteralPath $comicNameFile) {
        $candidate = $line.Trim()
        if ($candidate -match "^[A-Za-z']+$" -and -not $lexicalHeads.Contains($candidate)) { [void]$nameHeads.Add($candidate) }
    }
}

$suffixes = @("'e'", 'vaD', 'Daq', "vo'", "mo'", 'mey', "pu'", "Du'", 'Hom', 'oy', 'wIj', "ma'", 'maj', 'lIj', "lI'", 'Daj', 'chaj', "na'", 'qoq')
function Find-NameHead([string]$word) {
    $candidate = $word
    for ($depth = 0; $depth -le 3; $depth++) {
        if ($nameHeads.Contains($candidate)) { return $candidate }
        $stripped = $false
        foreach ($suffix in $suffixes) {
            if ($candidate.Length -gt $suffix.Length -and $candidate.EndsWith($suffix, [StringComparison]::Ordinal)) {
                $candidate = $candidate.Substring(0, $candidate.Length - $suffix.Length)
                $stripped = $true
                break
            }
        }
        if (-not $stripped) { break }
    }
    return $null
}

$all = @(Import-Csv -LiteralPath $allPath)
$kept = [System.Collections.Generic.List[object]]::new()
$removed = [System.Collections.Generic.List[object]]::new()
foreach ($row in $all) {
    $head = Find-NameHead $row.Word
    if ($null -ne $head) {
        $removed.Add([pscustomobject]@{
            Word=$row.Word; MatchedName=$head; HamletCount=$row.HamletCount
            DiscoveryCount=$row.DiscoveryCount; ComicCount=$row.ComicCount
            HamletPer1000=$row.HamletPer1000; DiscoveryPer1000=$row.DiscoveryPer1000
            ComicPer1000=$row.ComicPer1000; WeightedPer1000=$row.WeightedPer1000
        })
    } else { $kept.Add($row) }
}
$filteredWeighted = @(Import-Csv -LiteralPath $weightedPath | Where-Object { $null -eq (Find-NameHead $_.Word) })
$kept | Export-Csv -LiteralPath (Join-Path $root "all-surface-counts-no-names.csv") -NoTypeInformation -Encoding utf8
$filteredWeighted | Export-Csv -LiteralPath (Join-Path $root "raw-weighted-word-frequencies-no-names.csv") -NoTypeInformation -Encoding utf8
$removed | Sort-Object Word | Export-Csv -LiteralPath (Join-Path $root "removed-name-counts.csv") -NoTypeInformation -Encoding utf8
"Dictionary name entries: $($nameEntries.Count)"
"Name heads including comic supplement: $($nameHeads.Count)"
"Removed forms: $($removed.Count)"
"Retained forms: $($kept.Count)"
"Removed token occurrences: $((($removed | ForEach-Object { [int]$_.HamletCount + [int]$_.DiscoveryCount + [int]$_.ComicCount } | Measure-Object -Sum).Sum))"
