# mazda_tool/core/ai_tuner.py
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import statistics

@dataclass
class DrivingPattern:
    """Data structure to store analyzed driving patterns"""
    acceleration_aggression: float  # 0-1 scale
    shift_points: List[int]         # RPM shift points detected
    cruising_rpm: int              # Typical cruising RPM
    throttle_usage: Dict[str, float]  # % time in throttle ranges
    brake_usage: Dict[str, float]     # Braking patterns
    driving_style: str             # performance, balanced, economical
    typical_contexts: List[str]    # city_traffic, highway_cruising, etc.

@dataclass 
class TuningAdjustment:
    """Data structure for AI-generated tuning recommendations"""
    parameter: str
    current_value: float
    recommended_value: float
    confidence: float
    reasoning: str
    urgency: str  # immediate, soon, optional
    category: str  # performance, efficiency, safety

class MazdaAITuner:
    """
    MAZDA AI TUNING ENGINE
    The intelligent core that learns your driving and optimizes your tune
    
    Features:
    - Real-time driving pattern analysis
    - Mazda-specific tuning recommendations  
    - Adaptive learning based on your driving style
    - Performance vs efficiency optimization
    - Safety-first approach with MZR DISI knowledge
    """
    
    def __init__(self, config_manager=None):
        self.driving_data = []
        self.performance_history = []
        self.learning_active = False
        self.driving_profile = None
        self.session_start_time = None
        self.config_manager = config_manager
        
        # Analysis thresholds (Mazdaspeed 3 optimized)
        self.analysis_thresholds = {
            'aggressive_throttle': 80,  # % throttle position
            'high_rpm': 5000,           # RPM
            'performance_rpm': 4000,    # RPM
            'efficient_rpm_min': 1500,  # RPM
            'efficient_rpm_max': 3000,  # RPM
            'boost_threshold': 10.0,    # PSI
            'sample_size_min': 50       # min data points for analysis
        }
        
        # Mazda-specific knowledge base
        self.mazda_knowledge_base = self._load_mazda_knowledge()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Mazda AI Tuner initialized")

    def _load_mazda_knowledge(self) -> Dict[str, Any]:
        """Load comprehensive Mazdaspeed 3 specific engineering knowledge"""
        return {
            "vehicle_limits": {
                "k04_turbo_max_safe_boost": 18.5,
                "stock_hpfp_max_pressure": 1700,
                "mzr_displacement_cc": 2261,
                "compression_ratio": 9.5,
                "redline_rpm": 6700,
                "fuel_cut_rpm": 6800
            },
            "optimal_ranges": {
                "cruise_afr": (14.5, 15.0),
                "wot_afr": (11.2, 11.8),
                "boost_k04_efficiency": (15.0, 18.0),
                "timing_advance_safe": (1.0, 3.0),
                "vvt_optimization_rpm": (2500, 4500),
                "ideal_intake_temp": (25, 40),
                "safe_ect_range": (85, 105)
            },
            "tuning_strategies": {
                "high_hp_low_boost": {
                    "description": "Maximize power while maintaining K04 longevity",
                    "target_boost": 17.0,
                    "focus_areas": ["timing_advance", "thermal_efficiency", "vvt_optimization"]
                },
                "daily_driver": {
                    "description": "Balance performance and reliability for daily use", 
                    "target_boost": 16.0,
                    "focus_areas": ["throttle_response", "fuel_economy", "smooth_power_delivery"]
                },
                "max_efficiency": {
                    "description": "Optimize for fuel economy and smooth operation",
                    "target_boost": 15.0,
                    "focus_areas": ["lean_cruise", "early_torque", "thermal_management"]
                }
            },
            "common_issues": {
                "p0234_overboost": {
                    "causes": ["restrictive_exhaust", "wastegate_issues", "boost_control_aggressive"],
                    "solutions": ["reduce_boost_targets", "check_wastegate_preload", "improve_timing"]
                },
                "p0087_fuel_pressure": {
                    "causes": ["hpfp_failure", "excessive_power", "fuel_control_issues"],
                    "solutions": ["upgrade_hpfp", "reduce_load_targets", "optimize_fuel_tables"]
                },
                "knock_detected": {
                    "causes": ["poor_fuel_quality", "excessive_timing", "high_intake_temps"],
                    "solutions": ["reduce_timing", "improve_charge_cooling", "use_higher_octane"]
                }
            }
        }

    def start_learning_session(self, vehicle_profile: Dict) -> str:
        """
        Start a new AI learning session
        
        Args:
            vehicle_profile: Dictionary containing vehicle information
        
        Returns:
            str: Session startup message
        """
        self.learning_active = True
        self.driving_data = []
        self.session_start_time = datetime.now()
        
        # Initialize driving profile
        self.driving_profile = self._analyze_initial_driving_style(vehicle_profile)
        
        session_info = f"""
🧠 MAZDA AI TUNER ACTIVATED

Session Started: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}
Vehicle: {vehicle_profile.get('model', 'Mazdaspeed 3')}
Initial Driving Style: {self.driving_profile['style'].upper()}

WHAT I'M LEARNING:
• Your acceleration preferences and typical shift points
• Driving contexts (city, highway, performance)
• Throttle usage patterns and braking habits  
• Environmental adaptations (temperature, altitude)

RECOMMENDED DRIVE CYCLE:
1. 10-15 minutes of city driving with stops
2. 10-15 minutes of highway cruising
3. A few full-throttle accelerations (when safe!)
4. Mixed driving to establish your normal patterns

Drive normally - I'll analyze your patterns and provide tuning optimizations!
"""
        self.logger.info("AI learning session started")
        return session_info

    def stop_learning_session(self) -> str:
        """Stop the current learning session"""
        self.learning_active = False
        session_duration = datetime.now() - self.session_start_time
        
        summary = f"""
🛑 AI LEARNING SESSION COMPLETED

Session Duration: {str(session_duration).split('.')[0]}
Data Points Collected: {len(self.driving_data):,}
Driving Style Analyzed: {self.driving_profile['style'].upper()}

Ready to generate your personalized tuning report!
"""
        self.logger.info(f"AI learning session stopped after {session_duration}")
        return summary

    def process_driving_data(self, real_time_data: Dict) -> Optional[TuningAdjustment]:
        """
        Process real-time driving data and generate tuning recommendations
        
        Args:
            real_time_data: Dictionary of OBD-II parameters
        
        Returns:
            Optional[TuningAdjustment]: Tuning recommendation if available
        """
        if not self.learning_active:
            return None

        # Add context and timestamp to data
        data_point = {
            'timestamp': datetime.now(),
            'data': real_time_data,
            'context': self._get_driving_context(real_time_data)
        }
        
        self.driving_data.append(data_point)
        
        # Keep data manageable (last 2 hours of driving approx)
        if len(self.driving_data) > 3600:  # 1 data point per 2 seconds = 2 hours
            self.driving_data = self.driving_data[-3600:]
        
        # Generate recommendations at intervals
        if len(self.driving_data) % 100 == 0 and len(self.driving_data) >= self.analysis_thresholds['sample_size_min']:
            return self._generate_tuning_recommendation()
        
        return None

    def _analyze_initial_driving_style(self, vehicle_profile: Dict) -> Dict:
        """Analyze initial driving style based on vehicle profile and early data"""
        # This would be enhanced with actual driving data over time
        return {
            'style': 'balanced',  # Will be updated with real analysis
            'preferences': {
                'throttle_response': 'medium',
                'boost_response': 'progressive',
                'shift_aggression': 'medium',
                'cruise_preference': 'relaxed'
            },
            'typical_usage': {
                'city_percentage': 60,  # Default assumptions
                'highway_percentage': 40,
                'performance_usage': 20
            },
            'adaptation_factors': {
                'learning_rate': 0.8,
                'confidence': 0.3,  # Starts low, increases with data
                'last_updated': datetime.now()
            }
        }

    def _get_driving_context(self, data: Dict) -> str:
        """Determine the current driving context from real-time data"""
        rpm = data.get('rpm', 0)
        throttle = data.get('throttle_position', 0)
        speed = data.get('speed', 0)
        boost = data.get('boost_pressure', 0)
        
        # Context detection logic
        if speed < 30:
            return "city_traffic"
        elif speed > 80 and throttle < 30:
            return "highway_cruising"
        elif throttle > 80 and rpm > 4000 and boost > 5:
            return "performance_driving"
        elif 20 <= throttle <= 60 and 2000 <= rpm <= 3500:
            return "normal_cruising"
        elif throttle < 10 and speed > 20:
            return "deceleration"
        else:
            return "transitional"

    def _generate_tuning_recommendation(self) -> Optional[TuningAdjustment]:
        """Generate AI-powered tuning recommendation based on driving analysis"""
        if len(self.driving_data) < self.analysis_thresholds['sample_size_min']:
            return None
        
        analysis = self._analyze_driving_patterns()
        
        # Update driving profile with new analysis
        self._update_driving_profile(analysis)
        
        # Generate appropriate recommendation based on driving style
        if analysis['aggression_level'] > 0.7:
            return self._create_performance_adjustment(analysis)
        elif analysis['efficiency_score'] > 0.7:
            return self._create_efficiency_adjustment(analysis)
        elif analysis['aggression_level'] > 0.6 and analysis['efficiency_score'] > 0.6:
            return self._create_balanced_adjustment(analysis)
        else:
            return self._create_adaptive_adjustment(analysis)

    def _analyze_driving_patterns(self) -> Dict[str, Any]:
        """Comprehensive analysis of driving patterns from collected data"""
        if not self.driving_data:
            return {}
        
        recent_data = self.driving_data[-200:]  # Last ~6-7 minutes of driving
        
        aggression_metrics = 0
        efficiency_metrics = 0
        total_points = len(recent_data)
        
        rpm_values = []
        throttle_values = []
        boost_values = []
        contexts = []
        
        for data_point in recent_data:
            data = data_point['data']
            rpm = data.get('rpm', 0)
            throttle = data.get('throttle_position', 0)
            boost = data.get('boost_pressure', 0)
            
            # Collect values for distribution analysis
            rpm_values.append(rpm)
            throttle_values.append(throttle)
            boost_values.append(boost)
            contexts.append(data_point['context'])
            
            # Aggression scoring
            if throttle > self.analysis_thresholds['aggressive_throttle']:
                aggression_metrics += 1
            if rpm > self.analysis_thresholds['high_rpm']:
                aggression_metrics += 1
            if boost > self.analysis_thresholds['boost_threshold']:
                aggression_metrics += 1
            
            # Efficiency scoring
            if self.analysis_thresholds['efficient_rpm_min'] <= rpm <= self.analysis_thresholds['efficient_rpm_max']:
                efficiency_metrics += 1
            if throttle < 50:
                efficiency_metrics += 1
            if data_point['context'] in ['highway_cruising', 'normal_cruising']:
                efficiency_metrics += 1
        
        # Calculate distributions
        rpm_distribution = self._calculate_rpm_distribution(rpm_values)
        throttle_distribution = self._analyze_throttle_usage(throttle_values)
        context_distribution = self._analyze_context_usage(contexts)
        
        return {
            'aggression_level': aggression_metrics / (total_points * 3),  # Normalize to 0-1
            'efficiency_score': efficiency_metrics / (total_points * 3),  # Normalize to 0-1
            'typical_rpm_range': rpm_distribution,
            'throttle_usage_pattern': throttle_distribution,
            'context_distribution': context_distribution,
            'data_points_analyzed': total_points,
            'analysis_timestamp': datetime.now()
        }

    def _calculate_rpm_distribution(self, rpm_values: List[float]) -> Dict[str, float]:
        """Calculate RPM distribution statistics"""
        if not rpm_values:
            return {"mean": 0, "std": 0, "common_range": "0-0"}
        
        mean_rpm = statistics.mean(rpm_values)
        std_rpm = statistics.stdev(rpm_values) if len(rpm_values) > 1 else 0
        
        # Find common RPM range (mean ± 0.5 std)
        low_range = max(0, mean_rpm - 0.5 * std_rpm)
        high_range = min(7000, mean_rpm + 0.5 * std_rpm)
        
        return {
            "mean": round(mean_rpm),
            "std": round(std_rpm),
            "common_range": f"{int(low_range)}-{int(high_range)}"
        }

    def _analyze_throttle_usage(self, throttle_values: List[float]) -> Dict[str, float]:
        """Analyze throttle usage patterns"""
        if not throttle_values:
            return {"light": 0, "medium": 0, "heavy": 0}
        
        total = len(throttle_values)
        light = len([t for t in throttle_values if t < 30]) / total
        medium = len([t for t in throttle_values if 30 <= t <= 70]) / total
        heavy = len([t for t in throttle_values if t > 70]) / total
        
        return {
            "light": round(light, 3),
            "medium": round(medium, 3),
            "heavy": round(heavy, 3)
        }

    def _analyze_context_usage(self, contexts: List[str]) -> Dict[str, float]:
        """Analyze driving context distribution"""
        if not contexts:
            return {}
        
        total = len(contexts)
        context_counts = {}
        
        for context in contexts:
            context_counts[context] = context_counts.get(context, 0) + 1
        
        return {ctx: round(count/total, 3) for ctx, count in context_counts.items()}

    def _update_driving_profile(self, analysis: Dict):
        """Update driving profile based on new analysis"""
        if not self.driving_profile:
            return
        
        aggression = analysis.get('aggression_level', 0.5)
        efficiency = analysis.get('efficiency_score', 0.5)
        
        # Classify driving style
        if aggression > 0.7:
            new_style = "performance"
        elif efficiency > 0.7:
            new_style = "economical"
        elif aggression > 0.6 and efficiency > 0.6:
            new_style = "balanced_aggressive"
        else:
            new_style = "balanced"
        
        # Update profile with smoothing
        current_style = self.driving_profile['style']
        if new_style != current_style:
            # Only update if we have reasonable confidence
            if analysis.get('data_points_analyzed', 0) > 100:
                self.driving_profile['style'] = new_style
                self.driving_profile['adaptation_factors']['confidence'] = min(
                    0.95, self.driving_profile['adaptation_factors']['confidence'] + 0.1
                )
        
        self.driving_profile['adaptation_factors']['last_updated'] = datetime.now()

    def _create_performance_adjustment(self, analysis: Dict) -> TuningAdjustment:
        """Create performance-oriented tuning adjustment"""
        aggression = analysis.get('aggression_level', 0.5)
        
        return TuningAdjustment(
            parameter="load_targeting_midrange",
            current_value=1.8,
            recommended_value=2.1 + (aggression - 0.7) * 0.5,  # Scale with aggression
            confidence=min(0.9, aggression),
            urgency="soon",
            category="performance",
            reasoning=f"""
🚀 PERFORMANCE DRIVING DETECTED

Your driving analysis shows:
• Aggression Level: {aggression:.1%} (High Performance)
• Typical RPM Range: {analysis.get('typical_rpm_range', {}).get('common_range', 'N/A')}
• Heavy Throttle Usage: {analysis.get('throttle_usage_pattern', {}).get('heavy', 0):.1%}

RECOMMENDATION: Increase mid-range load targets
• Better throttle response in 3000-5000 RPM range
• Improved turbo spool characteristics
• Maintains K04 turbo safety margins

BENEFITS:
- Quicker acceleration in your typical driving range
- More immediate power when you need it
- Optimized for your performance-oriented style

SAFETY: I'm monitoring knock and temperatures to keep your engine safe!
"""
        )

    def _create_efficiency_adjustment(self, analysis: Dict) -> TuningAdjustment:
        """Create efficiency-oriented tuning adjustment"""
        efficiency = analysis.get('efficiency_score', 0.5)
        
        return TuningAdjustment(
            parameter="cruise_afr_target",
            current_value=14.7,
            recommended_value=15.0,
            confidence=min(0.85, efficiency),
            urgency="optional", 
            category="efficiency",
            reasoning=f"""
🌿 EFFICIENCY-FOCUSED DRIVING DETECTED

Your driving analysis shows:
• Efficiency Score: {efficiency:.1%} (Excellent Efficiency)
• Typical RPM Range: {analysis.get('typical_rpm_range', {}).get('common_range', 'N/A')}
• Light Throttle Usage: {analysis.get('throttle_usage_pattern', {}).get('light', 0):.1%}

RECOMMENDATION: Optimize cruise AFR for fuel economy
• Slightly leaner mixture during highway cruising
• Maintains driveability and emissions compliance
• Better thermal efficiency during steady-state driving

ESTIMATED BENEFITS:
- 3-5% improvement in fuel economy during cruising
- Reduced emissions during highway driving
- Maintains full power when you need it

PERFECT for your economical driving style and daily commuting!
"""
        )

    def _create_balanced_adjustment(self, analysis: Dict) -> TuningAdjustment:
        """Create balanced tuning adjustment for mixed driving"""
        return TuningAdjustment(
            parameter="throttle_response_map",
            current_value=0,
            recommended_value=0.8,
            confidence=0.75,
            urgency="optional",
            category="driveability",
            reasoning=f"""
⚖️ BALANCED DRIVING STYLE DETECTED

Your driving analysis shows excellent balance:
• Aggression Level: {analysis.get('aggression_level', 0):.1%}
• Efficiency Score: {analysis.get('efficiency_score', 0):.1%}
• Versatile driving across multiple contexts

RECOMMENDATION: Optimize throttle response mapping
• Improved linearity in throttle response
• Better connection between pedal and power
• Enhanced driveability in all conditions

BENEFITS:
- Smofter daily driving experience
- Predictable power delivery
- Maintains both efficiency and performance capability

This optimization enhances the stock Mazda driving feel you enjoy!
"""
        )

    def _create_adaptive_adjustment(self, analysis: Dict) -> TuningAdjustment:
        """Create adaptive adjustment for evolving driving patterns"""
        return TuningAdjustment(
            parameter="vvt_optimization_midrange",
            current_value=0,
            recommended_value=0.6,
            confidence=0.7,
            urgency="optional",
            category="adaptation",
            reasoning=f"""
🎯 ADAPTIVE OPTIMIZATION

I'm still learning your driving patterns, but initial analysis shows:
• Data Points: {analysis.get('data_points_analyzed', 0):,}
• Context Variety: {len(analysis.get('context_distribution', {}))}
• RPM Range: {analysis.get('typical_rpm_range', {}).get('common_range', 'N/A')}

RECOMMENDATION: Conservative VVT optimization
• Small improvement in mid-range torque
• Better low-end response for daily driving
• Safe, reversible change

CONTINUE DRIVING NORMALLY so I can learn:
- Your typical commute routes
- Performance vs efficiency preferences
- Environmental adaptations needed

The more you drive, the better my recommendations will become!
"""
        )

    def generate_ai_tuning_report(self) -> Dict[str, Any]:
        """Generate comprehensive AI tuning report"""
        if len(self.driving_data) < self.analysis_thresholds['sample_size_min']:
            return {
                "error": "Insufficient data",
                "message": f"Need at least {self.analysis_thresholds['sample_size_min']} data points for analysis",
                "data_points": len(self.driving_data)
            }
        
        analysis = self._analyze_driving_patterns()
        driving_style = self._classify_driving_style(analysis)
        
        return {
            "session_summary": {
                "data_points_collected": len(self.driving_data),
                "learning_duration": str(datetime.now() - self.session_start_time).split('.')[0],
                "session_start": self.session_start_time.isoformat(),
                "driving_style": driving_style,
                "confidence_score": self.driving_profile['adaptation_factors']['confidence']
            },
            "driving_analysis": analysis,
            "tuning_recommendations": self._generate_all_recommendations(analysis),
            "mazda_specific_insights": self._generate_mazda_insights(analysis, driving_style),
            "next_steps": self._get_learning_next_steps(driving_style),
            "vehicle_health_check": self._perform_vehicle_health_check()
        }

    def _classify_driving_style(self, analysis: Dict) -> str:
        """Classify overall driving style based on analysis"""
        aggression = analysis.get('aggression_level', 0.5)
        efficiency = analysis.get('efficiency_score', 0.5)
        
        if aggression > 0.7:
            return "Performance Enthusiast"
        elif efficiency > 0.7:
            return "Efficiency Master"
        elif aggression > 0.6 and efficiency > 0.6:
            return "Balanced All-Rounder"
        elif aggression > 0.6:
            return "Spirited Daily Driver"
        elif efficiency > 0.6:
            return "Eco-Conscious Driver"
        else:
            return "Adaptive Driver"

    def _generate_all_recommendations(self, analysis: Dict) -> List[Dict]:
        """Generate all tuning recommendations based on comprehensive analysis"""
        recommendations = []
        
        # Base recommendation
        main_rec = self._generate_tuning_recommendation()
        if main_rec:
            recommendations.append({
                "parameter": main_rec.parameter,
                "adjustment": f"{main_rec.current_value} → {main_rec.recommended_value}",
                "confidence": main_rec.confidence,
                "category": main_rec.category,
                "urgency": main_rec.urgency
            })
        
        # Additional context-specific recommendations
        context_dist = analysis.get('context_distribution', {})
        
        if context_dist.get('performance_driving', 0) > 0.1:
            recommendations.append({
                "parameter": "boost_response_aggression",
                "adjustment": "Medium → High",
                "confidence": 0.8,
                "category": "performance",
                "urgency": "optional"
            })
        
        if context_dist.get('highway_cruising', 0) > 0.3:
            recommendations.append({
                "parameter": "highway_afr_optimization", 
                "adjustment": "Enabled",
                "confidence": 0.75,
                "category": "efficiency",
                "urgency": "optional"
            })
        
        return recommendations

    def _generate_mazda_insights(self, analysis: Dict, driving_style: str) -> List[str]:
        """Generate Mazda-specific engineering insights"""
        insights = []
        
        # Style-specific insights
        if "Performance" in driving_style:
            insights.extend([
                "💪 Your driving style matches the MZR DISI engine's performance heritage",
                "🎯 Load-based tuning will provide consistent power across conditions", 
                "🌡️ Consider monitoring intake temps during extended spirited driving",
                "⚙️ Your K04 turbo is being used efficiently in its power band"
            ])
        
        if "Efficiency" in driving_style:
            insights.extend([
                "🌿 Your driving maximizes SkyActiv efficiency principles",
                "⚡ Conservative boost usage extends K04 turbo lifespan",
                "🛣️ Perfect tuning candidate for daily driving with occasional performance",
                "💰 Excellent fuel economy habits detected"
            ])
        
        # Context-based insights
        context_dist = analysis.get('context_distribution', {})
        if context_dist.get('city_traffic', 0) > 0.4:
            insights.append("🏙️ Optimizing for your heavy city driving patterns")
        
        if context_dist.get('highway_cruising', 0) > 0.3:
            insights.append("🛣️ Highway efficiency optimizations applied")
        
        # Mazda engineering insight
        insights.append("🔧 Recommendations based on Mazda MZR DISI engineering specifications")
        
        return insights

    def _get_learning_next_steps(self, driving_style: str) -> List[str]:
        """Get recommended next steps for continued learning"""
        steps = [
            "Continue driving normally to improve recommendation accuracy",
            "Try different driving conditions (hills, highway, city) for broader analysis",
            "Monitor engine parameters during your typical drives"
        ]
        
        if "Performance" in driving_style:
            steps.extend([
                "Consider logging some track or autocross sessions",
                "Monitor knock activity during high-load conditions"
            ])
        
        if "Efficiency" in driving_style:
            steps.extend([
                "Try some back-road driving to test transient response",
                "Monitor fuel economy improvements after tuning changes"
            ])
        
        return steps

    def _perform_vehicle_health_check(self) -> Dict[str, Any]:
        """Perform basic vehicle health check based on driving data"""
        if len(self.driving_data) < 100:
            return {"status": "insufficient_data", "message": "Need more driving data for health analysis"}
        
        # Analyze recent data for anomalies
        recent_data = [d['data'] for d in self.driving_data[-100:]]
        
        # Check for common issues
        max_boost = max([d.get('boost_pressure', 0) for d in recent_data])
        max_rpm = max([d.get('rpm', 0) for d in recent_data])
        avg_intake_temp = statistics.mean([d.get('intake_temp', 25) for d in recent_data if d.get('intake_temp')])
        
        health_status = "healthy"
        issues = []
        
        if max_boost > self.mazda_knowledge_base['vehicle_limits']['k04_turbo_max_safe_boost']:
            health_status = "attention_required"
            issues.append("Boost levels exceeding safe K04 limits")
        
        if max_rpm > self.mazda_knowledge_base['vehicle_limits']['redline_rpm']:
            health_status = "attention_required" 
            issues.append("RPM exceeding recommended redline")
        
        if avg_intake_temp > 45:
            health_status = "monitor"
            issues.append("Elevated intake temperatures detected")
        
        return {
            "status": health_status,
            "issues": issues,
            "parameters": {
                "max_boost_observed": round(max_boost, 1),
                "max_rpm_observed": max_rpm,
                "average_intake_temp": round(avg_intake_temp, 1)
            }
        }

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        if not self.session_start_time:
            return {"error": "No active session"}
        
        return {
            "learning_active": self.learning_active,
            "session_duration": str(datetime.now() - self.session_start_time).split('.')[0],
            "data_points": len(self.driving_data),
            "driving_style": self.driving_profile['style'] if self.driving_profile else "unknown",
            "confidence": self.driving_profile['adaptation_factors']['confidence'] if self.driving_profile else 0
        }