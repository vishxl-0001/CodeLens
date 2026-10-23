from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from typing import List, Dict, Type
from app.models import Issue, SeverityLevel, CategoryType


class BaseRule(ABC):
    rule_id: str
    title: str
    severity: SeverityLevel
    category: CategoryType
    why_it_matters: str
    suggestion: str
    reference: str = ""
    fixable: bool = False

    @abstractmethod
    def check(self, tree: ast.AST, source_code: str, source_lines: List[str]) -> List[Issue]:
        """Inspect the AST and source to return detected issues."""
        raise NotImplementedError

    def create_issue(
        self,
        message: str,
        line: int,
        column: int = 0,
        end_line: int | None = None,
        why_it_matters: str | None = None,
        suggestion: str | None = None,
        fixable: bool | None = None,
        reference: str | None = None,
    ) -> Issue:
        if end_line is None or end_line < line:
            end_line = line
        return Issue(
            id=f"{self.rule_id}-{line}-{column}",
            rule_id=self.rule_id,
            title=self.title,
            message=message,
            severity=self.severity,
            category=self.category,
            line=line,
            end_line=end_line,
            column=column,
            why_it_matters=why_it_matters or self.why_it_matters,
            suggestion=suggestion or self.suggestion,
            fixable=self.fixable if fixable is None else fixable,
            reference=reference or self.reference,
        )


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: Dict[str, BaseRule] = {}

    def register(self, rule_cls: Type[BaseRule]) -> Type[BaseRule]:
        rule = rule_cls()
        self._rules[rule.rule_id] = rule
        return rule_cls

    def get_all_rules(self) -> List[BaseRule]:
        return list(self._rules.values())

    def get_rule(self, rule_id: str) -> BaseRule | None:
        return self._rules.get(rule_id)


registry = RuleRegistry()
