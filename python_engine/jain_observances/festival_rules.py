# jain_festival_rules.py - Data-driven and OOP rule registry for Jain festivals.

from datetime import timedelta
from typing import List, Dict, Any
from datetime import date
from .registry import FESTIVAL_REGISTRY

class FestivalRule:
    """Base class for all festival rules."""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.id = config.get("id")
        self.name = config.get("name")
        self.name_hindi = config.get("name_hindi", "")
        self.category = config.get("category", "")
        self.profiles = config.get("profiles", [])
        self.meaning = config.get("meaning", "")
        self.observance = config.get("observance", "")
        self.sources = config.get("sources", [])
        self.jain_month = config.get("jain_month")
        self.paksha = config.get("paksha")
        self.tithi = config.get("tithi")
        self.vriddhi_rule = config.get("vriddhi_rule")
        self.kshaya_rule = config.get("kshaya_rule")
        self.adhika_rule = config.get("adhika_rule")

    def matches_profile(self, profile: str) -> bool:
        return profile in self.profiles or "all" in self.profiles

    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Resolve this rule into a list of occurrence dictionaries."""
        raise NotImplementedError

    def _create_occurrence(self, start_date: date, end_date: date, tithi: Any, month: str, paksha: str, profile: str) -> Dict[str, Any]:
        return {
            "id": self.id,
            "occurrence_id": f"{self.id}:{start_date.isoformat()}",
            "name": self.name,
            "name_hindi": self.name_hindi,
            "category": self.category,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "jain_month": month,
            "paksha": paksha,
            "tithi": tithi,
            "profile": profile,
            "status": "confirmed",
            "meaning": self.meaning,
            "observance": self.observance,
            "sources": self.sources
        }

class SingleTithiFestival(FestivalRule):
    """Festival occurring on a specific single Tithi, supporting Vriddhi and Kshaya."""
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        matches = snapshots
        if self.jain_month:
            matches = [s for s in matches if s["hindu_month"] == self.jain_month and not s["is_adhika"]]
        if self.paksha:
            matches = [s for s in matches if s["paksha"] == self.paksha]
            
        occurrences = []
        if isinstance(self.tithi, int):
            if self.jain_month:
                # Single annual occurrence
                candidates = [s for s in matches if s["tithi_in_paksha"] == self.tithi]
                if candidates:
                    if self.category == "parva":
                        for cand in candidates:
                            occurrences.append(self._create_occurrence(cand["date"], cand["date"], self.tithi, self.jain_month, self.paksha, profile))
                    else:
                        resolved_day = candidates[1]["date"] if len(candidates) > 1 and self.vriddhi_rule == "second_day" else candidates[0]["date"]
                        occurrences.append(self._create_occurrence(resolved_day, resolved_day, self.tithi, self.jain_month, self.paksha, profile))
                else:
                    # Kshaya
                    next_days = [s for s in matches if s["tithi_in_paksha"] > self.tithi]
                    if next_days:
                        resolved_day = next_days[0]["date"]
                        occurrences.append(self._create_occurrence(resolved_day, resolved_day, self.tithi, self.jain_month, self.paksha, profile))
            else:
                # Recurring monthly
                from itertools import groupby
                keyed = sorted(matches, key=lambda s: (s["hindu_month"], s["date"]))
                for _month_name, group_iter in groupby(keyed, key=lambda s: s["hindu_month"]):
                    group = list(group_iter)
                    candidates = [s for s in group if s["tithi_in_paksha"] == self.tithi]
                    if candidates:
                        if self.category == "parva":
                            for cand in candidates:
                                occurrences.append(self._create_occurrence(cand["date"], cand["date"], self.tithi, _month_name, self.paksha, profile))
                        else:
                            resolved_day = candidates[1]["date"] if len(candidates) > 1 and self.vriddhi_rule == "second_day" else candidates[0]["date"]
                            occurrences.append(self._create_occurrence(resolved_day, resolved_day, self.tithi, _month_name, self.paksha, profile))
                    else:
                        # Kshaya
                        next_days = [s for s in group if s["tithi_in_paksha"] > self.tithi]
                        if next_days:
                            resolved_day = next_days[0]["date"]
                            occurrences.append(self._create_occurrence(resolved_day, resolved_day, self.tithi, _month_name, self.paksha, profile))
        return occurrences

class MultiDayFestival(FestivalRule):
    """Festival spanning multiple consecutive days (e.g. Ayambil Oli)."""
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        duration_days = self.config.get("duration_days", 9)
        matches = [s for s in snapshots if s["hindu_month"] == self.jain_month and not s["is_adhika"] and s["paksha"] == self.paksha]
        
        start_tithi = int(self.tithi.split('-')[0]) if isinstance(self.tithi, str) and '-' in self.tithi else self.tithi
        
        candidates = [s for s in matches if s["tithi_in_paksha"] == start_tithi]
        resolved_day = None
        if candidates:
            resolved_day = candidates[0]["date"]
        else:
            # Kshaya
            next_days = [s for s in matches if s["tithi_in_paksha"] > start_tithi]
            if next_days:
                resolved_day = next_days[0]["date"]
                
        occurrences = []
        if resolved_day:
            end_date = resolved_day + timedelta(days=duration_days - 1)
            occurrences.append(self._create_occurrence(resolved_day, end_date, self.tithi, self.jain_month, self.paksha, profile))
        return occurrences

class RelativeFestival(FestivalRule):
    """Festival occurring at a fixed offset from another festival (e.g. Paryushan Start)."""
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        target_id = self.config.get("relative_to")
        offset_days = self.config.get("offset_days", 0)
        
        target_occurrences = context.get(target_id, [])
        occurrences = []
        for target_occ in target_occurrences:
            t_start = date.fromisoformat(target_occ["start_date"])
            new_start = t_start + timedelta(days=offset_days)
            occurrences.append(self._create_occurrence(
                new_start, t_start, self.tithi, self.jain_month, self.paksha, profile
            ))
        return occurrences

class RuleFactory:
    """Creates FestivalRule instances based on their config."""
    @staticmethod
    def create(config: Dict[str, Any]) -> FestivalRule:
        r_type = config.get("rule_type", "SingleTithi")
        if r_type == "SingleTithi":
            return SingleTithiFestival(config)
        elif r_type == "MultiDay":
            return MultiDayFestival(config)
        elif r_type == "Relative":
            return RelativeFestival(config)
        else:
            return FestivalRule(config)
