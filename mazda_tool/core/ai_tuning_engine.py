# mazda_tool/core/ai_tuning_engine.py
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
import joblib
import json

class MazdaAITuner:
    """
    Adaptive machine learning system for Mazdaspeed 3 performance optimization
    """
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        
        # Mazda-specific knowledge base
        self.mazda_knowledge = self._load_mazda_knowledge_base()
        
        # Machine Learning Models
        self.driving_style_model = None
        self.performance_model = None  
        self.safety_model = None
        
        # Training state
        self.training_data = []
        self.current_driving_profile = None
        self.performance_goals = {}
        
        self._initialize_models()

    def _load_mazda_knowledge_base(self):
        """Load Mazdaspeed 3 specific engineering knowledge"""
        return {
            "mzr_disi_2.3L_turbo": {
                "engine_characteristics": {
                    "redline": 6700,
                    "fuel_system": "Direct Injection + HPFP",
                    "turbo": "K04 with internal wastegate",
                    "vvt_system": "Dual VVT on intake and exhaust",
                    "compression_ratio": 9.5,
                    "displacement_cc": 2261
                },
                "performance_limits": {
                    "safe_boost_kpa": 240,      # ~22 PSI
                    "max_injector_duty": 85,    # %
                    "hpfp_pressure_min": 1400,  # PSI
                    "egt_safe_max": 850,        # °C
                    "timing_advance_range": (-5, 25)  # Degrees
                },
                "common_issues": {
                    "carbon_buildup": "Cylinders 2 & 3 typical",
                    "hpfp_failure": "Monitor pressure below 1500 PSI",
                    "wastegate_stick": "Boost oscillation > 2 PSI",
                    "vvt_issues": "Rattle on cold start, performance loss"
                }
            },
            "tuning_strategies": {
                "high_hp_low_boost": {
                    "description": "Efficient power within K04 compressor limits",
                    "target_afr": 11.5,
                    "boost_curve": "Progressive to 20 PSI by 3500 RPM",
                    "timing_strategy": "Aggressive mid-range, conservative top-end"
                },
                "daily_driver": {
                    "description": "Balance of performance and reliability", 
                    "target_afr": 12.0,
                    "boost_curve": "Linear to 18 PSI by 4000 RPM",
                    "timing_strategy": "Moderate throughout range"
                },
                "track_optimized": {
                    "description": "Maximum performance with safety margins",
                    "target_afr": 11.2,
                    "boost_curve": "Quick spool to 22 PSI by 3000 RPM",
                    "timing_strategy": "Optimized for charge cooling"
                }
            }
        }

    def _initialize_models(self):
        """Initialize machine learning models with Mazda-specific features"""
        try:
            # Try to load pre-trained models
            self.driving_style_model = joblib.load('models/driving_style_classifier.pkl')
            self.performance_model = joblib.load('models/performance_predictor.pkl')
            self.safety_model = joblib.load('models/safety_analyzer.pkl')
            self.logger.info("Loaded pre-trained AI models")
        except:
            # Initialize new models with Mazda-specific feature sets
            self._create_new_models()
            self.logger.info("Initialized new AI models")

    def _create_new_models(self):
        """Create new ML models with Mazdaspeed-optimized architecture"""
        # Driving style classification (aggressive, moderate, conservative)
        self.driving_style_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        # Performance prediction (power, torque, spool time)
        self.performance_model = RandomForestRegressor(
            n_estimators=150, 
            max_depth=12,
            random_state=42
        )
        
        # Safety analysis (knock probability, component stress)
        self.safety_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )

    def process_driving_data(self, live_data):
        """Process real-time driving data and generate tuning insights"""
        # Extract features for ML models
        features = self._extract_features(live_data)
        
        # Update driving style classification
        driving_style = self._classify_driving_style(features)
        
        # Generate performance recommendations
        recommendations = self._generate_recommendations(features, driving_style)
        
        # Safety validation
        safety_checked = self._validate_safety(recommendations)
        
        return {
            'driving_style': driving_style,
            'recommendations': safety_checked,
            'confidence': self._calculate_confidence(features),
            'timestamp': time.time()
        }

    def _extract_features(self, data):
        """Extract Mazdaspeed-specific features for ML analysis"""
        features = {}
        
        # Turbo and boost characteristics
        if 'boost_pressure' in data:
            features['boost_mean'] = np.mean([d.get('boost_pressure', 0) for d in data[-10:]])
            features['boost_response'] = self._calculate_boost_response(data)
            
        # Engine load patterns
        if 'engine_load' in data:
            features['load_aggression'] = np.std([d.get('engine_load', 0) for d in data[-20:]])
            
        # RPM usage patterns
        if 'rpm' in data:
            rpm_data = [d.get('rpm', 0) for d in data[-30:]]
            features['rpm_variance'] = np.std(rpm_data)
            features['max_rpm_used'] = max(rpm_data)
            features['preferred_shift_points'] = self._detect_shift_points(rpm_data)
            
        # Thermal management
        if 'coolant_temp' in data and 'intake_temp' in data:
            features['thermal_stress'] = data[-1].get('coolant_temp', 0) - data[-1].get('intake_temp', 0)
            
        return features

    def _classify_driving_style(self, features):
        """Classify driver behavior into performance categories"""
        if not self.driving_style_model:
            return "moderate"  # Default classification
            
        # Predict driving style score (0-100)
        style_score = self.driving_style_model.predict([list(features.values())])[0]
        
        if style_score > 75:
            return "aggressive"
        elif style_score > 25:
            return "moderate" 
        else:
            return "conservative"

    def _generate_recommendations(self, features, driving_style):
        """Generate tuning recommendations based on driving patterns and goals"""
        base_strategy = self.mazda_knowledge['tuning_strategies']['daily_driver']
        
        # Adapt strategy based on driving style
        if driving_style == "aggressive":
            base_strategy = self._blend_strategies(
                self.mazda_knowledge['tuning_strategies']['daily_driver'],
                self.mazda_knowledge['tuning_strategies']['track_optimized'],
                blend_factor=0.7
            )
        elif driving_style == "conservative":
            base_strategy = self._blend_strategies(
                self.mazda_knowledge['tuning_strategies']['daily_driver'],
                self.mazda_knowledge['tuning_strategies']['high_hp_low_boost'], 
                blend_factor=0.3
            )
            
        # Fine-tune based on vehicle response characteristics
        tuned_strategy = self._adaptive_fine_tuning(base_strategy, features)
        
        return tuned_strategy

    def _adaptive_fine_tuning(self, base_strategy, features):
        """Apply fine-tuning adjustments based on vehicle response data"""
        tuned = base_strategy.copy()
        
        # Boost response optimization
        if features.get('boost_response', 0) > 3.0:  # Slow spool
            tuned['boost_curve'] = "More aggressive low-end for faster spool"
            tuned['wastegate_duty'] = "Increase initial duty cycle"
            
        # Knock tendency adjustment
        if features.get('knock_tendency', 0) > 0.1:
            tuned['timing_strategy'] = "More conservative in mid-range"
            tuned['target_afr'] = max(11.2, tuned.get('target_afr', 12.0) - 0.2)
            
        # Thermal management
        if features.get('thermal_stress', 0) > 30:  # High coolant-intake delta
            tuned['cooling_strategy'] = "More aggressive fan control"
            tuned['timing_strategy'] += " with heat-adaptive pullback"
            
        return tuned