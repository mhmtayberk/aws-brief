import yaml
import re
import os
import logging
from enum import Enum
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FilterAction(str, Enum):
    NOTIFY = "NOTIFY"
    IGNORE = "IGNORE"
    DIGEST_ONLY = "DIGEST_ONLY"

class FilterEngine:
    def __init__(self, config_path: str = "filters.yaml"):
        self.config_path = config_path
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.config_path):
            logger.debug(f"Filter config {self.config_path} not found. Filtering disabled.")
            return []
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
                rules = data.get('rules', [])
                logger.info(f"Loaded {len(rules)} filtering rules.")
                return rules
        except Exception as e:
            logger.error(f"Failed to load filter rules: {e}")
            return []

    def evaluate(self, title: str, content: str = "") -> FilterAction:
        """
        Evaluate an item against loaded rules. First match wins.
        Default action is NOTIFY.
        """
        if not self.rules:
            return FilterAction.NOTIFY
            
        for rule in self.rules:
            try:
                name = rule.get("name", "Unknown Rule")
                match_config = rule.get("match", {})
                action_str = rule.get("action", "NOTIFY").upper()
                
                # Check Title Regex
                if "title_regex" in match_config:
                    pattern = match_config["title_regex"]
                    if re.search(pattern, title, re.IGNORECASE):
                        logger.info(f"Filter Match: '{title}' matched rule '{name}' -> {action_str}")
                        return FilterAction(action_str)
                        
                # Future: Add content regex or other fields
                
            except Exception as e:
                logger.error(f"Error evaluating rule {rule}: {e}")
                continue
                
        return FilterAction.NOTIFY
