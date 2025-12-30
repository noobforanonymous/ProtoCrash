"""
Performance benchmarks for protocol parsers and mutators
"""

import time
import json
import struct
from statistics import mean, median, stdev
from typing import List, Dict, Any

from protocrash.parsers.dns_parser import DNSParser, DNSMessage, DNSQuestion, DNSResourceRecord, DNSType, DNSClass
from protocrash.parsers.smtp_parser import SMTPParser, SMTPMessage, SMTPCommandLine, SMTPResponse
from protocrash.mutators.dns_mutator import DNSMutator
from protocrash.mutators.smtp_mutator import SMTPMutator


class ProtocolBenchmark:
    """Comprehensive protocol performance benchmarking"""
    
    def __init__(self):
        self.results = {}
    
    def benchmark_dns_parsing(self, iterations: int = 10000) -> Dict[str, Any]:
        """Benchmark DNS parsing throughput"""
        parser = DNSParser()
        
        # Test data: simple query
        msg = DNSMessage(
            transaction_id=0x1234,
            flags=0x0100,
            questions=[DNSQuestion('example.com', DNSType.A, DNSClass.IN)]
        )
        test_data = parser.reconstruct(msg)
        
        # Warmup
        for _ in range(100):
            parser.parse(test_data)
        
        # Benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            parser.parse(test_data)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        total_time = sum(times)
        throughput = iterations / total_time
        
        return {
            'test': 'DNS Parsing',
            'iterations': iterations,
            'total_time_s': total_time,
            'throughput_msg_per_sec': throughput,
            'mean_latency_us': mean(times) * 1_000_000,
            'median_latency_us': median(times) * 1_000_000,
            'p95_latency_us': sorted(times)[int(iterations * 0.95)] * 1_000_000,
            'p99_latency_us': sorted(times)[int(iterations * 0.99)] * 1_000_000,
            'stddev_latency_us': stdev(times) * 1_000_000 if len(times) > 1 else 0
        }
    
    def benchmark_smtp_parsing(self, iterations: int = 10000) -> Dict[str, Any]:
        """Benchmark SMTP parsing throughput"""
        parser = SMTPParser()
        
        # Test data: HELO command
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('HELO', 'client.example.com')]
        test_data = parser.reconstruct(msg)
        
        # Warmup
        for _ in range(100):
            parser.parse(test_data)
        
        # Benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            parser.parse(test_data)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        total_time = sum(times)
        throughput = iterations / total_time
        
        return {
            'test': 'SMTP Parsing',
            'iterations': iterations,
            'total_time_s': total_time,
            'throughput_msg_per_sec': throughput,
            'mean_latency_us': mean(times) * 1_000_000,
            'median_latency_us': median(times) * 1_000_000,
            'p95_latency_us': sorted(times)[int(iterations * 0.95)] * 1_000_000,
            'p99_latency_us': sorted(times)[int(iterations * 0.99)] * 1_000_000,
            'stddev_latency_us': stdev(times) * 1_000_000 if len(times) > 1 else 0
        }
    
    def benchmark_dns_mutation(self, iterations: int = 5000) -> Dict[str, Any]:
        """Benchmark DNS mutation speed"""
        parser = DNSParser()
        mutator = DNSMutator()
        
        # Seed message
        msg = DNSMessage(
            transaction_id=0x5678,
            flags=0x0100,
            questions=[DNSQuestion('test.com', DNSType.A, DNSClass.IN)]
        )
        seed_data = parser.reconstruct(msg)
        
        # Warmup
        for _ in range(100):
            mutator.mutate(seed_data)
        
        # Benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            mutator.mutate(seed_data)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        total_time = sum(times)
        throughput = iterations / total_time
        
        return {
            'test': 'DNS Mutation',
            'iterations': iterations,
            'total_time_s': total_time,
            'throughput_mutations_per_sec': throughput,
            'mean_latency_us': mean(times) * 1_000_000,
            'median_latency_us': median(times) * 1_000_000,
            'p95_latency_us': sorted(times)[int(iterations * 0.95)] * 1_000_000,
            'p99_latency_us': sorted(times)[int(iterations * 0.99)] * 1_000_000,
            'stddev_latency_us': stdev(times) * 1_000_000 if len(times) > 1 else 0
        }
    
    def benchmark_smtp_mutation(self, iterations: int = 5000) -> Dict[str, Any]:
        """Benchmark SMTP mutation speed"""
        parser = SMTPParser()
        mutator = SMTPMutator()
        
        # Seed message
        msg = SMTPMessage()
        msg.commands = [SMTPCommandLine('MAIL', 'FROM:<user@example.com>')]
        seed_data = parser.reconstruct(msg)
        
        # Warmup
        for _ in range(100):
            mutator.mutate(seed_data)
        
        # Benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            mutator.mutate(seed_data)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        total_time = sum(times)
        throughput = iterations / total_time
        
        return {
            'test': 'SMTP Mutation',
            'iterations': iterations,
            'total_time_s': total_time,
            'throughput_mutations_per_sec': throughput,
            'mean_latency_us': mean(times) * 1_000_000,
            'median_latency_us': median(times) * 1_000_000,
            'p95_latency_us': sorted(times)[int(iterations * 0.95)] * 1_000_000,
            'p99_latency_us': sorted(times)[int(iterations * 0.99)] * 1_000_000,
            'stddev_latency_us': stdev(times) * 1_000_000 if len(times) > 1 else 0
        }
    
    def benchmark_dns_reconstruction(self, iterations: int = 10000) -> Dict[str, Any]:
        """Benchmark DNS message reconstruction"""
        parser = DNSParser()
        
        msg = DNSMessage(
            transaction_id=0xABCD,
            flags=0x8180,
            questions=[DNSQuestion('google.com', DNSType.A, DNSClass.IN)],
            answers=[DNSResourceRecord('google.com', DNSType.A, DNSClass.IN, 300, b'\x08\x08\x08\x08')]
        )
        
        # Warmup
        for _ in range(100):
            parser.reconstruct(msg)
        
        # Benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            parser.reconstruct(msg)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        total_time = sum(times)
        throughput = iterations / total_time
        
        return {
            'test': 'DNS Reconstruction',
            'iterations': iterations,
            'total_time_s': total_time,
            'throughput_msg_per_sec': throughput,
            'mean_latency_us': mean(times) * 1_000_000,
            'median_latency_us': median(times) * 1_000_000,
            'p95_latency_us': sorted(times)[int(iterations * 0.95)] * 1_000_000,
            'p99_latency_us': sorted(times)[int(iterations * 0.99)] * 1_000_000
        }
    
    def benchmark_smtp_reconstruction(self, iterations: int = 10000) -> Dict[str, Any]:
        """Benchmark SMTP message reconstruction"""
        parser = SMTPParser()
        
        msg = SMTPMessage()
        msg.responses = [SMTPResponse(250, 'OK', False)]
        
        # Warmup
        for _ in range(100):
            parser.reconstruct(msg)
        
        # Benchmark
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            parser.reconstruct(msg)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        total_time = sum(times)
        throughput = iterations / total_time
        
        return {
            'test': 'SMTP Reconstruction',
            'iterations': iterations,
            'total_time_s': total_time,
            'throughput_msg_per_sec': throughput,
            'mean_latency_us': mean(times) * 1_000_000,
            'median_latency_us': median(times) * 1_000_000,
            'p95_latency_us': sorted(times)[int(iterations * 0.95)] * 1_000_000,
            'p99_latency_us': sorted(times)[int(iterations * 0.99)] * 1_000_000
        }
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks and return results"""
        print("Running Protocol Performance Benchmarks...")
        print("=" * 60)
        
        results = []
        
        print("\n1. DNS Parsing...")
        results.append(self.benchmark_dns_parsing())
        
        print("2. SMTP Parsing...")
        results.append(self.benchmark_smtp_parsing())
        
        print("3. DNS Mutation...")
        results.append(self.benchmark_dns_mutation())
        
        print("4. SMTP Mutation...")
        results.append(self.benchmark_smtp_mutation())
        
        print("5. DNS Reconstruction...")
        results.append(self.benchmark_dns_reconstruction())
        
        print("6. SMTP Reconstruction...")
        results.append(self.benchmark_smtp_reconstruction())
        
        print("\n" + "=" * 60)
        print("Benchmarks Complete!")
        
        return {
            'benchmarks': results,
            'summary': self._generate_summary(results)
        }
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        return {
            'total_tests': len(results),
            'avg_throughput': mean([r.get('throughput_msg_per_sec', r.get('throughput_mutations_per_sec', 0)) for r in results]),
            'fastest_test': max(results, key=lambda r: r.get('throughput_msg_per_sec', r.get('throughput_mutations_per_sec', 0)))['test'],
            'slowest_test': min(results, key=lambda r: r.get('throughput_msg_per_sec', r.get('throughput_mutations_per_sec', 0)))['test']
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Print results in readable format"""
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("=" * 60)
        
        for benchmark in results['benchmarks']:
            print(f"\n{benchmark['test']}:")
            print(f"  Iterations:     {benchmark['iterations']:,}")
            print(f"  Total Time:     {benchmark['total_time_s']:.3f}s")
            
            if 'throughput_msg_per_sec' in benchmark:
                print(f"  Throughput:     {benchmark['throughput_msg_per_sec']:,.0f} msg/sec")
            else:
                print(f"  Throughput:     {benchmark['throughput_mutations_per_sec']:,.0f} mutations/sec")
            
            print(f"  Mean Latency:   {benchmark['mean_latency_us']:.2f} μs")
            print(f"  Median Latency: {benchmark['median_latency_us']:.2f} μs")
            print(f"  P95 Latency:    {benchmark['p95_latency_us']:.2f} μs")
            print(f"  P99 Latency:    {benchmark['p99_latency_us']:.2f} μs")
        
        print("\n" + "=" * 60)
        print("SUMMARY:")
        print(f"  Total Tests:    {results['summary']['total_tests']}")
        print(f"  Avg Throughput: {results['summary']['avg_throughput']:,.0f} ops/sec")
        print(f"  Fastest Test:   {results['summary']['fastest_test']}")
        print(f"  Slowest Test:   {results['summary']['slowest_test']}")
        print("=" * 60)
    
    def save_results(self, results: Dict[str, Any], filename: str = 'benchmark_results.json'):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {filename}")


if __name__ == '__main__':
    benchmark = ProtocolBenchmark()
    results = benchmark.run_all_benchmarks()
    benchmark.print_results(results)
    benchmark.save_results(results)
