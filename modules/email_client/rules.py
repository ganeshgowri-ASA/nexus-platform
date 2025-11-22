"""
Email Rules and Automation

Inbox rules, auto-reply, and email automation.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class RuleConditionType(Enum):
    """Rule condition types."""
    FROM_CONTAINS = "from_contains"
    TO_CONTAINS = "to_contains"
    SUBJECT_CONTAINS = "subject_contains"
    BODY_CONTAINS = "body_contains"
    HAS_ATTACHMENT = "has_attachment"
    SIZE_GREATER_THAN = "size_greater_than"
    SIZE_LESS_THAN = "size_less_than"
    IS_FROM_DOMAIN = "is_from_domain"


class RuleActionType(Enum):
    """Rule action types."""
    MOVE_TO_FOLDER = "move_to_folder"
    ADD_LABEL = "add_label"
    MARK_AS_READ = "mark_as_read"
    MARK_AS_STARRED = "mark_as_starred"
    DELETE = "delete"
    FORWARD_TO = "forward_to"
    AUTO_REPLY = "auto_reply"
    MARK_AS_SPAM = "mark_as_spam"
    SET_CATEGORY = "set_category"


@dataclass
class RuleCondition:
    """Rule condition."""
    condition_type: RuleConditionType
    value: Any
    case_sensitive: bool = False


@dataclass
class RuleAction:
    """Rule action."""
    action_type: RuleActionType
    value: Any


@dataclass
class EmailRule:
    """Email automation rule."""
    rule_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""

    # Conditions (AND logic)
    conditions: List[RuleCondition] = field(default_factory=list)

    # Actions (all executed)
    actions: List[RuleAction] = field(default_factory=list)

    # Settings
    is_enabled: bool = True
    stop_processing: bool = False  # Stop other rules after this one

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    execution_count: int = 0
    last_executed: Optional[datetime] = None


@dataclass
class AutoReplyConfig:
    """Auto-reply/vacation configuration."""
    config_id: str = field(default_factory=lambda: str(uuid4()))
    is_enabled: bool = False

    subject: str = "Out of Office"
    message: str = ""

    # Schedule
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Limits
    send_to_each_sender_once: bool = True  # Only reply once per sender
    replied_to: set = field(default_factory=set)  # Track who we've replied to


class RulesEngine:
    """
    Email rules and automation engine.

    Processes incoming emails against rules and executes actions.
    """

    def __init__(self):
        """Initialize rules engine."""
        self.rules: Dict[str, EmailRule] = {}
        self.auto_reply_config: Optional[AutoReplyConfig] = None
        self._initialize_default_rules()

    def _initialize_default_rules(self) -> None:
        """Create default rules."""
        # Spam filter rule
        spam_rule = EmailRule(
            rule_id="spam_filter",
            name="Spam Filter",
            description="Move obvious spam to spam folder",
            conditions=[
                RuleCondition(
                    condition_type=RuleConditionType.SUBJECT_CONTAINS,
                    value="viagra"
                ),
            ],
            actions=[
                RuleAction(
                    action_type=RuleActionType.MARK_AS_SPAM,
                    value=True
                ),
                RuleAction(
                    action_type=RuleActionType.MOVE_TO_FOLDER,
                    value="Spam"
                )
            ],
            stop_processing=True
        )
        self.rules[spam_rule.rule_id] = spam_rule

    async def apply_rules(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all enabled rules to a message.

        Args:
            message: Email message

        Returns:
            Dict: Modified message
        """
        # Sort rules by creation date (FIFO)
        sorted_rules = sorted(
            [r for r in self.rules.values() if r.is_enabled],
            key=lambda r: r.created_at
        )

        for rule in sorted_rules:
            # Check if all conditions match
            if self._check_conditions(message, rule.conditions):
                # Execute all actions
                message = await self._execute_actions(message, rule.actions)

                # Update rule stats
                rule.execution_count += 1
                rule.last_executed = datetime.utcnow()

                logger.info(f"Applied rule: {rule.name}")

                # Stop processing if specified
                if rule.stop_processing:
                    break

        # Check auto-reply
        await self._check_auto_reply(message)

        return message

    def _check_conditions(
        self,
        message: Dict[str, Any],
        conditions: List[RuleCondition]
    ) -> bool:
        """Check if message matches all conditions (AND logic)."""
        for condition in conditions:
            if not self._check_condition(message, condition):
                return False
        return True

    def _check_condition(
        self,
        message: Dict[str, Any],
        condition: RuleCondition
    ) -> bool:
        """Check a single condition."""
        ctype = condition.condition_type
        value = condition.value

        # Get message field
        if ctype == RuleConditionType.FROM_CONTAINS:
            field_value = message.get('from_address', '')
            if not condition.case_sensitive:
                field_value = field_value.lower()
                value = value.lower()
            return value in field_value

        elif ctype == RuleConditionType.TO_CONTAINS:
            to_addrs = message.get('to_addresses', [])
            if not condition.case_sensitive:
                to_addrs = [addr.lower() for addr in to_addrs]
                value = value.lower()
            return any(value in addr for addr in to_addrs)

        elif ctype == RuleConditionType.SUBJECT_CONTAINS:
            field_value = message.get('subject', '')
            if not condition.case_sensitive:
                field_value = field_value.lower()
                value = value.lower()
            return value in field_value

        elif ctype == RuleConditionType.BODY_CONTAINS:
            body = message.get('body_text', '') + message.get('body_html', '')
            if not condition.case_sensitive:
                body = body.lower()
                value = value.lower()
            return value in body

        elif ctype == RuleConditionType.HAS_ATTACHMENT:
            return message.get('has_attachments', False) == value

        elif ctype == RuleConditionType.SIZE_GREATER_THAN:
            return message.get('size_bytes', 0) > value

        elif ctype == RuleConditionType.SIZE_LESS_THAN:
            return message.get('size_bytes', 0) < value

        elif ctype == RuleConditionType.IS_FROM_DOMAIN:
            from_addr = message.get('from_address', '')
            domain = from_addr.split('@')[-1] if '@' in from_addr else ''
            return domain.lower() == value.lower()

        return False

    async def _execute_actions(
        self,
        message: Dict[str, Any],
        actions: List[RuleAction]
    ) -> Dict[str, Any]:
        """Execute all actions on a message."""
        for action in actions:
            message = await self._execute_action(message, action)
        return message

    async def _execute_action(
        self,
        message: Dict[str, Any],
        action: RuleAction
    ) -> Dict[str, Any]:
        """Execute a single action."""
        atype = action.action_type
        value = action.value

        if atype == RuleActionType.MOVE_TO_FOLDER:
            message['folder'] = value

        elif atype == RuleActionType.ADD_LABEL:
            if 'labels' not in message:
                message['labels'] = set()
            message['labels'].add(value)

        elif atype == RuleActionType.MARK_AS_READ:
            message['is_read'] = value

        elif atype == RuleActionType.MARK_AS_STARRED:
            message['is_starred'] = value

        elif atype == RuleActionType.DELETE:
            message['is_deleted'] = True

        elif atype == RuleActionType.MARK_AS_SPAM:
            message['is_spam'] = value

        elif atype == RuleActionType.SET_CATEGORY:
            message['ai_category'] = value

        elif atype == RuleActionType.FORWARD_TO:
            # TODO: Implement forwarding
            logger.info(f"Would forward to: {value}")

        elif atype == RuleActionType.AUTO_REPLY:
            # TODO: Implement auto-reply
            logger.info(f"Would auto-reply with: {value}")

        return message

    async def _check_auto_reply(self, message: Dict[str, Any]) -> None:
        """Check and send auto-reply if configured."""
        if not self.auto_reply_config or not self.auto_reply_config.is_enabled:
            return

        config = self.auto_reply_config

        # Check schedule
        now = datetime.utcnow()
        if config.start_date and now < config.start_date:
            return
        if config.end_date and now > config.end_date:
            return

        # Check if already replied to this sender
        from_addr = message.get('from_address', '')
        if config.send_to_each_sender_once and from_addr in config.replied_to:
            return

        # TODO: Send auto-reply
        logger.info(f"Would send auto-reply to: {from_addr}")

        # Track sender
        if config.send_to_each_sender_once:
            config.replied_to.add(from_addr)

    def add_rule(self, rule: EmailRule) -> str:
        """
        Add a new rule.

        Args:
            rule: Email rule

        Returns:
            str: Rule ID
        """
        self.rules[rule.rule_id] = rule
        logger.info(f"Added rule: {rule.name}")
        return rule.rule_id

    def update_rule(self, rule: EmailRule) -> bool:
        """Update an existing rule."""
        if rule.rule_id in self.rules:
            rule.updated_at = datetime.utcnow()
            self.rules[rule.rule_id] = rule
            return True
        return False

    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].is_enabled = True
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule."""
        if rule_id in self.rules:
            self.rules[rule_id].is_enabled = False
            return True
        return False

    def list_rules(self) -> List[EmailRule]:
        """List all rules."""
        return list(self.rules.values())

    def get_rule(self, rule_id: str) -> Optional[EmailRule]:
        """Get a specific rule."""
        return self.rules.get(rule_id)

    def configure_auto_reply(self, config: AutoReplyConfig) -> None:
        """
        Configure auto-reply/vacation mode.

        Args:
            config: Auto-reply configuration
        """
        self.auto_reply_config = config
        logger.info("Auto-reply configured")

    def disable_auto_reply(self) -> None:
        """Disable auto-reply."""
        if self.auto_reply_config:
            self.auto_reply_config.is_enabled = False

    def get_auto_reply_config(self) -> Optional[AutoReplyConfig]:
        """Get current auto-reply configuration."""
        return self.auto_reply_config

    def test_rule(
        self,
        rule: EmailRule,
        test_messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Test a rule against messages.

        Args:
            rule: Rule to test
            test_messages: Messages to test against

        Returns:
            List[Dict]: Messages that match the rule
        """
        matching = []

        for message in test_messages:
            if self._check_conditions(message, rule.conditions):
                matching.append(message)

        return matching


