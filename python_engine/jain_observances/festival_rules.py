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
        elif r_type == "RohiniVrat":
            return RohiniVratFestival(config)
        elif r_type == "BhaktambarVrat":
            return BhaktambarVratFestival(config)
        elif r_type == "DaslakshanVrat":
            return DaslakshanVratFestival(config)
        elif r_type == "RatnatrayaVrat":
            return RatnatrayaVratFestival(config)
        elif r_type == "AshtahnikaVrat":
            return AshtahnikaVratFestival(config)
        elif r_type == "ShodashkaranVrat":
            return ShodashkaranVratFestival(config)
        elif r_type == "RavivaraVrat":
            return RavivaraVratFestival(config)
        elif r_type == "KarmaNirjaraVrat":
            return KarmaNirjaraVratFestival(config)
        elif r_type == "RaviVrat":
            return RaviVratFestival(config)
        elif r_type == "NavpadOli":
            return NavpadOliFestival(config)
        elif r_type == "ChaitraShuklaEkamKalyanaks":
            return ChaitraShuklaEkamKalyanaksFestival(config)
        elif r_type == "PushpanjaliVrat":
            return PushpanjaliVratFestival(config)
        elif r_type == "AkshayaTritiya":
            return AkshayaTritiyaFestival(config)
        elif r_type == "MonthlyVrat":
            return MonthlyVratFestival(config)
        elif r_type == "DiwaliChaturmasNishthapan":
            return DiwaliChaturmasNishthapanFestival(config)
        else:
            return FestivalRule(config)


def get_greg_month(snapshots: List[Dict[str, Any]], h_name: str, paksha: str, target_tithi: int = 1) -> int:
    base_name = h_name.split("_")[0].upper()
    for s in snapshots:
        if s["hindu_month"].upper() == base_name and s["paksha"].upper() == paksha.upper() and not s["is_adhika"]:
            if s["tithi_in_paksha"] == target_tithi:
                return s["date"].month
    # Fallback to first day of paksha
    for s in snapshots:
        if s["hindu_month"].upper() == base_name and s["paksha"].upper() == paksha.upper() and not s["is_adhika"]:
            return s["date"].month
    return {"ASHADHA": 6, "KARTIKA": 10, "PHALGUNA": 2, "BHADRAPADA": 8, "MAGHA": 1, "CHAITRA": 3, "ASHVINA": 10, "SHRAVANA": 7}.get(base_name, 1)


class RohiniVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .vrats.rohini import evaluate_rohini_vrat, SwissEphPanchangProvider
        lat, lon = context["lat"], context["lon"]
        year = context["year"]
        ayanamsa = context.get("ayanamsa", "Lahiri")
        start_date_obj = date(year, 1, 1)
        end_date_obj = date(year, 12, 31)
        provider = SwissEphPanchangProvider(ayanamsa=ayanamsa)
        dates = evaluate_rohini_vrat(start_date_obj, end_date_obj, lat, lon, provider)
        occurrences = []
        for d in dates:
            d_str = d.strftime("%Y-%m-%d")
            occurrences.append({
                "id": self.id,
                "occurrence_id": self.id,
                "name": self.name,
                "name_hindi": self.name_hindi,
                "category": self.category,
                "start_date": d_str,
                "end_date": d_str,
                "status": "confirmed",
                "jain_month": "Nakshatra:",
                "paksha": "Rohini",
                "tithi": " ",
                "meaning": self.meaning,
                "observance": self.observance,
                "sources": self.sources
            })
        return occurrences


class BhaktambarVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .vrats.bhaktambar import calculate_bhaktambar_vrat, SwissEphTithiProvider
        lat, lon = context["lat"], context["lon"]
        year = context["year"]
        ayanamsa = context.get("ayanamsa", "Lahiri")
        tithi_provider = SwissEphTithiProvider(ayanamsa=ayanamsa)
        occurrences = []
        for m in range(1, 13):
            for p in ["SHUKLA", "KRISHNA"]:
                try:
                    vrat = calculate_bhaktambar_vrat(year, m, p, lat, lon, tithi_provider)
                    if vrat:
                        occurrences.append({
                            "id": f"bhaktambar_vrat_{year}_{m}_{p.lower()}",
                            "occurrence_id": f"bhaktambar_vrat_{year}_{m}_{p.lower()}",
                            "name": f"{p.capitalize()} Bhaktambar Vrat",
                            "name_hindi": self.name_hindi,
                            "category": self.category,
                            "start_date": vrat.start_date,
                            "end_date": vrat.end_date,
                            "status": "confirmed",
                            "duration_days": vrat.total_fasting_days,
                            "has_kshaya": vrat.has_kshaya,
                            "has_vriddhi": vrat.has_vriddhi,
                            "meaning": self.meaning,
                            "observance": self.observance,
                            "sources": self.sources
                        })
                except Exception:
                    pass
        return occurrences


class DaslakshanVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .vrats.daslakshan import calculate_daslakshan_vrat, SwissEphTithiProvider
        lat, lon = context["lat"], context["lon"]
        year = context["year"]
        ayanamsa = context.get("ayanamsa", "Lahiri")
        occurrences = []
        p_name = self.jain_month
        try:
            p_month = get_greg_month(snapshots, p_name, "Shukla", 5)
            vrat = calculate_daslakshan_vrat(year, p_month, p_name, lat, lon, SwissEphTithiProvider(ayanamsa))
            if vrat and hasattr(vrat, 'daily_schedule'):
                occurrences.append({
                    "id": f"daslakshan_{p_name}_{year}",
                    "occurrence_id": f"daslakshan_{p_name}_{year}",
                    "name": self.name,
                    "name_hindi": self.name_hindi,
                    "category": self.category,
                    "start_date": vrat.start_date,
                    "end_date": vrat.end_date,
                    "status": "confirmed",
                    "meaning": self.meaning,
                    "observance": self.observance,
                    "sources": self.sources,
                    "daily_schedule": [{"date": d.date, "virtue": d.virtue} for d in vrat.daily_schedule]
                })
        except Exception:
            pass
        return occurrences


class RatnatrayaVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .vrats.ratnatraya import calculate_ratnatraya_vrat, SwissEphTithiProvider
        lat, lon = context["lat"], context["lon"]
        year = context["year"]
        ayanamsa = context.get("ayanamsa", "Lahiri")
        occurrences = []
        p_name = self.jain_month
        try:
            p_month = get_greg_month(snapshots, p_name, "Shukla", 13)
            vrat = calculate_ratnatraya_vrat(year, p_month, p_name, lat, lon, SwissEphTithiProvider(ayanamsa))
            if vrat:
                occurrences.append({
                    "id": f"ratnatraya_{p_name}_{year}",
                    "occurrence_id": f"ratnatraya_{p_name}_{year}",
                    "name": f"Ratnatraya Vrat ({p_name})",
                    "name_hindi": self.name_hindi,
                    "category": self.category,
                    "start_date": vrat.fast_start_date,
                    "end_date": vrat.fast_end_date,
                    "status": "confirmed",
                    "meaning": self.meaning,
                    "observance": self.observance,
                    "sources": self.sources
                })
        except Exception:
            pass
        return occurrences


class AshtahnikaVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        target_month = self.jain_month # e.g. "ASHADHA", "KARTIKA", "PHALGUNA"
        
        # Season Filter: Month IN [Ashadha, Kartika, Phalguna]
        season_months = ["ASHADHA", "KARTIKA", "PHALGUNA"]
        if not target_month or target_month.upper() not in season_months:
            return []

        # Find snapshots of the target month in the target year
        month_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() == target_month.upper()
        ]
        
        if not month_snaps:
            return []

        # Adhik Maas Rule:
        # - If Ashadha, Kartika, or Phalguna repeats (Nija vs. Adhik), 
        #   DO NOT execute during Nija (regular) month. 
        #   Execute Ashtahnika Mahaparv ONLY during Adhik Maas.
        has_adhik_month_in_year = any(s["is_adhika"] for s in month_snaps)
        if has_adhik_month_in_year:
            # Keep only Adhik days, skip Nija
            month_snaps = [s for s in month_snaps if s["is_adhika"]]
        else:
            # Keep Nija
            month_snaps = [s for s in month_snaps if not s["is_adhika"]]

        # Map active Tithis in Shukla 7..15 for each day using morning window logic
        # Shukla Saptami (7) is included for potential Kshaya shift
        tithi_dates = {t: [] for t in range(7, 16)}
        for s in month_snaps:
            # In Amanta, Shukla Paksha corresponds to Tithis 1 to 15.
            # Morning window is sunrise to sunrise + 144 mins (0.1 days)
            for t in range(7, 16):
                if s["tithi"] == t or s["jain_tithi"] == t:
                    tithi_dates[t].append(s["date"])

        # Determine skipped and repeated Tithis in the base range 8..15
        skipped_tithis = [t for t in range(8, 16) if not tithi_dates[t]]
        repeated_tithis = [t for t in range(8, 16) if len(tithi_dates[t]) > 1]

        # Standard range 8..15 active dates
        active_dates = sorted(list({d for t in range(8, 16) for d in tithi_dates[t]}))
        if not active_dates:
            return []

        # Anomaly logic:
        # - Only Kshaya: Shift start date back to Shukla Saptami (7) to guarantee 8-day span.
        # - Only Vriddhi: Span naturally extends to 9 days.
        # - Both Kshaya & Vriddhi: Maintain standard 8-day span (net change zero).
        has_only_kshaya = len(skipped_tithis) > 0 and len(repeated_tithis) == 0

        if has_only_kshaya:
            if tithi_dates[7]:
                start_date = tithi_dates[7][0]
            else:
                start_date = active_dates[0] - timedelta(days=1)
            end_date = active_dates[-1]
        else:
            # Standard or Both or Only Vriddhi
            # Ashtami repeats -> starts on 1st Ashtami (active_dates[0])
            # Purnima repeats -> ends on 2nd Purnima (active_dates[-1])
            start_date = active_dates[0]
            end_date = active_dates[-1]

        # Format output schema
        # prefix for Adhik month name if applicable
        if has_adhik_month_in_year:
            prefix = "Adhik "
        else:
            prefix = ""
        month_title = prefix + target_month.capitalize()
        title = f"Ashtahnika Mahaparv ({month_title})"

        # MM_DD formatting
        start_mm_dd = start_date.strftime("%m-%d")
        end_mm_dd = end_date.strftime("%m-%d")
        span_label = f"Span: {start_mm_dd} – {end_mm_dd}" # Using correct en-dash '–'

        occurrences = [{
            "id": f"ashtahnika_{target_month.lower()}_{year}",
            "occurrence_id": f"ashtahnika_{target_month.lower()}_{year}",
            "name": title,
            "title": title,
            "name_hindi": self.name_hindi or title,
            "category": "mahaparv",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "status": "confirmed",
            "badge": "Mahaparv",
            "badge_color": "blue",
            "is_span": True,
            "span_label": span_label,
            "meaning": self.meaning or "An 8-day Jain festival of fasting and worship.",
            "observance": self.observance or "Special pujas, fasting, and reading scriptures.",
            "sources": self.sources or ["Jain Traditions"]
        }]
        return occurrences


class ShodashkaranVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .vrats.shodashkaran import calculate_shodashkaran_vrat, SwissEphTithiProvider
        lat, lon = context["lat"], context["lon"]
        year = context["year"]
        ayanamsa = context.get("ayanamsa", "Lahiri")
        occurrences = []
        p_name = self.jain_month
        shodashkaran_amanta_starts = {
            "BHADRAPADA_ASHVINA": "ASHADHA",
            "MAGHA_PHALGUNA": "PAUSHA",
            "CHAITRA_VAISHAKHA": "PHALGUNA"
        }
        try:
            amanta_start = shodashkaran_amanta_starts[p_name]
            p_month = get_greg_month(snapshots, amanta_start, "Krishna", 1)
            vrat = calculate_shodashkaran_vrat(year, p_month, p_name, lat, lon, SwissEphTithiProvider(ayanamsa))
            if vrat:
                occurrences.append({
                    "id": f"shodashkaran_{p_name}_{year}",
                    "occurrence_id": f"shodashkaran_{p_name}_{year}",
                    "name": f"Shodashkaran Vrat ({p_name})",
                    "name_hindi": self.name_hindi,
                    "category": self.category,
                    "start_date": vrat.start_date,
                    "end_date": vrat.end_date,
                    "status": "confirmed",
                    "meaning": self.meaning,
                    "observance": self.observance,
                    "sources": self.sources
                })
        except Exception:
            pass
        return occurrences


class RavivaraVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        from .vrats.ravivara import calculate_ravivara_vrat, SwissEphTithiProvider
        lat, lon = context["lat"], context["lon"]
        year = context["year"]
        ayanamsa = context.get("ayanamsa", "Lahiri")
        occurrences = []
        try:
            vrat = calculate_ravivara_vrat(year, lat, lon, SwissEphTithiProvider(ayanamsa))
            if vrat:
                occurrences.append({
                    "id": f"ravivara_{year}",
                    "occurrence_id": f"ravivara_{year}",
                    "name": self.name,
                    "name_hindi": self.name_hindi,
                    "category": self.category,
                    "start_date": vrat.start_date,
                    "end_date": vrat.end_date,
                    "status": "confirmed",
                    "meaning": self.meaning,
                    "observance": self.observance,
                    "sources": self.sources
                })
        except Exception:
            pass
        return occurrences


class KarmaNirjaraVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        target_month = self.jain_month # e.g. "ASHADHA", "SHRAVANA", "BHADRAPADA", "ASHVINA"
        
        # Season Filter: Month IN [Ashadha, Shravana, Bhadrapada, Ashvina]
        season_months = ["ASHADHA", "SHRAVANA", "BHADRAPADA", "ASHVINA", "ASHWIN"]
        if not target_month or target_month.upper() not in season_months:
            return []

        # Find snapshots of the target month in the target year
        target_months_set = {target_month.upper()}
        if target_month.upper() in ["ASHVINA", "ASHWIN"]:
            target_months_set.add("ASHVINA")
            target_months_set.add("ASHWIN")

        month_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in target_months_set
        ]
        
        if not month_snaps:
            return []

        # Adhik Maas Rules:
        # - If Ashadha repeats (Nija Ashadha & Adhik Ashadha):
        #   * SKIP Nija Ashadha.
        #   * Execute Vrat starting ONLY from Adhik Ashadha.
        # - For all other Chaumasa months (Shravana, Bhadrapada, Ashvina):
        #   * Execute Vrat in BOTH Nija and Adhik months if an intercalary month occurs.
        has_adhik_month_in_year = any(s["is_adhika"] for s in month_snaps)
        
        if target_month.upper() == "ASHADHA":
            if has_adhik_month_in_year:
                # Keep only Adhik days, skip Nija
                month_snaps = [s for s in month_snaps if s["is_adhika"]]
            else:
                # Keep Nija
                month_snaps = [s for s in month_snaps if not s["is_adhika"]]
        else:
            # Keep all (both Nija and Adhik)
            pass

        occurrences = []
        for s in month_snaps:
            # Evaluate morning window (sunrise to sunrise + 144 mins / 0.1 days)
            # Check if Shukla Chaturdashi (Tithi 14) is active during this window
            is_tithi_14_at_sunrise = (s["tithi"] == 14)
            is_tithi_14_at_cutoff = (s["jain_tithi"] == 14)
            
            if is_tithi_14_at_sunrise or is_tithi_14_at_cutoff:
                # Determine title with proper Adhik / Nija prefix
                if has_adhik_month_in_year:
                    prefix = "Adhik " if s["is_adhika"] else "Nija "
                else:
                    prefix = ""
                
                # Format to title case (e.g. "Ashadha" or "Adhik Ashadha")
                month_title = prefix + s["hindu_month"]
                title = f"Karma Nirjara Vrat ({month_title})"
                
                occurrences.append({
                    "id": f"{self.id}_{month_title.lower().replace(' ', '_')}_{year}",
                    "occurrence_id": f"{self.id}_{s['date'].isoformat()}",
                    "name": title,
                    "title": title,
                    "name_hindi": title,
                    "category": "parva_vrat",
                    "start_date": s["date"].isoformat(),
                    "end_date": s["date"].isoformat(),
                    "status": "confirmed",
                    "badge": "Parva / Vrat",
                    "badge_color": "purple",
                    "is_span": False,
                    "jain_month": month_title,
                    "paksha": "Shukla",
                    "tithi": "Chaturdashi (14)",
                    "meaning": self.meaning or "Vrat observing shedding of karmas via austerity.",
                    "observance": self.observance or "Fasting and meditation.",
                    "sources": self.sources or ["Digambar Jain Traditions"]
                })
        return occurrences


class NavpadOliFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        target_month = self.jain_month # e.g. "CHAITRA" or "ASHWIN"
        
        # Season Filter (Bi-annual): Month IN [Chaitra, Ashwin]
        season_months = ["CHAITRA", "ASHWIN", "ASHVINA"]
        if not target_month or target_month.upper() not in season_months:
            return []

        # Find snapshots of the target month in the target year
        target_months_set = {target_month.upper()}
        if target_month.upper() in ["ASHVINA", "ASHWIN"]:
            target_months_set.add("ASHVINA")
            target_months_set.add("ASHWIN")

        month_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in target_months_set
        ]
        
        if not month_snaps:
            return []

        # Adhik Maas Rule:
        # - If Chaitra or Ashwin repeats (Adhik vs. Nija):
        #   * Execute Navpad Oli strictly during Adhik Maas.
        #   * DO NOT execute during Nija Maas.
        has_adhik_month_in_year = any(s["is_adhika"] for s in month_snaps)
        if has_adhik_month_in_year:
            # Keep only Adhik days, skip Nija
            month_snaps = [s for s in month_snaps if s["is_adhika"]]
        else:
            # Keep Nija
            month_snaps = [s for s in month_snaps if not s["is_adhika"]]

        # Map active Tithis in Shukla 6..15 for each day using morning window logic
        # Shukla Shashthi (6) is included for potential Kshaya shift
        tithi_dates = {t: [] for t in range(6, 16)}
        for s in month_snaps:
            # Morning window is sunrise to sunrise + 144 mins (0.1 days)
            for t in range(6, 16):
                if s["tithi"] == t or s["jain_tithi"] == t:
                    tithi_dates[t].append(s["date"])

        # Determine skipped and repeated Tithis in the base range 7..15
        skipped_tithis = [t for t in range(7, 16) if not tithi_dates[t]]
        repeated_tithis = [t for t in range(7, 16) if len(tithi_dates[t]) > 1]

        # Standard range 7..15 active dates
        active_dates = sorted(list({d for t in range(7, 16) for d in tithi_dates[t]}))
        if not active_dates:
            return []

        # Anomaly logic:
        # - Only Kshaya: Shift start date back to Shukla Shashthi (6) to guarantee 9-day span.
        # - Only Vriddhi: Span naturally extends to 10 days.
        # - Both Kshaya & Vriddhi: Maintain standard 9-day span (net change zero).
        has_only_kshaya = len(skipped_tithis) > 0 and len(repeated_tithis) == 0

        if has_only_kshaya:
            if tithi_dates[6]:
                start_date = tithi_dates[6][0]
            else:
                start_date = active_dates[0] - timedelta(days=1)
            end_date = active_dates[-1]
        else:
            # Standard or Both or Only Vriddhi
            # Saptami repeats -> starts on 1st Saptami (active_dates[0])
            # Purnima repeats -> ends on 2nd Purnima (active_dates[-1])
            start_date = active_dates[0]
            end_date = active_dates[-1]

        # Generate dates list in the span
        vrat_dates = []
        curr = start_date
        while curr <= end_date:
            vrat_dates.append(curr)
            curr += timedelta(days=1)

        total_days = len(vrat_dates)
        
        # Build date to snap map for fast lookup
        date_to_snap = {s["date"].isoformat(): s for s in snapshots}

        # Sequential Pads mapping
        pads = [
            "Arihant", "Siddha", "Acharya", "Upadhyay", "Sadhu",
            "Samyag Darshan", "Samyag Gyan", "Samyag Charitra", "Samyag Tapa"
        ]

        pad_assignments = {}
        if total_days == 9:
            for i, d in enumerate(vrat_dates):
                pad_assignments[d] = (i + 1, pads[i])
        else:
            # total_days is 10 (Only Vriddhi)
            pad_idx = 0
            for i, d in enumerate(vrat_dates):
                if i == 0:
                    pad_assignments[d] = (1, pads[0])
                else:
                    prev_d = vrat_dates[i - 1]
                    snap_d = date_to_snap[d.isoformat()]
                    snap_prev = date_to_snap[prev_d.isoformat()]
                    is_repeat = (snap_d["tithi"] == snap_prev["tithi"] or snap_d["jain_tithi"] == snap_prev["jain_tithi"])
                    if is_repeat:
                        pad_assignments[d] = (pad_idx + 1, pads[pad_idx])
                    else:
                        pad_idx += 1
                        if pad_idx < len(pads):
                            pad_assignments[d] = (pad_idx + 1, pads[pad_idx])
                        else:
                            pad_assignments[d] = (9, pads[-1])

        # Overall span formatted as MM-DD
        start_mm_dd = start_date.strftime("%m-%d")
        end_mm_dd = end_date.strftime("%m-%d")
        span_label = f"Span: {start_mm_dd} – {end_mm_dd}" # Using correct en-dash '–'

        occurrences = []
        for d in vrat_dates:
            day_num, pad_name = pad_assignments[d]
            title = f"Navpad Oli - Day {day_num} ({pad_name})"
            occurrences.append({
                "id": f"{self.id}_{d.isoformat()}",
                "occurrence_id": f"{self.id}_{d.isoformat()}",
                "name": title,
                "title": title,
                "name_hindi": title,
                "category": "mahaparv",
                "start_date": d.isoformat(),
                "end_date": d.isoformat(),
                "status": "confirmed",
                "badge": "Navpad Oli",
                "badge_color": "gold",
                "is_span": True,
                "span_label": span_label,
                "meaning": self.meaning or f"Day {day_num} of Navpad Ayambil Oli fast, meditating on {pad_name}.",
                "observance": self.observance or f"Ayambil fast, meditating on {pad_name}.",
                "sources": self.sources or ["Jain Traditions"]
            })
            
        return occurrences


class ChaitraShuklaEkamKalyanaksFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        
        # Season Filter: Month == Chaitra
        month_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() == "CHAITRA"
        ]
        
        if not month_snaps:
            return []

        # Adhik Maas Rule:
        # - Exclusion of Adhik Chaitra (execute strictly during Nija Chaitra)
        month_snaps = [s for s in month_snaps if not s["is_adhika"]]
        
        if not month_snaps:
            return []

        # Evaluate morning window (sunrise to sunrise + 144 mins / 0.1 days)
        # to find days where Shukla Ekam (1) is active
        ekam_days = []
        for s in month_snaps:
            if s["paksha"] == "Shukla" and (s["tithi"] == 1 or s["jain_tithi"] == 1):
                ekam_days.append(s)

        target_snap = None
        if ekam_days:
            # Normal or Vriddhi (Repeated Ekam)
            # If repeated, assign Kalyanaks to 1st Ekam, 2nd instance is marked as continuation (skipped here)
            target_snap = ekam_days[0]
        else:
            # Kshaya Tithi (Skipped Ekam)
            # Find the day before Chaitra Shukla Dwitiya (2) at sunrise.
            # This corresponds to Chaitra Krishna Amavasya (15) or the sunrise moment when Ekam prevails dynamically.
            dwitiya_days = [
                s for s in month_snaps
                if s["paksha"] == "Shukla" and (s["tithi"] == 2 or s["jain_tithi"] == 2)
            ]
            if dwitiya_days:
                first_dwitiya = dwitiya_days[0]
                idx = snapshots.index(first_dwitiya)
                if idx > 0:
                    target_snap = snapshots[idx - 1]

        if not target_snap:
            return []

        # Output schema fields based on self.id
        occurrences = []
        
        if self.id == "gautam_swami_janam_divas":
            occurrences.append({
                "id": f"{self.id}_{year}",
                "occurrence_id": f"{self.id}_{year}",
                "name": "Gautam Swami Janam Divas",
                "title": "Gautam Swami Janam Divas",
                "name_hindi": "गौतम स्वामी जन्म दिवस",
                "category": "janam_kalyanak",
                "badge": "Janam Kalyan",
                "badge_color": "green",
                "start_date": target_snap["date"].isoformat(),
                "end_date": target_snap["date"].isoformat(),
                "status": "confirmed",
                "description": "Birth anniversary of Gandhar Gautam Swami",
                "meaning": self.meaning or "Birth anniversary of Gandhar Gautam Swami",
                "observance": self.observance or "Special prayers and reading of scriptures",
                "sources": self.sources or ["Jain Traditions"]
            })
        elif self.id == "shri_mallinath_ji___garbh":
            occurrences.append({
                "id": f"{self.id}_{year}",
                "occurrence_id": f"{self.id}_{year}",
                "name": "Shri Mallinath Bhagwan Garbha Kalyanak",
                "title": "Shri Mallinath Bhagwan Garbha Kalyanak",
                "name_hindi": "श्री मल्लिनाथ भगवान गर्भ कल्याणक",
                "category": "garbha_kalyanak",
                "badge": "Garbha Kalyan",
                "badge_color": "saffron",
                "start_date": target_snap["date"].isoformat(),
                "end_date": target_snap["date"].isoformat(),
                "status": "confirmed",
                "description": "Garbha Kalyanak of 19th Tirthankara Shri Mallinath Bhagwan",
                "meaning": self.meaning or "Garbha Kalyanak of 19th Tirthankara Shri Mallinath Bhagwan",
                "observance": self.observance or "Special prayers and reading of scriptures",
                "sources": self.sources or ["Jain Traditions"]
            })
            
        return occurrences


class PushpanjaliVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        target_month = self.jain_month # e.g. "CHAITRA", "BHADRAPADA", "MAGHA"
        
        # Season Filter: Month IN [Chaitra, Bhadrapada, Magha]
        season_months = ["CHAITRA", "BHADRAPADA", "MAGHA"]
        if not target_month or target_month.upper() not in season_months:
            return []

        # Find snapshots of the target month in the target year
        month_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() == target_month.upper()
        ]
        
        if not month_snaps:
            return []

        # Adhik Maas Rule:
        # - If Chaitra, Bhadrapada, or Magha repeats (Adhik vs. Nija):
        #   * EXECUTE Pushpanjali Vrat strictly during ADHIK MAAS.
        #   * DO NOT execute during Nija MAAS.
        has_adhik_month_in_year = any(s["is_adhika"] for s in month_snaps)
        if has_adhik_month_in_year:
            # Keep only Adhik days, skip Nija
            month_snaps = [s for s in month_snaps if s["is_adhika"]]
        else:
            # Keep Nija
            month_snaps = [s for s in month_snaps if not s["is_adhika"]]

        # Map active Tithis in Shukla 4..9 for each day using morning window logic
        # Shukla Chaturthi (4) is included for potential Kshaya shift
        tithi_dates = {t: [] for t in range(4, 10)}
        for s in month_snaps:
            if s["paksha"] == "Shukla":
                for t in range(4, 10):
                    if s["tithi"] == t or s["jain_tithi"] == t:
                        tithi_dates[t].append(s["date"])

        # Determine skipped and repeated Tithis in the base range 5..9
        skipped_tithis = [t for t in range(5, 10) if not tithi_dates[t]]
        repeated_tithis = [t for t in range(5, 10) if len(tithi_dates[t]) > 1]

        # Standard range 5..9 active dates
        active_dates = sorted(list({d for t in range(5, 10) for d in tithi_dates[t]}))
        if not active_dates:
            return []

        # Anomaly logic:
        # - Only Kshaya: Shift start date back to Shukla Chaturthi (4) to preserve 5-day span.
        # - Only Vriddhi: Span naturally extends to 6 days.
        # - Both Kshaya & Vriddhi: Maintain standard 5-day span (net change zero).
        has_only_kshaya = len(skipped_tithis) > 0 and len(repeated_tithis) == 0

        if has_only_kshaya:
            if tithi_dates[4]:
                start_date = tithi_dates[4][0]
            else:
                start_date = active_dates[0] - timedelta(days=1)
            end_date = active_dates[-1]
        else:
            # Standard or Both or Only Vriddhi
            # Panchami repeats -> starts on 1st Panchami (active_dates[0])
            # Navami repeats -> ends on 2nd Navami (active_dates[-1])
            start_date = active_dates[0]
            end_date = active_dates[-1]

        # Generate dates list in the span
        vrat_dates = []
        curr = start_date
        while curr <= end_date:
            vrat_dates.append(curr)
            curr += timedelta(days=1)

        start_mm_dd = start_date.strftime("%m-%d")
        end_mm_dd = end_date.strftime("%m-%d")
        span_label = f"Span: {start_mm_dd} – {end_mm_dd}" # Using correct en-dash '–'

        occurrences = []
        for idx, d in enumerate(vrat_dates):
            day_num = idx + 1
            title = f"Pushpanjali Vrat - Day {day_num}"
            occurrences.append({
                "id": f"{self.id}_{d.isoformat()}",
                "occurrence_id": f"{self.id}_{d.isoformat()}",
                "name": title,
                "title": title,
                "name_hindi": f"पुष्पांजलि व्रत - दिन {day_num}",
                "category": "vrat",
                "start_date": d.isoformat(),
                "end_date": d.isoformat(),
                "status": "confirmed",
                "badge": "Pushpanjali Vrat",
                "badge_color": "rose",
                "is_span": True,
                "span_label": span_label,
                "meaning": self.meaning or f"Day {day_num} of Pushpanjali Vrat dedicated to worshiping Siddhas and Tirthankaras.",
                "observance": self.observance or "Fasting, flower offerings and meditation.",
                "sources": self.sources or ["Jain Traditions"]
            })
            
        return occurrences


class AkshayaTritiyaFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        target_month = self.jain_month # e.g. "Vaishakha"
        
        # Season Filter: Month == Vaishakha
        month_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["VAISHAKHA", "VAISAKH", "BAISAKH"]
        ]
        
        if not month_snaps:
            return []

        # Adhik Maas Rule:
        # - If Vaishakha repeats (Adhik Vaishakha vs. Nija Vaishakha):
        #   * EXECUTE STRICTLY during Adhik Vaishakha (the intercalary month).
        #   * DO NOT execute during Nija Vaishakha.
        has_adhik_month_in_year = any(s["is_adhika"] for s in month_snaps)
        if has_adhik_month_in_year:
            # Keep only Adhik days, skip Nija
            month_snaps = [s for s in month_snaps if s["is_adhika"]]
        else:
            # Keep Nija
            month_snaps = [s for s in month_snaps if not s["is_adhika"]]

        # Evaluate morning window to find active Shukla Dwitiya (2) and Tritiya (3)
        tritiya_days = []
        dwitiya_days = []
        for s in month_snaps:
            if s["paksha"] == "Shukla":
                if s["tithi"] == 3 or s["jain_tithi"] == 3:
                    tritiya_days.append(s)
                if s["tithi"] == 2 or s["jain_tithi"] == 2:
                    dwitiya_days.append(s)

        target_snap = None
        if tritiya_days:
            # Normal or Vriddhi (Repeated Tritiya)
            # If Tritiya repeats, assign primary observance to the 1st Tritiya
            target_snap = tritiya_days[0]
        else:
            # Kshaya Tithi (Skipped Tritiya)
            # Trigger event on Vaishakha Shukla Dwitiya (2) when Tritiya prevailing window is active
            # (which is the last Dwitiya day, right before Chaturthi)
            if dwitiya_days:
                target_snap = dwitiya_days[-1]

        if not target_snap:
            return []

        occurrences = [{
            "id": f"{self.id}_{year}",
            "occurrence_id": f"{self.id}_{year}",
            "name": "Akshaya Tritiya (Dan Divas)",
            "title": "Akshaya Tritiya (Dan Divas)",
            "name_hindi": "अक्षय तृतीया (दान दिवस)",
            "category": "mahaparv",
            "badge": "Akshaya Tritiya",
            "badge_color": "gold",
            "start_date": target_snap["date"].isoformat(),
            "end_date": target_snap["date"].isoformat(),
            "status": "confirmed",
            "description": "First Ahar Dan to Bhagwan Rishabhdev & Varshi Tapa Parana",
            "meaning": self.meaning or "First Ahar Dan to Bhagwan Rishabhdev & Varshi Tapa Parana",
            "observance": self.observance or "Offering of sugarcane juice, charity, and prayers.",
            "sources": self.sources or ["Jain Traditions"]
        }]
        
        return occurrences


class MonthlyVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        target_month = self.jain_month # e.g. "Jyeshtha"
        
        # Season Filter: Month == Jyeshtha
        month_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["JYESTHA", "JYESHTHA", "JETH"]
        ]
        
        if not month_snaps:
            return []

        # Adhik Maas Rule:
        # - If Jyeshtha repeats (Adhik Jyeshtha vs. Nija Jyeshtha):
        #   * EXECUTE STRICTLY during Adhik Maas.
        #   * DO NOT execute during Nija Maas.
        has_adhik_month_in_year = any(s["is_adhika"] for s in month_snaps)
        if has_adhik_month_in_year:
            # Keep only Adhik days, skip Nija
            month_snaps = [s for s in month_snaps if s["is_adhika"]]
        else:
            # Keep Nija
            month_snaps = [s for s in month_snaps if not s["is_adhika"]]

        if not month_snaps:
            return []

        # Evaluate morning window to find active Krishna Ekam (1)
        krishna_ekam_days = []
        for s in month_snaps:
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 1:
                krishna_ekam_days.append(s)

        start_snap = None
        if krishna_ekam_days:
            # Vriddhi (Repeated Ekam): Tag the 1st Ekam
            start_snap = krishna_ekam_days[0]
        else:
            # Kshaya (Skipped Ekam): Tag the preceding Amavasya day
            first_day = sorted(month_snaps, key=lambda x: x["date"])[0]
            idx = snapshots.index(first_day)
            if idx > 0:
                start_snap = snapshots[idx - 1]
            else:
                start_snap = first_day

        # Evaluate morning window to find active Shukla Purnima (15)
        purnima_days = []
        for s in month_snaps:
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 15:
                purnima_days.append(s)

        end_snap = None
        if purnima_days:
            # Vriddhi (Repeated Purnima): Tag the 2nd Purnima
            end_snap = purnima_days[-1]
        else:
            # Kshaya (Skipped Purnima): Tag Shukla Chaturdashi (14)
            chaturdashi_days = []
            for s in month_snaps:
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 14:
                    chaturdashi_days.append(s)
            if chaturdashi_days:
                end_snap = chaturdashi_days[-1]

        occurrences = []
        
        # Start occurrence
        if start_snap:
            occurrences.append({
                "id": f"{self.id}_start_{year}",
                "occurrence_id": f"{self.id}_start_{year}",
                "name": f"{self.name} - Start",
                "title": f"{self.name} - Start",
                "name_hindi": f"{self.name_hindi} - प्रारंभ",
                "category": "monthly_vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": start_snap["date"].isoformat(),
                "end_date": start_snap["date"].isoformat(),
                "status": "confirmed",
                "is_boundary": True,
                "boundary_type": "START",
                "meaning": self.meaning or f"Start of {self.name} monthly vrat cycle.",
                "observance": self.observance or "Boundary marker.",
                "sources": self.sources or ["Jain Traditions"]
            })

        # Conclusion occurrence
        if end_snap:
            occurrences.append({
                "id": f"{self.id}_end_{year}",
                "occurrence_id": f"{self.id}_end_{year}",
                "name": f"{self.name} - Conclusion",
                "title": f"{self.name} - Conclusion",
                "name_hindi": f"{self.name_hindi} - समापन",
                "category": "monthly_vrat",
                "badge": "Vrat End",
                "badge_color": "pink",
                "start_date": end_snap["date"].isoformat(),
                "end_date": end_snap["date"].isoformat(),
                "status": "confirmed",
                "is_boundary": True,
                "boundary_type": "END",
                "meaning": self.meaning or f"Conclusion of {self.name} monthly vrat cycle.",
                "observance": self.observance or "Boundary marker.",
                "sources": self.sources or ["Jain Traditions"]
            })

        return occurrences


class DiwaliChaturmasNishthapanFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        target_month = self.jain_month # e.g. "Kartik" or "Kartika"
        
        # Season Filter: Month == Kartika
        month_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["KARTIK", "KARTIKA"]
        ]
        
        if not month_snaps:
            return []

        # Adhik Maas Rule:
        # - If Kartika repeats (Adhik Kartika vs. Nija Kartika):
        #   * EXECUTE STRICTLY during Adhik Kartika (the intercalary month).
        #   * DO NOT execute during Nija Kartika.
        has_adhik_month_in_year = any(s["is_adhika"] for s in month_snaps)
        if has_adhik_month_in_year:
            # Keep only Adhik days, skip Nija
            month_snaps = [s for s in month_snaps if s["is_adhika"]]
        else:
            # Keep Nija
            month_snaps = [s for s in month_snaps if not s["is_adhika"]]

        # Evaluate morning window to find active Krishna Chaturdashi (14) and Amavasya (15)
        amavasya_days = []
        chaturdashi_days = []
        for s in month_snaps:
            if s["paksha"] == "Krishna":
                if s["tithi_in_paksha"] == 15:
                    amavasya_days.append(s)
                if s["tithi_in_paksha"] == 14:
                    chaturdashi_days.append(s)

        target_snap = None
        if amavasya_days:
            # Normal or Vriddhi (Repeated Amavasya)
            # If Amavasya repeats, assign strictly to the 2nd Amavasya (last instance)
            target_snap = amavasya_days[-1]
        else:
            # Kshaya Tithi (Skipped Amavasya)
            # Trigger event on Kartika Krishna Chaturdashi (14) during active Amavasya prevailing window
            # (which is the last Chaturdashi day)
            if chaturdashi_days:
                target_snap = chaturdashi_days[-1]

        if not target_snap:
            return []

        occurrences = [
            {
                "id": f"{self.id}_{year}",
                "occurrence_id": f"{self.id}_{year}",
                "name": "Diwali (Bhagwan Mahavir Nirvan Kalyanak)",
                "title": "Diwali (Bhagwan Mahavir Nirvan Kalyanak)",
                "name_hindi": "दीपावली (भगवान महावीर निर्वाण)",
                "category": "mahaparv",
                "badge": "Diwali",
                "badge_color": "pink",
                "start_date": target_snap["date"].isoformat(),
                "end_date": target_snap["date"].isoformat(),
                "status": "confirmed",
                "description": "Nirvan Kalyanak of 24th Tirthankara Bhagwan Mahavir",
                "meaning": self.meaning or "Nirvan Kalyanak of 24th Tirthankara Bhagwan Mahavir",
                "observance": self.observance or "Laddoo offering & Swadhyay",
                "sources": self.sources or ["Jain Traditions"]
            },
            {
                "id": f"chaturmas_nishthapan_{year}",
                "occurrence_id": f"chaturmas_nishthapan_{year}",
                "name": "Chaturmas Nishthapan",
                "title": "Chaturmas Nishthapan",
                "name_hindi": "चातुर्मास निष्ठापन",
                "category": "mahaparv",
                "badge": "Chaturmas End",
                "badge_color": "pink",
                "start_date": target_snap["date"].isoformat(),
                "end_date": target_snap["date"].isoformat(),
                "status": "confirmed",
                "description": "Formal conclusion and completion of holy Chaturmas",
                "meaning": "Formal conclusion and completion of holy Chaturmas",
                "observance": "Special prayers and conclusion of monsoon stay",
                "sources": ["Jain Traditions"]
            }
        ]
        
        return occurrences


class RaviVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        
        # 1. Find all Sundays in Ashadha Shukla Paksha of the target year that are not Adhika
        ashadha_shukla_sundays = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"] == "Ashadha"
            and not s["is_adhika"]
            and s["paksha"] == "Shukla"
            and s["date"].weekday() == 6
        ]

        if not ashadha_shukla_sundays:
            return []

        # 2. Start on the last Sunday of Ashadha Shukla Paksha
        start_date = ashadha_shukla_sundays[-1]["date"]

        # 3. Generate the 9 consecutive Sundays
        vrat_dates = [start_date + timedelta(days=i * 7) for i in range(9)]

        # 4. Map vrat_dates back to snapshots for astronomical details
        date_to_snap = {s["date"]: s for s in snapshots}
        vrat_days = []
        for d in vrat_dates:
            snap = date_to_snap.get(d)
            if snap:
                vrat_days.append(snap)

        occurrences = []
        from panchang import get_tithi_at_jd, get_nakshatra_at_jd
        ayanamsa = context.get("ayanamsa", "Lahiri")

        for d in vrat_days:
            sunrise_jd = d["sunrise_jd"]
            # 144 minutes is exactly 0.1 days
            cutoff_jd = sunrise_jd + 0.1

            t_sunrise = get_tithi_at_jd(sunrise_jd, ayanamsa)
            t_cutoff = get_tithi_at_jd(cutoff_jd, ayanamsa)

            nak_sunrise = get_nakshatra_at_jd(sunrise_jd, ayanamsa)
            nak_cutoff = get_nakshatra_at_jd(cutoff_jd, ayanamsa)

            is_saptami = (t_sunrise % 15 == 7) or (t_cutoff % 15 == 7)
            is_pushya = (nak_sunrise == 8) or (nak_cutoff == 8)

            if is_pushya:
                title = "☀️ Ravi Pushya Vrat"
            elif is_saptami:
                title = "☀️ Ravi Saptami Vrat"
            else:
                title = "☀️ Ravi Vrat"

            occurrences.append({
                "id": self.id,
                "occurrence_id": f"{self.id}_{d['date'].isoformat()}",
                "name": title,
                "title": title,
                "name_hindi": title,
                "category": self.category,
                "start_date": d["date"].isoformat(),
                "end_date": d["date"].isoformat(),
                "status": "confirmed",
                "badge": self.config.get("badge", "Parva / Vrat"),
                "badge_color": self.config.get("badge_color", "purple"),
                "is_span": False,
                "jain_month": d["hindu_month"],
                "paksha": d["paksha"],
                "tithi": d["tithi"],
                "meaning": "Sunday fasting dedicated to Surya/Sun.",
                "observance": "Fast starts at sunrise, single saltless meal in afternoon.",
                "sources": ["Jain/Vedic Traditions"]
            })

        return occurrences
