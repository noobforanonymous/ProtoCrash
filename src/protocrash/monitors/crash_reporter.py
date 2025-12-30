"""
Enhanced crash reporting with multiple output formats
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List
from protocrash.core.types import CrashInfo
from protocrash.monitors.crash_bucketing import CrashBucket
from protocrash.monitors.crash_classifier import CrashClassifier
class CrashReporter:
    """Generate crash reports in multiple formats"""
    def __init__(self, output_dir: str = "crash_reports"):
        """
        Initialize crash reporter
        Args:
            output_dir: Directory for crash reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.classifier = CrashClassifier()  # Backward compatibility
    def generate_crash_report(
        self,
        bucket: CrashBucket,
        crash_info: CrashInfo,
        format: str = "json"
    ) -> str:
        """
        Generate crash report
        Args:
            bucket: Crash bucket
            crash_info: Crash information
            format: Output format ("json", "html", "markdown")
        Returns:
            Path to generated report
        """
        if format == "json":
            return self._generate_json_report(bucket, crash_info)
        elif format == "html":
            return self._generate_html_report(bucket, crash_info)
        elif format == "markdown":
            return self._generate_markdown_report(bucket, crash_info)
        else:
            raise ValueError(f"Unknown format: {format}")
    def _generate_json_report(self, bucket: CrashBucket, crash_info: CrashInfo) -> str:
        """Generate JSON report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'bucket_id': bucket.bucket_id,
            'crash_hash': bucket.crash_hash,
            'crash_type': bucket.crash_type,
            'exploitability': bucket.exploitability,
            'count': bucket.count,
            'crash_info': {
                'crashed': crash_info.crashed,
                'signal_number': crash_info.signal_number,
                'exit_code': crash_info.exit_code,
                'input_size': len(crash_info.input_data) if crash_info.input_data else 0,
                'stderr': crash_info.stderr.decode('utf-8', errors='ignore') if crash_info.stderr else None
            },
            'stack_trace': bucket.stack_trace.to_dict() if bucket.stack_trace else None
        }
        output_path = self.output_dir / f"crash_{bucket.crash_hash}.json"
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return str(output_path)
    def _generate_html_report(self, bucket: CrashBucket, crash_info: CrashInfo) -> str:
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Crash Report - {bucket.crash_hash}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #d32f2f; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }}
        .label {{ font-weight: bold; color: #1976d2; }}
        pre {{ background: #263238; color: #aed581; padding: 10px; border-radius: 3px; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #1976d2; color: white; }}
        .high {{ color: #d32f2f; font-weight: bold; }}
        .medium {{ color: #f57c00; font-weight: bold; }}
        .low {{ color: #388e3c; }}
    </style>
</head>
<body>
    <h1>Crash Report</h1>
    <div class="section">
        <h2>Summary</h2>
        <table>
            <tr><th>Field</th><th>Value</th></tr>
            <tr><td class="label">Crash Type</td><td>{bucket.crash_type}</td></tr>
            <tr><td class="label">Bucket ID</td><td>{bucket.bucket_id}</td></tr>
            <tr><td class="label">Crash Hash</td><td>{bucket.crash_hash}</td></tr>
            <tr><td class="label">Exploitability</td><td class="{bucket.exploitability.lower() if bucket.exploitability else 'unknown'}">{bucket.exploitability or 'UNKNOWN'}</td></tr>
            <tr><td class="label">Occurrence Count</td><td>{bucket.count}</td></tr>
            <tr><td class="label">Signal Number</td><td>{crash_info.signal_number or 'N/A'}</td></tr>
            <tr><td class="label">Exit Code</td><td>{crash_info.exit_code}</td></tr>
            <tr><td class="label">Input Size</td><td>{len(crash_info.input_data) if crash_info.input_data else 0} bytes</td></tr>
        </table>
    </div>
    <div class="section">
        <h2>Stack Trace</h2>
        <pre>{str(bucket.stack_trace) if bucket.stack_trace else 'No stack trace available'}</pre>
    </div>
    <div class="section">
        <h2>Error Output</h2>
        <pre>{crash_info.stderr.decode('utf-8', errors='ignore') if crash_info.stderr else 'No stderr output'}</pre>
    </div>
    <div class="section">
        <h2>Reproduction</h2>
        <p>To reproduce this crash, use the saved input from: <code>crash_{bucket.crash_hash}.input</code></p>
    </div>
    <footer style="margin-top: 30px; color: #666; font-size: 12px;">
        Generated at: {datetime.now().isoformat()}
    </footer>
</body>
</html>"""
        output_path = self.output_dir / f"crash_{bucket.crash_hash}.html"
        with open(output_path, 'w') as f:
            f.write(html)
        # Save input data
        if crash_info.input_data:
            input_path = self.output_dir / f"crash_{bucket.crash_hash}.input"
            with open(input_path, 'wb') as f:
                f.write(crash_info.input_data)
        return str(output_path)
    def _generate_markdown_report(self, bucket: CrashBucket, crash_info: CrashInfo) -> str:
        """Generate Markdown report"""
        md = f"""# Crash Report: {bucket.crash_hash}
## Summary
| Field | Value |
|-------|-------|
| Crash Type | {bucket.crash_type} |
| Bucket ID | {bucket.bucket_id} |
| Exploitability | **{bucket.exploitability or 'UNKNOWN'}** |
| Count | {bucket.count} |
| Signal | {crash_info.signal_number or 'N/A'} |
| Exit Code | {crash_info.exit_code} |
| Input Size | {len(crash_info.input_data) if crash_info.input_data else 0} bytes |
## Stack Trace
```
{str(bucket.stack_trace) if bucket.stack_trace else 'No stack trace available'}
```
## Error Output
```
{crash_info.stderr.decode('utf-8', errors='ignore') if crash_info.stderr else 'No stderr output'}
```
## Reproduction
To reproduce this crash:
1. Use input file: `crash_{bucket.crash_hash}.input`
2. Run the target with this input
---
*Generated: {datetime.now().isoformat()}*
"""
        output_path = self.output_dir / f"crash_{bucket.crash_hash}.md"
        with open(output_path, 'w') as f:
            f.write(md)
        return str(output_path)
    def generate_summary_report(self, buckets: List[CrashBucket], format: str = "html") -> str:
        """
        Generate summary report for multiple crashes
        Args:
            buckets: List of crash buckets
            format: Output format
        Returns:
            Path to summary report
        """
        if format == "html":
            return self._generate_html_summary(buckets)
        elif format == "markdown":
            return self._generate_markdown_summary(buckets)
        else:
            raise ValueError(f"Unknown format: {format}")
    def _generate_html_summary(self, buckets: List[CrashBucket]) -> str:
        """Generate HTML summary report"""
        rows = ""
        for bucket in sorted(buckets, key=lambda b: b.count, reverse=True):
            rows += f"""<tr>
                <td>{bucket.crash_type}</td>
                <td><code>{bucket.bucket_id[:12]}</code></td>
                <td class="{bucket.exploitability.lower() if bucket.exploitability else 'unknown'}">
                    {bucket.exploitability or 'UNKNOWN'}
                </td>
                <td>{bucket.count}</td>
            </tr>"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Crash Summary Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #1976d2; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #1976d2; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .high {{ color: #d32f2f; font-weight: bold; }}
        .medium {{ color: #f57c00; font-weight: bold; }}
        .low {{ color: #388e3c; }}
    </style>
</head>
<body>
    <h1>Crash Summary Report</h1>
    <p>Total unique crashes: <strong>{len(buckets)}</strong></p>
    <p>Total occurrences: <strong>{sum(b.count for b in buckets)}</strong></p>
    <table>
        <thead>
            <tr>
                <th>Crash Type</th>
                <th>Bucket ID</th>
                <th>Exploitability</th>
                <th>Count</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    <footer style="margin-top: 30px; color: #666; font-size: 12px;">
        Generated at: {datetime.now().isoformat()}
    </footer>
</body>
</html>"""
        output_path = self.output_dir / "crash_summary.html"
        with open(output_path, 'w') as f:
            f.write(html)
        return str(output_path)
    def _generate_markdown_summary(self, buckets: List[CrashBucket]) -> str:
        """Generate Markdown summary report"""
        total_unique = len(buckets)
        total_occurrences = sum(b.count for b in buckets)
        rows = ""
        for bucket in sorted(buckets, key=lambda b: b.count, reverse=True):
            rows += f"| {bucket.crash_type} | `{bucket.bucket_id[:12]}` | **{bucket.exploitability or 'UNKNOWN'}** | {bucket.count} |\n"
        md = f"""# Crash Summary Report
**Total Unique Crashes:** {total_unique}
**Total Occurrences:** {total_occurrences}
## Crashes
| Crash Type | Bucket ID | Exploitability | Count |
|------------|-----------|----------------|-------|
{rows}
---
*Generated: {datetime.now().isoformat()}*
"""
        output_path = self.output_dir / "crash_summary.md"
        with open(output_path, 'w') as f:
            f.write(md)
        return str(output_path)
    # Old API compatibility methods
    def save_crash(self, crash_info, crash_id=None):
        """Old API: Save crash to disk"""
        from protocrash.monitors.crash_bucketing import CrashBucketing
        # Generate crash ID if not provided
        if crash_id is None:
            crash_id = self.classifier.generate_crash_id(crash_info)
        # Save report
        output_path = self.output_dir / f"{crash_id}.json"
        exploitability = self.classifier.assess_exploitability(crash_info)
        report = {
            'crash_id': crash_id,
            'crashed': crash_info.crashed,
            'crash_type': crash_info.crash_type.value if crash_info.crash_type else 'Unknown',
            'exploitability': exploitability,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        # Save input file
        if crash_info.input_data:
            input_path = self.output_dir / f"{crash_id}.input"
            with open(input_path, 'wb') as f:
                f.write(crash_info.input_data)
        return Path(output_path)
    def generate_report(self, crash_info, crash_id):
        """Old API: Generate report dict"""
        exploitability = self.classifier.assess_exploitability(crash_info)
        return {
            'crash_id': crash_id,
            'crashed': crash_info.crashed,
            'crash_type': crash_info.crash_type.value if crash_info.crash_type else 'Unknown',
            'exploitability': exploitability,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
    def list_crashes(self):
        """Old API: List all crashes"""
        crashes = []
        for json_file in self.output_dir.glob("*.json"):
            crashes.append(json_file.stem)
        return crashes
    def get_crash_report(self, crash_id):
        """Old API: Get crash report by ID"""
        json_file = self.output_dir / f"{crash_id}.json"
        if json_file.exists():
            with open(json_file, 'r') as f:
                data = json.load(f)
            return {'crash_id': crash_id, **data}
        return None
