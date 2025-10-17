import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from db_handler.dynamo import Dynamo
from utils.metrics import metrics

logger = logging.getLogger(__name__)

class SubscriberManager:
    def __init__(self, dynamo_client: Dynamo):
        self.dynamo = dynamo_client
        self.table_name = "subscribers"
    
    async def create_subscriber_profile(self, email: str, preferences: Dict[str, Any] = None) -> Dict:
        """Create detailed subscriber profile with preferences"""
        try:
            if preferences is None:
                preferences = {
                    'sections': ['all'],
                    'frequency': 'weekly',
                    'format': 'html'
                }
            
            profile = {
                'email': email,
                'preferences': preferences,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active',
                'engagement_score': 0.0,
                'last_opened': None,
                'total_opens': 0,
                'total_clicks': 0
            }
            
            self.dynamo.add_item(self.table_name, "email", profile, auto_id=False)
            metrics.increment_counter('subscribers_created')
            logger.info(f"Created subscriber profile for {email}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to create subscriber profile for {email}: {e}")
            raise
    
    async def update_preferences(self, email: str, preferences: Dict[str, Any]) -> bool:
        """Update subscriber content preferences"""
        try:
            update_data = {
                'preferences': preferences,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            success = self.dynamo.update_item(
                self.table_name,
                {'email': email},
                update_data
            )
            
            if success:
                metrics.increment_counter('preferences_updated')
                logger.info(f"Updated preferences for {email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update preferences for {email}: {e}")
            return False
    
    async def get_personalized_content(self, email: str) -> Dict[str, Any]:
        """Get content preferences for subscriber"""
        try:
            profile = self.dynamo.get_item(self.table_name, {'email': email})
            
            if not profile:
                # Return default preferences for new subscriber
                return {
                    'sections': ['all'],
                    'frequency': 'weekly',
                    'format': 'html'
                }
            
            return profile.get('preferences', {
                'sections': ['all'],
                'frequency': 'weekly',
                'format': 'html'
            })
            
        except Exception as e:
            logger.error(f"Failed to get preferences for {email}: {e}")
            return {'sections': ['all'], 'frequency': 'weekly', 'format': 'html'}
    
    async def track_engagement(self, email: str, action: str, content_id: str = None):
        """Track subscriber engagement for analytics"""
        try:
            profile = self.dynamo.get_item(self.table_name, {'email': email})
            
            if not profile:
                # Create profile if it doesn't exist
                await self.create_subscriber_profile(email)
                profile = {'total_opens': 0, 'total_clicks': 0, 'engagement_score': 0.0}
            
            update_data = {'last_activity': datetime.utcnow().isoformat()}
            
            if action == 'open':
                update_data['total_opens'] = profile.get('total_opens', 0) + 1
                update_data['last_opened'] = datetime.utcnow().isoformat()
                metrics.increment_counter('email_opens')
                
            elif action == 'click':
                update_data['total_clicks'] = profile.get('total_clicks', 0) + 1
                metrics.increment_counter('email_clicks')
            
            # Calculate engagement score (simple formula)
            total_opens = update_data.get('total_opens', profile.get('total_opens', 0))
            total_clicks = update_data.get('total_clicks', profile.get('total_clicks', 0))
            engagement_score = (total_opens * 1.0 + total_clicks * 2.0) / max(total_opens, 1)
            update_data['engagement_score'] = engagement_score
            
            self.dynamo.update_item(self.table_name, {'email': email}, update_data)
            logger.debug(f"Tracked {action} for {email}")
            
        except Exception as e:
            logger.error(f"Failed to track engagement for {email}: {e}")
    
    async def get_subscriber_stats(self) -> Dict[str, Any]:
        """Get subscriber statistics"""
        try:
            # This would need to be implemented based on your DynamoDB scan capabilities
            # For now, return basic stats
            return {
                'total_subscribers': len(scheduler.subscribers) if 'scheduler' in globals() else 0,
                'active_subscribers': len(scheduler.subscribers) if 'scheduler' in globals() else 0,
                'engagement_rate': 0.0,  # Would calculate from actual data
                'last_updated': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get subscriber stats: {e}")
            return {}