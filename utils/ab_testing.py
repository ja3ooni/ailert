import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Experiment:
    name: str
    variants: List[str]
    traffic_split: Dict[str, float]
    start_date: datetime
    end_date: Optional[datetime] = None
    active: bool = True

class ABTestManager:
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.conversions: Dict[str, Dict[str, int]] = {}
    
    def create_experiment(self, name: str, variants: List[str], traffic_split: Dict[str, float]) -> bool:
        """Create new A/B test experiment"""
        try:
            # Validate traffic split
            if abs(sum(traffic_split.values()) - 1.0) > 0.001:
                raise ValueError("Traffic split must sum to 1.0")
            
            if set(variants) != set(traffic_split.keys()):
                raise ValueError("Variants and traffic split keys must match")
            
            experiment = Experiment(
                name=name,
                variants=variants,
                traffic_split=traffic_split,
                start_date=datetime.utcnow()
            )
            
            self.experiments[name] = experiment
            self.conversions[name] = {variant: 0 for variant in variants}
            
            logger.info(f"Created experiment '{name}' with variants {variants}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create experiment '{name}': {e}")
            return False
    
    def get_variant_for_user(self, experiment_name: str, user_id: str) -> Optional[str]:
        """Get experiment variant for specific user using consistent hashing"""
        if experiment_name not in self.experiments:
            logger.warning(f"Experiment '{experiment_name}' not found")
            return None
        
        experiment = self.experiments[experiment_name]
        if not experiment.active:
            return None
        
        # Use consistent hashing to assign variant
        hash_input = f"{experiment_name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        normalized_hash = (hash_value % 10000) / 10000.0
        
        cumulative_probability = 0.0
        for variant, probability in experiment.traffic_split.items():
            cumulative_probability += probability
            if normalized_hash <= cumulative_probability:
                return variant
        
        # Fallback to first variant
        return experiment.variants[0]
    
    def track_conversion(self, experiment_name: str, user_id: str, variant: str = None):
        """Track conversion events for analysis"""
        try:
            if experiment_name not in self.experiments:
                logger.warning(f"Experiment '{experiment_name}' not found")
                return
            
            if variant is None:
                variant = self.get_variant_for_user(experiment_name, user_id)
            
            if variant and variant in self.conversions[experiment_name]:
                self.conversions[experiment_name][variant] += 1
                logger.debug(f"Tracked conversion for experiment '{experiment_name}', variant '{variant}'")
            
        except Exception as e:
            logger.error(f"Failed to track conversion: {e}")
    
    def get_experiment_results(self, experiment_name: str) -> Dict[str, Any]:
        """Get experiment results and statistics"""
        if experiment_name not in self.experiments:
            return {}
        
        experiment = self.experiments[experiment_name]
        conversions = self.conversions[experiment_name]
        
        total_conversions = sum(conversions.values())
        
        results = {
            'experiment_name': experiment_name,
            'variants': experiment.variants,
            'traffic_split': experiment.traffic_split,
            'conversions': conversions,
            'total_conversions': total_conversions,
            'conversion_rates': {
                variant: (conversions[variant] / max(total_conversions, 1)) * 100
                for variant in experiment.variants
            },
            'start_date': experiment.start_date.isoformat(),
            'active': experiment.active
        }
        
        return results
    
    def stop_experiment(self, experiment_name: str) -> bool:
        """Stop an active experiment"""
        if experiment_name in self.experiments:
            self.experiments[experiment_name].active = False
            self.experiments[experiment_name].end_date = datetime.utcnow()
            logger.info(f"Stopped experiment '{experiment_name}'")
            return True
        return False
    
    def get_all_experiments(self) -> Dict[str, Dict[str, Any]]:
        """Get all experiments and their results"""
        return {
            name: self.get_experiment_results(name)
            for name in self.experiments.keys()
        }

# Global A/B test manager
ab_test_manager = ABTestManager()