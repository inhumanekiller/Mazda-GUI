# mazda_tool/core/mazdaspeed_knowledge.py
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class TuningStrategy:
    name: str
    description: str
    target_parameters: Dict
    safety_limits: Dict
    implementation_steps: List[str]

class MazdaspeedKnowledgeEngine:
    """Embed the technical knowledge from your document into executable guidance"""
    
    def __init__(self):
        self.load_vs_boost_explanation = self._load_boost_knowledge()
        self.tuning_strategies = self._create_tuning_strategies()
        self.common_issues = self._load_common_issues()
        
    def _load_boost_knowledge(self) -> Dict:
        return {
            "key_concept": "LOAD_TARGETING_PRIMARY",
            "explanation": "ECU uses Load as primary target, Boost is a result",
            "tables_affected": [
                "requested_load_vs_rpm",
                "load_limits_by_gear", 
                "load_compensation_tables",
                "throttle_plate_control"
            ],
            "tuning_approach": "Tune for Load targets first, then optimize boost control"
        }
    
    def _create_tuning_strategies(self) -> Dict[str, TuningStrategy]:
        return {
            "high_hp_low_boost": TuningStrategy(
                name="High HP / Low Boost Efficiency",
                description="Maximize power while maintaining K04 turbo longevity",
                target_parameters={
                    "peak_boost": 17.0,  # PSI
                    "target_afr_wot": 11.5,
                    "timing_advance_midrange": "+2.0°",
                    "load_targets": "Optimized for thermal efficiency"
                },
                safety_limits={
                    "max_boost": 18.0,
                    "min_afr": 11.2,
                    "max_knock_retard": 2.0,
                    "max_intake_temp": 50  # °C
                },
                implementation_steps=[
                    "1. Start with factory boost levels",
                    "2. Optimize timing and AFR first", 
                    "3. Add 1-2° timing in 3000-5000 RPM range",
                    "4. Target AFR of 11.5-11.8:1 under high load",
                    "5. Gradually increase boost ONLY when timing/AFR optimized",
                    "6. Validate with datalogs for knock and temps"
                ]
            ),
            "daily_driver_safe": TuningStrategy(
                name="Daily Driver - Maximum Reliability",
                description="Conservative tune for daily driving with stock components",
                target_parameters={
                    "peak_boost": 16.0,
                    "target_afr_wot": 12.0, 
                    "timing_advance": "Stock +0.5°",
                    "load_targets": "Conservative with safety margins"
                },
                safety_limits={
                    "max_boost": 16.5,
                    "min_afr": 11.8,
                    "max_knock_retard": 1.0,
                    "max_intake_temp": 45
                },
                implementation_steps=[
                    "1. Maintain near-stock boost levels",
                    "2. Small timing improvements in safe areas",
                    "3. Focus on throttle response and driveability",
                    "4. Prioritize fuel economy in cruise areas",
                    "5. Conservative load targets for engine longevity"
                ]
            )
        }
    
    def _load_common_issues(self) -> Dict:
        return {
            "P0234": {
                "description": "Overboost Condition",
                "causes": [
                    "Restrictive exhaust with high boost targets",
                    "Wastegate actuator issues", 
                    "Incorrect wastegate duty cycle tables"
                ],
                "solutions": [
                    "Ensure proper wastegate pre-load",
                    "Tune for lower boost targets with better timing",
                    "Check for exhaust restrictions"
                ],
                "emergency_action": "Reduce boost targets immediately"
            },
            "P0087": {
                "description": "Fuel Rail Pressure Low", 
                "causes": [
                    "Failing HPFP (high pressure fuel pump)",
                    "Inadequate fuel pump tuning",
                    "Excessive power levels for stock pump"
                ],
                "solutions": [
                    "Upgrade HPFP internals (Autotech, CorkSport)",
                    "Optimize fuel pressure control tables", 
                    "Monitor fuel pressure in datalogs"
                ],
                "emergency_action": "Reduce load targets and avoid WOT"
            }
        }
    
    def get_tuning_recommendation(self, goals: List[str], mods: List[str]) -> Dict:
        """Generate personalized tuning recommendations based on user goals and modifications"""
        recommendations = {
            "strategy": None,
            "parameter_targets": {},
            "safety_checks": [],
            "hardware_considerations": []
        }
        
        if "max_power" in goals and "stock_turbo" in mods:
            recommendations["strategy"] = "high_hp_low_boost"
            recommendations["parameter_targets"] = {
                "load_targets": "Focus on mid-range torque",
                "boost_control": "Conservative taper for K04 longevity", 
                "ignition_timing": "Aggressive in safe areas only"
            }
            
        elif "reliability" in goals:
            recommendations["strategy"] = "daily_driver_safe" 
            recommendations["safety_checks"] = [
                "Monitor knock activity closely",
                "Keep intake temps below 45°C",
                "Maintain fuel pressure above 1600 PSI"
            ]
        
        return recommendations