from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FileResult:
    """Result of converting a single subtitle file."""
    filename: str
    success: bool
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)


@dataclass
class ConversionSummary:
    """Summary of all subtitle file conversions."""
    total: int = 0
    successful: int = 0
    failed: int = 0
    results: List[FileResult] = field(default_factory=list)
    
    def add_success(self, filename: str, warnings: List[str] = None):
        """Add a successful conversion result."""
        self.results.append(FileResult(filename, True, warnings=warnings or []))
        self.total += 1
        self.successful += 1
    
    def add_failure(self, filename: str, error: str):
        """Add a failed conversion result."""
        self.results.append(FileResult(filename, False, error_message=error))
        self.total += 1
        self.failed += 1
    
    def format_summary(self) -> str:
        """Format a concise summary message."""
        if self.total == 0:
            return "No VTT files found to convert."
        
        lines = [f"VTT Conversion: {self.successful}/{self.total} successful"]
        
        # Show warnings if any
        warnings_found = [r for r in self.results if r.warnings]
        if warnings_found:
            lines.append("  Warnings (auto-fixed):")
            for result in warnings_found:
                lines.append(f"    • {result.filename}: {len(result.warnings)} issue(s) sanitized")
        
        # Show failures if any
        failures = [r for r in self.results if not r.success]
        if failures:
            lines.append("  Errors:")
            for result in failures:
                lines.append(f"    ✗ {result.filename}: {result.error_message}")
        
        return "\n".join(lines)


@dataclass
class ManifestResult:
    """Result of manifest generation."""
    ism_created: bool = False
    ism_skipped: bool = False
    ismc_created: bool = False
    ismc_skipped: bool = False
    manifest_name: str = ""


@dataclass
class ProcessingSummary:
    """Overall summary of VTT conversion and manifest generation."""
    conversion_summary: Optional[ConversionSummary] = None
    manifest_result: Optional[ManifestResult] = None
    
    def format_summary(self) -> str:
        """Format a comprehensive summary message."""
        lines = ["\n" + "="*70]
        lines.append("PROCESSING SUMMARY")
        lines.append("="*70)
        
        # VTT Conversion section
        if self.conversion_summary and self.conversion_summary.total > 0:
            lines.append("\n" + self.conversion_summary.format_summary())
        else:
            lines.append("\nVTT Conversion: No VTT files found")
        
        # Manifest Generation section
        if self.manifest_result:
            lines.append("\nManifest Generation:")
            if self.manifest_result.ism_created:
                lines.append(f"  ✓ Server manifest created: {self.manifest_result.manifest_name}.ism")
            elif self.manifest_result.ism_skipped:
                lines.append(f"  ⊘ Server manifest skipped: {self.manifest_result.manifest_name}.ism (already exists)")
            
            if self.manifest_result.ismc_created:
                lines.append(f"  ✓ Client manifest created: {self.manifest_result.manifest_name}.ismc")
            elif self.manifest_result.ismc_skipped:
                lines.append(f"  ⊘ Client manifest skipped: {self.manifest_result.manifest_name}.ismc (already exists)")
        
        lines.append("="*70 + "\n")
        return "\n".join(lines)
