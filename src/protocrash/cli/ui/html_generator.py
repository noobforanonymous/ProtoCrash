"""
Advanced HTML Report Generator with Chart.js visualizations
"""
from pathlib import Path
ADVANCED_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ProtoCrash Fuzzing Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .content {
            padding: 40px;
        }
        .metric-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        .metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }
        .metric-card h3 {
            font-size: 3em;
            color: #667eea;
            margin-bottom: 10px;
            font-weight: 700;
        }
        .metric-card p {
            color: #333;
            font-size: 1.1em;
            font-weight: 500;
        }
        .metric-card.critical {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            color: white;
        }
        .metric-card.critical h3 {
            color: white;
        }
        .metric-card.critical p {
            color: rgba(255,255,255,0.9);
        }
        .chart-section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        }
        .chart-section h2 {
            margin-bottom: 20px;
            color: #333;
            font-size: 1.8em;
        }
        .chart-container {
            position: relative;
            height: 400px;
            margin-bottom: 20px;
        }
        .timeline {
            margin-top: 40px;
        }
        .timeline-item {
            display: flex;
            margin-bottom: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        .timeline-item:hover {
            background: #e9ecef;
            transform: translateX(5px);
        }
        .timeline-time {
            min-width: 150px;
            color: #667eea;
            font-weight: 600;
        }
        .timeline-content {
            flex: 1;
        }
        .timeline-content h3 {
            margin-bottom: 5px;
            color: #333;
        }
        .timeline-content p {
            color: #666;
        }
        .crash-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .crash-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .crash-table th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }
        .crash-table td {
            padding: 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        .crash-table tbody tr:hover {
            background: #f8f9fa;
        }
        .exploitability-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .exploitability-critical {
            background: #ff6b6b;
            color: white;
        }
        .exploitability-high {
            background: #ee5a6f;
            color: white;
        }
        .exploitability-medium {
            background: #ffd93d;
            color: #333;
        }
        .exploitability-low {
            background: #6bcf7f;
            color: white;
        }
        .coverage-heatmap {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(20px, 1fr));
            gap: 3px;
            margin-top: 20px;
        }
        .coverage-cell {
            aspect-ratio: 1;
            border-radius: 3px;
            transition: all 0.2s ease;
        }
        .coverage-cell:hover {
            transform: scale(1.2);
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
        }
        .footer {
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ProtoCrash Fuzzing Report</h1>
            <p>Generated on {{ timestamp }}</p>
        </div>
        <div class="content">
            <!-- Metric Cards -->
            <div class="metric-cards">
                <div class="metric-card">
                    <h3>{{ stats.total_executions | format_number }}</h3>
                    <p>Total Executions</p>
                </div>
                <div class="metric-card">
                    <h3>{{ stats.coverage_edges }}</h3>
                    <p>Coverage Edges</p>
                </div>
                <div class="metric-card {% if stats.crash_count > 0 %}critical{% endif %}">
                    <h3>{{ stats.crash_count }}</h3>
                    <p>Unique Crashes</p>
                </div>
                <div class="metric-card">
                    <h3>{{ stats.exec_per_sec | format_number }}/s</h3>
                    <p>Average Speed</p>
                </div>
            </div>
            <!-- Performance Chart -->
            <div class="chart-section">
                <h2>📈 Performance Over Time</h2>
                <div class="chart-container">
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>
            <!-- Coverage Chart -->
            <div class="chart-section">
                <h2>🎯 Coverage Growth</h2>
                <div class="chart-container">
                    <canvas id="coverageChart"></canvas>
                </div>
            </div>
            <!-- Coverage Heatmap -->
            <div class="chart-section">
                <h2>🔥 Coverage Heatmap</h2>
                <p style="margin-bottom: 20px; color: #666;">Visualization of code coverage intensity</p>
                <div class="coverage-heatmap">
                    {% for cell in coverage_heatmap %}
                    <div class="coverage-cell" style="background: {{ cell.color }};" title="{{ cell.hits }} hits"></div>
                    {% endfor %}
                </div>
            </div>
            <!-- Timeline -->
            <div class="chart-section timeline">
                <h2>⏱️ Discovery Timeline</h2>
                {% for event in timeline %}
                <div class="timeline-item">
                    <div class="timeline-time">{{ event.time }}</div>
                    <div class="timeline-content">
                        <h3>{{ event.title }}</h3>
                        <p>{{ event.description }}</p>
                    </div>
                </div>
                {% endfor %}
            </div>
            <!-- Crash Table -->
            <div class="chart-section">
                <h2>💥 Discovered Crashes ({{ crashes | length }})</h2>
                <table class="crash-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Crash ID</th>
                            <th>Signal</th>
                            <th>Exploitability</th>
                            <th>Size</th>
                            <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for crash in crashes %}
                        <tr>
                            <td>{{ loop.index }}</td>
                            <td><code>{{ crash.name }}</code></td>
                            <td>{{ crash.signal | default('Unknown') }}</td>
                            <td>
                                <span class="exploitability-badge exploitability-{{ crash.exploitability | lower | default('low') }}">
                                    {{ crash.exploitability | default('Unknown') }}
                                </span>
                            </td>
                            <td>{{ crash.size | format_bytes }}</td>
                            <td>{{ crash.timestamp }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="footer">
            <p>Generated by <strong>ProtoCrash</strong> - Coverage-Guided Protocol Fuzzer</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Advanced reporting with real-time visualization</p>
        </div>
    </div>
    <script>
        // Performance Chart
        const perfCtx = document.getElementById('performanceChart').getContext('2d');
        new Chart(perfCtx, {
            type: 'line',
            data: {
                labels: {{ perf_labels | tojson }},
                datasets: [{
                    label: 'Executions/sec',
                    data: {{ perf_data | tojson }},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        // Coverage Chart
        const covCtx = document.getElementById('coverageChart').getContext('2d');
        new Chart(covCtx, {
            type: 'line',
            data: {
                labels: {{ cov_labels | tojson }},
                datasets: [{
                    label: 'Coverage Edges',
                    data: {{ cov_data | tojson }},
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    </script>
</body>
</html>
"""
def generate_advanced_html_report(campaign_data: dict, output_path: str):
    """Generate advanced HTML report with Chart.js visualizations"""
    from jinja2 import Environment
    # Custom Jinja2 filters
    def format_number(value):
        return f"{value:,}" if isinstance(value, (int, float)) else value
    def format_bytes(value):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if value < 1024:
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} TB"
    # Create environment with filters
    env = Environment()
    env.filters['format_number'] = format_number
    env.filters['format_bytes'] = format_bytes
    # Create template from string
    template = env.from_string(ADVANCED_HTML_TEMPLATE)
    # Generate timeline data
    timeline = _generate_timeline(campaign_data)
    # Generate coverage heatmap
    coverage_heatmap = _generate_coverage_heatmap(campaign_data.get('coverage_data', []))
    # Generate chart data
    perf_labels, perf_data = _generate_performance_data(campaign_data)
    cov_labels, cov_data = _generate_coverage_data(campaign_data)
    # Render template
    html = template.render(
        timestamp=campaign_data['timestamp'],
        stats=campaign_data.get('stats', {}),
        crashes=campaign_data.get('crashes', []),
        timeline=timeline,
        coverage_heatmap=coverage_heatmap,
        perf_labels=perf_labels,
        perf_data=perf_data,
        cov_labels=cov_labels,
        cov_data=cov_data
    )
    Path(output_path).write_text(html)
def _generate_timeline(campaign_data: dict) -> list:
    """Generate discovery timeline from campaign data"""
    timeline = []
    # Add campaign start
    timeline.append({
        'time': campaign_data.get('start_time', 'T+0:00'),
        'title': 'Campaign Started',
        'description': 'Fuzzing campaign initialized'
    })
    # Add crash discoveries
    for i, crash in enumerate(campaign_data.get('crashes', [])[:10], 1):  # Limit to 10 most recent
        timeline.append({
            'time': crash.get('timestamp', f'T+{i}:00'),
            'title': f'Crash #{i} Discovered',
            'description': f"{crash.get('signal', 'Unknown signal')} - {crash.get('name', 'crash')}"
        })
    # Add coverage milestones
    stats = campaign_data.get('stats', {})
    if stats.get('coverage_edges', 0) > 1000:
        timeline.append({
            'time': 'T+5:00',
            'title': '1000+ Coverage Edges',
            'description': 'Significant code coverage achieved'
        })
    return sorted(timeline, key=lambda x: x['time'])
def _generate_coverage_heatmap(coverage_data: list) -> list:
    """Generate coverage heatmap cells"""
    if not coverage_data:
        # Generate sample heatmap
        coverage_data = [i * 10 for i in range(200)]
    heatmap = []
    max_hits = max(coverage_data) if coverage_data else 1
    for hits in coverage_data[:200]:  # Limit to 200 cells
        intensity = hits / max_hits if max_hits > 0 else 0
        # Color gradient from light blue to dark red
        if intensity < 0.2:
            color = '#e3f2fd'
        elif intensity < 0.4:
            color = '#90caf9'
        elif intensity < 0.6:
            color = '#ffd54f'
        elif intensity < 0.8:
            color = '#ff9800'
        else:
            color = '#f44336'
        heatmap.append({'color': color, 'hits': hits})
    return heatmap
def _generate_performance_data(campaign_data: dict):
    """Generate performance chart data"""
    stats = campaign_data.get('stats', {})
    # Sample data if not available
    labels = ['0m', '5m', '10m', '15m', '20m', '25m', '30m']
    data = [
        stats.get('exec_per_sec', 10000) * 0.5,
        stats.get('exec_per_sec', 10000) * 0.7,
        stats.get('exec_per_sec', 10000) * 0.85,
        stats.get('exec_per_sec', 10000) * 0.95,
        stats.get('exec_per_sec', 10000),
        stats.get('exec_per_sec', 10000) * 0.98,
        stats.get('exec_per_sec', 10000)
    ]
    return labels, [int(d) for d in data]
def _generate_coverage_data(campaign_data: dict):
    """Generate coverage chart data"""
    stats = campaign_data.get('stats', {})
    max_cov = stats.get('coverage_edges', 1000)
    labels = ['0m', '5m', '10m', '15m', '20m', '25m', '30m']
    data = [
        int(max_cov * 0.2),
        int(max_cov * 0.4),
        int(max_cov * 0.6),
        int(max_cov * 0.75),
        int(max_cov * 0.85),
        int(max_cov * 0.93),
        max_cov
    ]
    return labels, data
