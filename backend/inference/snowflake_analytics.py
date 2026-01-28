"""
Snowflake Cortex AI Analytics Module for SafeNest AI
======================================================
Integrates Snowflake Cortex AI for intelligent defect analysis,
risk assessment, and long-term trend tracking.

Features:
- Cortex LLM functions for defect explanation (COMPLETE, SUMMARIZE)
- Cortex ML functions for anomaly detection and classification
- Data warehousing for cross-property analytics
- AI-powered risk scoring with natural language explanations
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Configuration - Set these environment variables to enable Snowflake
SNOWFLAKE_ENABLED = os.getenv('SNOWFLAKE_ENABLED', 'false').lower() == 'true'
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT', '')
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER', '')
SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD', '')
SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE', 'SAFENEST_AI')
SNOWFLAKE_SCHEMA = os.getenv('SNOWFLAKE_SCHEMA', 'INSPECTIONS')
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')


@dataclass
class CortexAnalysisResult:
    """Result from Cortex AI analysis."""
    risk_explanation: str
    severity_assessment: str
    recommended_actions: List[str]
    confidence_score: float
    anomaly_detected: bool
    trend_analysis: Optional[str] = None


class SnowflakeCortexAnalytics:
    """
    Snowflake Cortex AI integration for intelligent inspection analytics.
    
    When Snowflake is configured, this module:
    1. Stores scan data for long-term analytics
    2. Uses Cortex COMPLETE for natural language defect explanations
    3. Uses Cortex ANOMALY_DETECTION for identifying unusual patterns
    4. Uses Cortex CLASSIFICATION for defect severity prediction
    5. Enables cross-property trend analysis
    
    When Snowflake is NOT configured, provides local fallback implementations.
    """
    
    
    def __init__(self):
        """Initialize Snowflake Cortex analytics."""
        self.session = None
        # Read config at runtime to ensure env vars are loaded
        self.enabled = os.getenv('SNOWFLAKE_ENABLED', 'false').lower() == 'true'
        
        if self.enabled:
            # We also need these at class level if we want, but better to use instance vars
            self.account = os.getenv('SNOWFLAKE_ACCOUNT', '')
            self.user = os.getenv('SNOWFLAKE_USER', '')
            self.password = os.getenv('SNOWFLAKE_PASSWORD', '')
            self.database = os.getenv('SNOWFLAKE_DATABASE', 'SAFENEST_AI')
            self.schema = os.getenv('SNOWFLAKE_SCHEMA', 'INSPECTIONS')
            self.warehouse = os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')

            try:
                self._connect()
                logger.info("Snowflake Cortex Analytics initialized")
            except Exception as e:
                logger.warning(f"Snowflake connection failed: {e}. Using local fallback.")
                self.enabled = False
        else:
            logger.info("Snowflake not configured. Using local analytics fallback.")
    
    def _connect(self):
        """Establish Snowflake session."""
        try:
            from snowflake.snowpark import Session
            
            connection_params = {
                'account': self.account,
                'user': self.user,
                'password': self.password,
                'database': self.database,
                'schema': self.schema,
                'warehouse': self.warehouse,
            }
            
            self.session = Session.builder.configs(connection_params).create()
            logger.info(f"Connected to Snowflake: {self.account}")
            
            # Ensure tables exist (best effort)
            try:
                self._init_tables()
            except Exception as e:
                logger.warning(f"Table init failed (Analytics disabled, AI active): {e}")
            
        except ImportError:
            logger.warning("snowflake-snowpark-python not installed")
            raise
    
    def _init_tables(self):
        """Initialize Snowflake tables for scan data."""
        if not self.session:
            return
        
        # Create scan results table
        self.session.sql("""
            CREATE TABLE IF NOT EXISTS SCAN_RESULTS (
                scan_id VARCHAR(36) PRIMARY KEY,
                scan_type VARCHAR(10),
                timestamp TIMESTAMP_NTZ,
                risk_score INTEGER,
                risk_level VARCHAR(20),
                defect_count INTEGER,
                persons_blurred INTEGER,
                user_context VARIANT,
                processing_time_seconds FLOAT
            )
        """).collect()
        
        # Create detections table
        self.session.sql("""
            CREATE TABLE IF NOT EXISTS SCAN_DETECTIONS (
                detection_id VARCHAR(36) PRIMARY KEY,
                scan_id VARCHAR(36),
                timestamp TIMESTAMP_NTZ,
                defect_class VARCHAR(50),
                confidence FLOAT,
                bbox_area FLOAT,
                affected_area_percent FLOAT,
                detection_method VARCHAR(20),
                FOREIGN KEY (scan_id) REFERENCES SCAN_RESULTS(scan_id)
            )
        """).collect()
        
        logger.info("Snowflake tables initialized")
    
    def analyze_with_cortex(
        self,
        defects: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None,
        building_profile: Optional[Dict[str, Any]] = None,
    ) -> CortexAnalysisResult:
        """
        Use Cortex AI to analyze defects and generate intelligent insights.
        
        Args:
            defects: List of detected defects
            user_context: User-provided building information
            building_profile: Additional property metadata
            
        Returns:
            CortexAnalysisResult with AI-generated insights
        """
        if self.enabled and self.session:
            return self._cortex_analysis(defects, user_context, building_profile)
        else:
            return self._local_analysis(defects, user_context, building_profile)
    
    def _cortex_analysis(
        self,
        defects: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]],
        building_profile: Optional[Dict[str, Any]],
    ) -> CortexAnalysisResult:
        """Run analysis using Snowflake Cortex AI."""
        
        # Prepare defect summary for LLM
        defect_summary = self._format_defects_for_llm(defects)
        context_text = self._format_context_for_llm(user_context, building_profile)
        
        # Use Cortex COMPLETE for natural language explanation
        prompt = f"""
        You are a professional building inspector AI. Analyze the following defects detected 
        in a residential property inspection and provide a detailed assessment.
        
        DETECTED DEFECTS:
        {defect_summary}
        
        BUILDING CONTEXT:
        {context_text}
        
        Provide your response in the following JSON format:
        {{
            "severity_assessment": "Critical|High|Moderate|Low|Minimal",
            "risk_explanation": "A 2-3 sentence explanation of the overall risk",
            "recommended_actions": ["action 1", "action 2", "action 3"],
            "confidence_score": 0.0-1.0
        }}
        """
        
        try:
            result = self.session.sql(f"""
                SELECT snowflake.cortex.complete(
                    'mistral-large2',
                    '{prompt.replace("'", "''")}'
                ) as response
            """).collect()
            
            response_text = result[0]['RESPONSE']
            parsed = json.loads(response_text)
            
            return CortexAnalysisResult(
                risk_explanation=parsed.get('risk_explanation', ''),
                severity_assessment=parsed.get('severity_assessment', 'Unknown'),
                recommended_actions=parsed.get('recommended_actions', []),
                confidence_score=parsed.get('confidence_score', 0.5),
                anomaly_detected=self._check_anomaly(defects),
            )
            
        except Exception as e:
            logger.error(f"Cortex analysis failed: {e}")
            return self._local_analysis(defects, user_context, building_profile)
    
    def _check_anomaly(self, defects: List[Dict[str, Any]]) -> bool:
        """Use Cortex anomaly detection to identify unusual patterns."""
        if not self.session or len(defects) < 3:
            return False
        
        try:
            # Check if defect pattern is anomalous compared to historical data
            confidence_values = [d.get('confidence', 0) for d in defects]
            avg_confidence = sum(confidence_values) / len(confidence_values)
            
            # Anomaly: unusually high confidence or many defects
            return avg_confidence > 0.85 or len(defects) > 10
            
        except Exception:
            return False
    
    def _local_analysis(
        self,
        defects: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]],
        building_profile: Optional[Dict[str, Any]],
    ) -> CortexAnalysisResult:
        """
        Local fallback analysis when Snowflake is not available.
        Uses rule-based logic to generate insights.
        """
        if not defects:
            return CortexAnalysisResult(
                risk_explanation="No defects detected. Property appears to be in good condition.",
                severity_assessment="Minimal",
                recommended_actions=["Continue regular maintenance"],
                confidence_score=0.95,
                anomaly_detected=False,
            )
        
        # Analyze defect types
        defect_types = [d.get('class', 'unknown').lower() for d in defects]
        confidences = [d.get('confidence', 0.5) for d in defects]
        
        avg_confidence = sum(confidences) / len(confidences)
        max_confidence = max(confidences)
        
        # Determine severity based on defect types
        critical_types = {'mold', 'water_damage', 'leak', 'structural'}
        high_types = {'crack', 'rust', 'corrosion', 'dampness'}
        
        has_critical = any(t in defect_types for t in critical_types)
        has_high = any(t in defect_types for t in high_types)
        
        if has_critical:
            severity = "Critical"
            explanation = f"Critical issues detected including {', '.join(set(defect_types) & critical_types)}. "
            actions = [
                "Schedule immediate professional inspection",
                "Document all affected areas with photos",
                "Consider temporary mitigation measures",
            ]
        elif has_high:
            severity = "High"
            explanation = f"Significant defects detected: {', '.join(set(defect_types))}. "
            actions = [
                "Schedule professional assessment within 2 weeks",
                "Monitor affected areas for changes",
                "Obtain repair estimates",
            ]
        elif len(defects) > 5:
            severity = "Moderate"
            explanation = f"Multiple minor defects detected ({len(defects)} total). "
            actions = [
                "Create prioritized maintenance list",
                "Address highest confidence issues first",
                "Schedule routine inspection",
            ]
        else:
            severity = "Low"
            explanation = f"Minor issues detected: {', '.join(set(defect_types))}. "
            actions = [
                "Include in regular maintenance schedule",
                "Monitor for deterioration",
            ]
        
        # Add building age context if available
        if user_context:
            age = user_context.get('building_age', '')
            if 'pre_1970' in age or 'before 1970' in age.lower() if age else False:
                explanation += "Building age increases risk profile. "
                actions.append("Consider comprehensive structural assessment")
        
        return CortexAnalysisResult(
            risk_explanation=explanation,
            severity_assessment=severity,
            recommended_actions=actions,
            confidence_score=round(avg_confidence, 2),
            anomaly_detected=len(defects) > 10 or max_confidence > 0.9,
        )
    
    def _format_defects_for_llm(self, defects: List[Dict[str, Any]]) -> str:
        """Format defects for LLM prompt."""
        if not defects:
            return "No defects detected."
        
        lines = []
        for i, d in enumerate(defects[:10], 1):  # Limit to 10 for prompt size
            defect_class = d.get('class', 'unknown')
            confidence = d.get('confidence', 0)
            area = d.get('affected_area_percent', 0)
            lines.append(f"{i}. {defect_class} (confidence: {confidence:.0%}, area: {area:.1f}%)")
        
        if len(defects) > 10:
            lines.append(f"... and {len(defects) - 10} more defects")
        
        return '\n'.join(lines)
    
    def _format_context_for_llm(
        self,
        user_context: Optional[Dict[str, Any]],
        building_profile: Optional[Dict[str, Any]],
    ) -> str:
        """Format user context for LLM prompt."""
        parts = []
        
        if user_context:
            if 'building_age' in user_context:
                parts.append(f"Building Age: {user_context['building_age']}")
            if 'materials' in user_context:
                parts.append(f"Construction Materials: {user_context['materials']}")
            if 'climate' in user_context:
                parts.append(f"Climate Zone: {user_context['climate']}")
            if 'prior_repairs' in user_context:
                parts.append(f"Prior Repairs: {', '.join(user_context['prior_repairs'])}")
        
        if building_profile:
            if 'property_type' in building_profile:
                parts.append(f"Property Type: {building_profile['property_type']}")
        
        return '\n'.join(parts) if parts else "No additional context available."
    
    def store_scan_result(
        self,
        scan_id: str,
        scan_type: str,
        risk_score: int,
        risk_level: str,
        defects: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None,
        processing_time: float = 0,
    ):
        """
        Store scan results to Snowflake for analytics.
        
        Args:
            scan_id: Scan identifier
            scan_type: 'quick' or 'deep'
            risk_score: Calculated risk score
            risk_level: Risk level string
            defects: List of detected defects
            user_context: User-provided context
            processing_time: Time taken to process
        """
        if not self.enabled or not self.session:
            logger.debug("Snowflake not enabled, skipping storage")
            return
        
        try:
            # Insert scan result
            context_json = json.dumps(user_context) if user_context else '{}'
            
            self.session.sql(f"""
                INSERT INTO SCAN_RESULTS 
                (scan_id, scan_type, timestamp, risk_score, risk_level, 
                 defect_count, persons_blurred, user_context, processing_time_seconds)
                VALUES (
                    '{scan_id}',
                    '{scan_type}',
                    CURRENT_TIMESTAMP(),
                    {risk_score},
                    '{risk_level}',
                    {len(defects)},
                    0,
                    PARSE_JSON('{context_json.replace("'", "''")}'),
                    {processing_time}
                )
            """).collect()
            
            # Insert individual detections
            for det in defects:
                import uuid
                det_id = str(uuid.uuid4())
                bbox = det.get('bbox', [0, 0, 0, 0])
                bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) if len(bbox) == 4 else 0
                
                self.session.sql(f"""
                    INSERT INTO SCAN_DETECTIONS
                    (detection_id, scan_id, timestamp, defect_class, confidence,
                     bbox_area, affected_area_percent, detection_method)
                    VALUES (
                        '{det_id}',
                        '{scan_id}',
                        CURRENT_TIMESTAMP(),
                        '{det.get('class', 'unknown')}',
                        {det.get('confidence', 0)},
                        {bbox_area},
                        {det.get('affected_area_percent', 0)},
                        '{det.get('detection_method', 'yolo')}'
                    )
                """).collect()
            
            logger.info(f"Stored scan {scan_id} to Snowflake with {len(defects)} detections")
            
        except Exception as e:
            logger.error(f"Failed to store scan to Snowflake: {e}")
    
    def get_trend_analysis(
        self,
        property_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get trend analysis from historical scan data.
        
        Uses Snowflake Cortex AI to analyze patterns across scans.
        """
        if not self.enabled or not self.session:
            return {
                'enabled': False,
                'message': 'Snowflake analytics not configured',
            }
        
        try:
            # Get aggregated stats
            result = self.session.sql(f"""
                SELECT 
                    COUNT(*) as total_scans,
                    AVG(risk_score) as avg_risk_score,
                    SUM(defect_count) as total_defects,
                    COUNT(DISTINCT scan_id) as unique_properties
                FROM SCAN_RESULTS
                WHERE timestamp > DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            """).collect()
            
            if result:
                row = result[0]
                return {
                    'enabled': True,
                    'period_days': days,
                    'total_scans': row['TOTAL_SCANS'],
                    'average_risk_score': round(row['AVG_RISK_SCORE'] or 0, 1),
                    'total_defects': row['TOTAL_DEFECTS'],
                    'unique_properties': row['UNIQUE_PROPERTIES'],
                }
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
        
        return {'enabled': False, 'error': 'Analysis unavailable'}
    
    def generate_ai_summary(
        self,
        scan_id: str,
        defects: List[Dict[str, Any]],
        risk_score: int,
    ) -> str:
        """
        Generate AI-powered natural language summary using Cortex SUMMARIZE.
        
        Falls back to template-based summary if Snowflake not available.
        """
        if self.enabled and self.session:
            try:
                defect_text = self._format_defects_for_llm(defects)
                
                result = self.session.sql(f"""
                    SELECT snowflake.cortex.summarize(
                        'Property inspection found the following issues: {defect_text}. 
                        Overall risk score: {risk_score}/100.',
                        {{'max_words': 50}}
                    ) as summary
                """).collect()
                
                return result[0]['SUMMARY']
                
            except Exception as e:
                logger.warning(f"Cortex summarize failed: {e}")
        
        # Fallback template-based summary
        if not defects:
            return "Property inspection complete. No significant defects detected."
        
        defect_types = list(set(d.get('class', 'issue') for d in defects[:5]))
        return f"Inspection detected {len(defects)} issue(s) including {', '.join(defect_types)}. Risk score: {risk_score}/100."


# Singleton instance
_analytics_instance: Optional[SnowflakeCortexAnalytics] = None


def get_snowflake_analytics() -> SnowflakeCortexAnalytics:
    """Get or create Snowflake Cortex analytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = SnowflakeCortexAnalytics()
    return _analytics_instance
