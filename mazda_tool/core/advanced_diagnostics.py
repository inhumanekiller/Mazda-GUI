# mazda_tool/core/advanced_diagnostics.py
class MazdaAdvancedDiagnostics:
    """
    Professional-grade diagnostic system for Mazdaspeed 3
    """
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        
        # Mazdaspeed-specific diagnostic patterns
        self.known_issues = self._load_known_issues()
        self.component_health_scores = {}
        self.maintenance_schedule = {}

    def _load_known_issues(self):
        """Load Mazdaspeed 3 common problem patterns"""
        return {
            'hpfp_failure': {
                'symptoms': ['fuel_pressure_high < 1500', 'lean_afr_under_boost', 'power_loss_high_rpm'],
                'severity': 'critical',
                'repair_urgency': 'immediate',
                'diagnostic_procedure': 'HPFP_flow_test'
            },
            'carbon_buildup': {
                'symptoms': ['rough_idle_cold', 'misfire_cylinder_2_3', 'reduced_mpg', 'hesitation_low_rpm'],
                'severity': 'high', 
                'repair_urgency': '2_weeks',
                'diagnostic_procedure': 'compression_test_visual_inspection'
            },
            'wastegate_stick': {
                'symptoms': ['boost_oscillation > 2psi', 'overboost_faults', 'slow_spool_time'],
                'severity': 'medium',
                'repair_urgency': '1_month',
                'diagnostic_procedure': 'wastegate_actuator_test'
            },
            'vvt_issues': {
                'symptoms': ['rattle_cold_start', 'power_loss_midrange', 'vvt_codes'],
                'severity': 'high',
                'repair_urgency': '1_week', 
                'diagnostic_procedure': 'vvt_solenoid_test_timing_analysis'
            }
        }

    def run_comprehensive_diagnostic(self):
        """Execute full vehicle health assessment"""
        diagnostic_results = {
            'timestamp': time.time(),
            'overall_health_score': 0,
            'system_reports': {},
            'identified_issues': [],
            'maintenance_recommendations': [],
            'component_health_scores': {}
        }
        
        # Analyze each major system
        diagnostic_results['system_reports']['engine'] = self._analyze_engine_health()
        diagnostic_results['system_reports']['turbo'] = self._analyze_turbo_health()
        diagnostic_results['system_reports']['fuel_system'] = self._analyze_fuel_system_health()
        diagnostic_results['system_reports']['ignition'] = self._analyze_ignition_health()
        diagnostic_results['system_reports']['emissions'] = self._analyze_emissions_health()
        
        # Identify issues based on symptom patterns
        diagnostic_results['identified_issues'] = self._identify_issues_from_patterns()
        
        # Calculate overall health score
        diagnostic_results['overall_health_score'] = self._calculate_overall_health(
            diagnostic_results['system_reports']
        )
        
        # Generate maintenance recommendations
        diagnostic_results['maintenance_recommendations'] = self._generate_maintenance_schedule(
            diagnostic_results['system_reports']
        )
        
        return diagnostic_results

    def _analyze_turbo_health(self):
        """Comprehensive K04 turbocharger health analysis"""
        turbo_data = {
            'health_score': 100,
            'findings': [],
            'recommendations': [],
            'metrics': {}
        }
        
        # Analyze boost response characteristics
        boost_samples = [d.get('boost_pressure', 0) for d in list(self.data_manager.live_data_buffer)[-100:]]
        
        if boost_samples:
            # Calculate spool time (RPM to target boost)
            spool_time = self._calculate_turbo_spool_time()
            turbo_data['metrics']['spool_time_seconds'] = spool_time
            
            # K04 should spool 15+ PSI by 3000 RPM in healthy condition
            if spool_time > 3.5:
                turbo_data['health_score'] -= 20
                turbo_data['findings'].append(f"Slow spool time: {spool_time:.1f}s (expected < 3.0s)")
                turbo_data['recommendations'].append("Check for boost leaks, wastegate operation")
                
            # Check boost stability
            boost_stability = np.std(boost_samples)
            turbo_data['metrics']['boost_stability_psi'] = boost_stability
            
            if boost_stability > 1.5:
                turbo_data['health_score'] -= 15
                turbo_data['findings'].append(f"Boost instability: {boost_stability:.2f} PSI variance")
                turbo_data['recommendations'].append("Inspect wastegate diaphragm and control solenoid")
                
            # Check for overboost conditions
            max_boost = max(boost_samples)
            turbo_data['metrics']['max_boost_psi'] = max_boost
            
            if max_boost > 25.0:
                turbo_data['health_score'] -= 25
                turbo_data['findings'].append(f"Dangerous overboost: {max_boost:.1f} PSI")
                turbo_data['recommendations'].append("Immediate wastegate and boost control inspection required")
                
        return turbo_data

    def _analyze_fuel_system_health(self):
        """HPFP and direct injection system health analysis"""
        fuel_data = {
            'health_score': 100,
            'findings': [],
            'recommendations': [],
            'metrics': {}
        }
        
        # Analyze HPFP pressure characteristics
        hpfp_samples = [d.get('fuel_pressure_high', 0) for d in list(self.data_manager.live_data_buffer)[-50:]]
        
        if hpfp_samples:
            avg_hpfp = np.mean(hpfp_samples)
            min_hpfp = min(hpfp_samples)
            
            fuel_data['metrics']['average_hpfp_pressure_psi'] = avg_hpfp
            fuel_data['metrics']['minimum_hpfp_pressure_psi'] = min_hpfp
            
            # Critical HPFP pressure checks
            if min_hpfp < 1400:
                fuel_data['health_score'] -= 40
                fuel_data['findings'].append(f"CRITICAL: HPFP pressure dropped to {min_hpfp:.0f} PSI")
                fuel_data['recommendations'].append("IMMEDIATE HPFP inspection/replacement required")
            elif avg_hpfp < 1600:
                fuel_data['health_score'] -= 20
                fuel_data['findings'].append(f"Low average HPFP pressure: {avg_hpfp:.0f} PSI")
                fuel_data['recommendations'].append("Monitor HPFP performance, consider preventative replacement")
                
        # Analyze fuel trims for injector health
        if 'long_term_fuel_trim' in self.data_manager.live_data_buffer[-1]:
            fuel_trim = self.data_manager.live_data_buffer[-1]['long_term_fuel_trim']
            fuel_data['metrics']['long_term_fuel_trim_percent'] = fuel_trim
            
            if abs(fuel_trim) > 10:
                fuel_data['health_score'] -= 15
                fuel_data['findings'].append(f"Excessive fuel trim: {fuel_trim:.1f}%")
                fuel_data['recommendations'].append("Check for intake leaks, injector performance, MAF sensor")
                
        return fuel_data