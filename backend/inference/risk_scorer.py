"""
Risk Scorer Module for SafeNest AI
===================================
Calculates 0-100 safety risk scores based on detected defects.

Features:
- Data-driven, explainable risk scoring
- User context fusion (building age, materials, climate)
- Snowflake Cortex AI integration for intelligent insights
- Per-component penalty breakdown
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DefectWeight:
    """Weight configuration for defect types."""
    severity: float  # 1-5 scale
    area_multiplier: float  # How much area affects score
    description: str = ""  # Human-readable description


# Defect severity weights with explanations
DEFECT_WEIGHTS = {
    'crack': DefectWeight(severity=3.0, area_multiplier=1.5, description="Structural cracks may indicate foundation or settling issues"),
    'leak': DefectWeight(severity=4.0, area_multiplier=2.0, description="Active leaks cause progressive damage"),
    'water_damage': DefectWeight(severity=4.0, area_multiplier=2.0, description="Water damage may hide mold or rot"),
    'damp': DefectWeight(severity=2.0, area_multiplier=1.2, description="Dampness indicates moisture intrusion"),
    'dampness': DefectWeight(severity=2.0, area_multiplier=1.2, description="Dampness indicates moisture intrusion"),
    'mold': DefectWeight(severity=5.0, area_multiplier=2.5, description="Mold poses health hazards and spreads"),
    'mould': DefectWeight(severity=5.0, area_multiplier=2.5, description="Mold poses health hazards and spreads"),
    'corrosion': DefectWeight(severity=3.0, area_multiplier=1.5, description="Corrosion weakens structural elements"),
    'rust': DefectWeight(severity=3.0, area_multiplier=1.5, description="Rust indicates moisture exposure"),
    'peeling': DefectWeight(severity=1.5, area_multiplier=1.0, description="Peeling paint may expose surfaces"),
    'stain': DefectWeight(severity=1.0, area_multiplier=0.8, description="Staining may indicate past water issues"),
    'electrical': DefectWeight(severity=4.5, area_multiplier=1.0, description="Electrical issues pose fire/safety risk"),
    'spalling': DefectWeight(severity=3.5, area_multiplier=1.8, description="Concrete spalling exposes rebar"),
    'deformation': DefectWeight(severity=4.0, area_multiplier=2.0, description="Structural deformation is serious"),
    'default': DefectWeight(severity=2.0, area_multiplier=1.0, description="Potential issue requiring assessment"),
}

# Building age penalty factors
AGE_FACTORS = {
    'pre_1950': 15.0,
    'pre_1970': 10.0,
    '1970_1990': 5.0,
    '1990_2010': 2.0,
    'post_2010': 0.0,
}

# Climate zone adjustments
CLIMATE_FACTORS = {
    'hot_humid': {'mold': 1.5, 'dampness': 1.3, 'rust': 1.2},
    'cold_dry': {'crack': 1.3, 'spalling': 1.4},
    'coastal': {'rust': 1.5, 'corrosion': 1.5, 'salt_damage': 1.4},
    'temperate': {},  # No adjustments
}


class RiskScorer:
    """
    Calculates property safety risk scores with data-driven methodology.
    
    Formula:
    risk_score = 100 - (
        w_defects * defect_penalty +
        w_age * age_factor +
        w_user * user_severity_adjustment
    )
    
    Score interpretation:
    - 0-30: High Risk (immediate attention needed)
    - 31-60: Moderate Risk (address soon)
    - 61-100: Low Risk (acceptable condition)
    """
    
    def __init__(
        self,
        base_score: float = 100.0,
        max_defects_penalty: float = 70.0,
        confidence_weight: float = 0.8,
        enable_cortex_ai: bool = True,
    ):
        """
        Initialize risk scorer.
        
        Args:
            base_score: Starting score (100 = perfect)
            max_defects_penalty: Maximum penalty from defects
            confidence_weight: How much detection confidence affects penalty
            enable_cortex_ai: Enable Snowflake Cortex AI for explanations
        """
        self.base_score = base_score
        self.max_defects_penalty = max_defects_penalty
        self.confidence_weight = confidence_weight
        self.enable_cortex_ai = enable_cortex_ai
        self._cortex_analytics = None
    
    def _get_cortex_analytics(self):
        """Lazy load Snowflake Cortex analytics."""
        if self._cortex_analytics is None and self.enable_cortex_ai:
            try:
                from .snowflake_analytics import get_snowflake_analytics
                self._cortex_analytics = get_snowflake_analytics()
            except ImportError:
                logger.warning("Snowflake analytics not available")
                self._cortex_analytics = None
        return self._cortex_analytics
    
    def calculate_score(
        self,
        defects: List[Dict[str, Any]],
        image_area: int = 640 * 480,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate risk score from detected defects.
        
        Args:
            defects: List of defect detections
            image_area: Total image area in pixels
            
        Returns:
            Dictionary with score and breakdown
        """
        if not defects:
            base_result = {
                'score': 100,
                'risk_level': 'Low Risk',
                'defect_count': 0,
                'breakdown': [],
                'penalty_breakdown': {
                    'defects': 0,
                    'age_factor': 0,
                    'climate_factor': 0,
                },
                'summary': 'No defects detected. Property appears to be in good condition.',
                'ai_explanation': None,
                'recommended_actions': ['Continue regular maintenance'],
            }
            return base_result
        
        total_penalty = 0.0
        breakdown = []
        penalty_by_type = {}
        
        # Get climate adjustments if available
        climate = user_context.get('climate', 'temperate') if user_context else 'temperate'
        climate_adjustments = CLIMATE_FACTORS.get(climate, {})
        
        for defect in defects:
            defect_class = defect.get('class', 'unknown').lower()
            confidence = defect.get('confidence', 0.5)
            bbox = defect.get('bbox', [0, 0, 0, 0])
            affected_area_percent = defect.get('affected_area_percent', None)
            
            # Get weight for this defect type
            weight = DEFECT_WEIGHTS.get(defect_class, DEFECT_WEIGHTS['default'])
            
            # Apply climate adjustment
            climate_mult = climate_adjustments.get(defect_class, 1.0)
            
            # Calculate defect area
            if affected_area_percent is not None:
                area_factor = affected_area_percent / 10.0  # Normalize
            else:
                # Estimate from bounding box
                if len(bbox) == 4:
                    box_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                    area_factor = (box_area / image_area) * 10.0
                else:
                    area_factor = 1.0
            
            # Calculate penalty for this defect
            base_penalty = weight.severity * 3.0  # Base penalty per defect
            area_penalty = area_factor * weight.area_multiplier
            confidence_factor = confidence * self.confidence_weight + (1 - self.confidence_weight)
            
            defect_penalty = (base_penalty + area_penalty) * confidence_factor * climate_mult
            total_penalty += defect_penalty
            
            # Track penalty by defect type for breakdown
            penalty_by_type[defect_class] = penalty_by_type.get(defect_class, 0) + defect_penalty
            
            breakdown.append({
                'defect_type': defect_class,
                'confidence': round(confidence, 2),
                'penalty': round(defect_penalty, 2),
                'severity': weight.severity,
                'description': weight.description,
                'climate_adjusted': climate_mult != 1.0,
            })
        
        # Calculate age penalty if user context provided
        age_penalty = 0.0
        if user_context and 'building_age' in user_context:
            age_key = user_context['building_age']
            age_penalty = AGE_FACTORS.get(age_key, 0.0)
            total_penalty += age_penalty
        
        # Cap penalty at max (but keep track of components)
        defect_penalty_capped = min(total_penalty - age_penalty, self.max_defects_penalty)
        total_penalty = defect_penalty_capped + age_penalty
        
        # Calculate final score
        final_score = max(0, self.base_score - total_penalty)
        final_score = round(final_score)
        
        # Determine risk level and base summary
        if final_score <= 30:
            risk_level = 'High Risk'
            summary = 'Critical defects detected. Immediate professional inspection recommended.'
            recommended_actions = [
                'Schedule professional inspection immediately',
                'Document all affected areas with photos',
                'Consider temporary mitigation measures',
            ]
        elif final_score <= 60:
            risk_level = 'Moderate Risk'
            summary = 'Several defects detected. Consider addressing these issues soon.'
            recommended_actions = [
                'Schedule professional assessment within 2 weeks',
                'Monitor affected areas for changes',
                'Obtain repair estimates',
            ]
        else:
            risk_level = 'Low Risk'
            summary = 'Minor issues detected. Property is in acceptable condition.'
            recommended_actions = [
                'Include in regular maintenance schedule',
                'Monitor for deterioration over time',
            ]
        
        # Get AI-powered insights if Cortex is available
        ai_explanation = None
        cortex = self._get_cortex_analytics()
        if cortex:
            try:
                cortex_result = cortex.analyze_with_cortex(defects, user_context)
                ai_explanation = cortex_result.risk_explanation
                if cortex_result.recommended_actions:
                    recommended_actions = cortex_result.recommended_actions
            except Exception as e:
                logger.warning(f"Cortex AI analysis failed: {e}")
        
        logger.info(f"Risk score calculated: {final_score} ({risk_level})")
        
        return {
            'score': final_score,
            'risk_level': risk_level,
            'defect_count': len(defects),
            'total_penalty': round(total_penalty, 2),
            'penalty_breakdown': {
                'defects': round(defect_penalty_capped, 2),
                'age_factor': round(age_penalty, 2),
                'by_defect_type': {k: round(v, 2) for k, v in penalty_by_type.items()},
            },
            'breakdown': breakdown,
            'summary': summary,
            'ai_explanation': ai_explanation,
            'recommended_actions': recommended_actions,
            'user_context_applied': user_context is not None,
        }
    
    def aggregate_scores(
        self,
        frame_scores: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Aggregate scores from multiple frames into overall assessment.
        
        Args:
            frame_scores: List of per-frame score results
            
        Returns:
            Aggregated score and analysis
        """
        if not frame_scores:
            return self.calculate_score([])
        
        # Use minimum score (worst case) as primary
        min_score = min(s['score'] for s in frame_scores)
        avg_score = sum(s['score'] for s in frame_scores) / len(frame_scores)
        
        # Collect all unique defects
        all_defects = []
        for fs in frame_scores:
            all_defects.extend(fs.get('breakdown', []))
        
        # Determine overall risk
        if min_score <= 30:
            risk_level = 'High Risk'
        elif min_score <= 60:
            risk_level = 'Moderate Risk'
        else:
            risk_level = 'Low Risk'
        
        return {
            'score': min_score,  # Conservative - use worst frame
            'average_score': round(avg_score),
            'risk_level': risk_level,
            'frames_analyzed': len(frame_scores),
            'total_defects_found': sum(s['defect_count'] for s in frame_scores),
            'defect_breakdown': all_defects,
        }


# Singleton instance
_scorer_instance = None


def get_risk_scorer() -> RiskScorer:
    """Get or create risk scorer instance."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = RiskScorer()
    return _scorer_instance
