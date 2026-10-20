# Exports Word/PowerPoint files to PDF with the locally installed Microsoft Office (COM automation).
# Usage: powershell.exe -File export_office.ps1 -Kind docx|pptx -Path <windows path> -Pdf <windows pdf path> [-PngDir <dir>]
# For docx the fields (table of contents, figure list, cross-references) are updated and the document is saved
# in place before export, so the editable file carries correct page numbers.
param([string]$Kind, [string]$Path, [string]$Pdf, [string]$PngDir = "")
$ErrorActionPreference = "Stop"
if ($Kind -eq "docx") {
  $w = New-Object -ComObject Word.Application
  $w.Visible = $false; $w.DisplayAlerts = 0
  try {
    $d = $w.Documents.Open($Path, $false, $false)
    $d.Repaginate()
    $d.Fields.Update() | Out-Null
    foreach ($t in $d.TablesOfContents) { $t.Update() }
    foreach ($t in $d.TablesOfFigures) { $t.Update() }
    $d.Repaginate()
    foreach ($t in $d.TablesOfContents) { $t.UpdatePageNumbers() }
    foreach ($t in $d.TablesOfFigures) { $t.UpdatePageNumbers() }
    $pages = $d.ComputeStatistics(2)
    $d.Save()
    $d.ExportAsFixedFormat($Pdf, 17)
    Write-Output "docx pages: $pages"
    $d.Close(0)
  } finally { $w.Quit() }
} elseif ($Kind -eq "pptx") {
  $p = New-Object -ComObject PowerPoint.Application
  try {
    $pres = $p.Presentations.Open($Path, $true, $false, $false)
    $pres.SaveAs($Pdf, 32)
    Write-Output ("pptx slides: " + $pres.Slides.Count)
    if ($PngDir -ne "") { $pres.Export($PngDir, "PNG", 1600, 900) }
    $pres.Close()
  } finally { $p.Quit() }
}