# Predefined rule templates
RULE_TEMPLATES = {
    "spam_filter": EmailRule(
        name="Spam Filter",
        description="Move spam to Spam folder",
        conditions=[
            RuleCondition(
                condition_type=RuleConditionType.SUBJECT_CONTAINS,
                value="spam_keyword"
            )
        ],
        actions=[
            RuleAction(
                action_type=RuleActionType.MOVE_TO_FOLDER,
                value="Spam"
            )
        ]
    ),
    "newsletter": EmailRule(
        name="Newsletter Filter",
        description="Label newsletters",
        conditions=[
            RuleCondition(
                condition_type=RuleConditionType.SUBJECT_CONTAINS,
                value="newsletter"
            )
        ],
        actions=[
            RuleAction(
                action_type=RuleActionType.ADD_LABEL,
                value="Newsletter"
            ),
            RuleAction(
                action_type=RuleActionType.MARK_AS_READ,
                value=True
            )
        ]
    ),
    "important_sender": EmailRule(
        name="Important Sender",
        description="Star emails from important sender",
        conditions=[
            RuleCondition(
                condition_type=RuleConditionType.FROM_CONTAINS,
                value="boss@company.com"
            )
        ],
        actions=[
            RuleAction(
                action_type=RuleActionType.MARK_AS_STARRED,
                value=True
            ),
            RuleAction(
                action_type=RuleActionType.SET_CATEGORY,
                value="Important"
            )
        ]
    )
}
