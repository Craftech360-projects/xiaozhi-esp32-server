#!/usr/bin/env python3
"""
Performance Monitoring Script for Simple LiveKit Agent
Monitors system resources and agent performance in real-time
"""

import time
import logging
import json
import os
from datetime import datetime
from typing import Dict, List

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available - install with: pip install psutil")

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Real-time performance monitoring for LiveKit Agent"""
    
    def __init__(self, log_interval: int = 5, save_logs: bool = True):
        self.log_interval = log_interval
        self.save_logs = save_logs
        self.monitoring = False
        self.start_time = time.time()
        self.metrics_history: List[Dict] = []
        self.max_history = 720  # Keep 1 hour of 5-second intervals
        
        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 70.0,
            'cpu_critical': 85.0,
            'memory_warning': 80.0,
            'memory_critical': 90.0,
            'process_memory_warning': 500.0,  # MB
            'process_memory_critical': 1000.0,  # MB
        }
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if not PSUTIL_AVAILABLE:
            logger.error("❌ Cannot start monitoring - psutil not available")
            return False
        
        logger.info("🚀 Starting LiveKit Agent Performance Monitor")
        logger.info(f"📊 Monitoring interval: {self.log_interval} seconds")
        logger.info(f"💾 Save logs: {self.save_logs}")
        logger.info("=" * 60)
        
        self.monitoring = True
        
        try:
            while self.monitoring:
                metrics = self._collect_metrics()
                self._log_metrics(metrics)
                self._check_alerts(metrics)
                
                if self.save_logs:
                    self._save_metrics(metrics)
                
                time.sleep(self.log_interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
        finally:
            self.stop_monitoring()
        
        return True
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        
        if self.save_logs and self.metrics_history:
            self._save_summary()
        
        logger.info("✅ Performance monitoring stopped")
    
    def _collect_metrics(self) -> Dict:
        """Collect current system metrics"""
        if not PSUTIL_AVAILABLE:
            return {}
        
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net_io = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_cpu = process.cpu_percent()
            process_memory = process.memory_info()
            process_threads = process.num_threads()
            
            # Calculate uptime
            uptime = time.time() - self.start_time
            
            # Estimate client count (rough approximation based on threads)
            estimated_clients = max(0, (process_threads - 10) // 3)  # Rough estimate
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'uptime': uptime,
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / (1024**3),
                    'disk_percent': disk.percent,
                    'network_bytes_sent': net_io.bytes_sent,
                    'network_bytes_recv': net_io.bytes_recv,
                },
                'process': {
                    'cpu_percent': process_cpu,
                    'memory_mb': process_memory.rss / (1024**2),
                    'memory_vms_mb': process_memory.vms / (1024**2),
                    'threads': process_threads,
                    'estimated_clients': estimated_clients,
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to collect metrics: {e}")
            return {}
    
    def _log_metrics(self, metrics: Dict):
        """Log current metrics"""
        if not metrics:
            return
        
        sys_metrics = metrics['system']
        proc_metrics = metrics['process']
        
        logger.info(
            f"📊 METRICS | "
            f"Uptime: {metrics['uptime']:.0f}s | "
            f"Clients: ~{proc_metrics['estimated_clients']} | "
            f"CPU: {sys_metrics['cpu_percent']:.1f}% (proc: {proc_metrics['cpu_percent']:.1f}%) | "
            f"RAM: {sys_metrics['memory_percent']:.1f}% (proc: {proc_metrics['memory_mb']:.0f}MB) | "
            f"Threads: {proc_metrics['threads']} | "
            f"Net: ↓{sys_metrics['network_bytes_recv']/1024/1024:.1f}MB ↑{sys_metrics['network_bytes_sent']/1024/1024:.1f}MB"
        )
    
    def _check_alerts(self, metrics: Dict):
        """Check for performance alerts"""
        if not metrics:
            return
        
        sys_metrics = metrics['system']
        proc_metrics = metrics['process']
        
        # CPU alerts
        if sys_metrics['cpu_percent'] >= self.thresholds['cpu_critical']:
            logger.error(f"🚨 CRITICAL CPU: {sys_metrics['cpu_percent']:.1f}% - Immediate action required!")
        elif sys_metrics['cpu_percent'] >= self.thresholds['cpu_warning']:
            logger.warning(f"⚠️ HIGH CPU: {sys_metrics['cpu_percent']:.1f}% - Monitor closely")
        
        # Memory alerts
        if sys_metrics['memory_percent'] >= self.thresholds['memory_critical']:
            logger.error(f"🚨 CRITICAL MEMORY: {sys_metrics['memory_percent']:.1f}% - System may become unstable!")
        elif sys_metrics['memory_percent'] >= self.thresholds['memory_warning']:
            logger.warning(f"⚠️ HIGH MEMORY: {sys_metrics['memory_percent']:.1f}% - Consider cleanup")
        
        # Process memory alerts
        if proc_metrics['memory_mb'] >= self.thresholds['process_memory_critical']:
            logger.error(f"🚨 CRITICAL PROCESS MEMORY: {proc_metrics['memory_mb']:.0f}MB - Restart recommended!")
        elif proc_metrics['memory_mb'] >= self.thresholds['process_memory_warning']:
            logger.warning(f"⚠️ HIGH PROCESS MEMORY: {proc_metrics['memory_mb']:.0f}MB - Monitor for leaks")
        
        # Client overload alert
        if proc_metrics['estimated_clients'] > 6:
            logger.warning(f"⚠️ HIGH CLIENT COUNT: ~{proc_metrics['estimated_clients']} clients - Performance may degrade")
        
        # Performance correlation alerts
        if (proc_metrics['estimated_clients'] > 3 and 
            sys_metrics['cpu_percent'] > 60):
            logger.warning(f"⚠️ PERFORMANCE RISK: {proc_metrics['estimated_clients']} clients + {sys_metrics['cpu_percent']:.1f}% CPU")
    
    def _save_metrics(self, metrics: Dict):
        """Save metrics to history"""
        self.metrics_history.append(metrics)
        
        # Limit history size
        if len(self.metrics_history) > self.max_history:
            self.metrics_history.pop(0)
    
    def _save_summary(self):
        """Save performance summary to file"""
        try:
            summary_file = f"performance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Calculate summary statistics
            if self.metrics_history:
                cpu_values = [m['system']['cpu_percent'] for m in self.metrics_history]
                memory_values = [m['system']['memory_percent'] for m in self.metrics_history]
                process_memory_values = [m['process']['memory_mb'] for m in self.metrics_history]
                
                summary = {
                    'monitoring_duration': time.time() - self.start_time,
                    'total_samples': len(self.metrics_history),
                    'statistics': {
                        'cpu': {
                            'avg': sum(cpu_values) / len(cpu_values),
                            'max': max(cpu_values),
                            'min': min(cpu_values),
                        },
                        'memory': {
                            'avg': sum(memory_values) / len(memory_values),
                            'max': max(memory_values),
                            'min': min(memory_values),
                        },
                        'process_memory': {
                            'avg': sum(process_memory_values) / len(process_memory_values),
                            'max': max(process_memory_values),
                            'min': min(process_memory_values),
                        }
                    },
                    'raw_data': self.metrics_history
                }
                
                with open(summary_file, 'w') as f:
                    json.dump(summary, f, indent=2)
                
                logger.info(f"💾 Performance summary saved to: {summary_file}")
                logger.info(f"📈 Average CPU: {summary['statistics']['cpu']['avg']:.1f}%")
                logger.info(f"📈 Average Memory: {summary['statistics']['memory']['avg']:.1f}%")
                logger.info(f"📈 Average Process Memory: {summary['statistics']['process_memory']['avg']:.1f}MB")
        
        except Exception as e:
            logger.error(f"❌ Failed to save summary: {e}")
    
    def get_current_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            'monitoring': self.monitoring,
            'uptime': time.time() - self.start_time,
            'samples_collected': len(self.metrics_history),
            'thresholds': self.thresholds
        }

def main():
    """Main monitoring function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LiveKit Agent Performance Monitor')
    parser.add_argument('--interval', type=int, default=5, help='Monitoring interval in seconds (default: 5)')
    parser.add_argument('--no-save', action='store_true', help='Disable saving logs to file')
    parser.add_argument('--cpu-warning', type=float, default=70.0, help='CPU warning threshold (default: 70%%)')
    parser.add_argument('--memory-warning', type=float, default=80.0, help='Memory warning threshold (default: 80%%)')
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = PerformanceMonitor(
        log_interval=args.interval,
        save_logs=not args.no_save
    )
    
    # Update thresholds if provided
    if args.cpu_warning:
        monitor.thresholds['cpu_warning'] = args.cpu_warning
    if args.memory_warning:
        monitor.thresholds['memory_warning'] = args.memory_warning
    
    # Start monitoring
    monitor.start_monitoring()

if __name__ == "__main__":
    main()