# jain_festival_rules.py - Data-driven and OOP rule registry for Jain festivals.

from datetime import timedelta

def get_jain_month(s: Dict[str, Any]) -> str:
    m_names = [
        "CHAITRA", "VAISHAKHA", "JYESHTHA", "ASHADHA", "SHRAVANA", "BHADRAPADA",
        "ASHVINA", "KARTIKA", "MARGASHIRSHA", "PAUSHA", "MAGHA", "PHALGUNA"
    ]
    base_month = s["hindu_month"].upper()
    if base_month == "ASHWIN":
        base_month = "ASHVINA"
    if s["paksha"] == "Krishna":
        if base_month in m_names:
            idx = m_names.index(base_month)
            base_month = m_names[(idx + 1) % 12]
    return base_month
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
        elif r_type == "VeerShasanJayanti":
            return VeerShasanJayantiShrut(config)
        elif r_type == "SaptaRishiVrat":
            return SaptaRishiVratFestival(config)
        elif r_type == "SaptaParamsthanVrat":
            return SaptaParamsthanVratFestival(config)
        elif r_type == "RakshabandhanVrat":
            return RakshabandhanVratFestival(config)
        elif r_type == "ShravanaPurnimaRakshabandhan":
            return ShravanaPurnimaRakshabandhanFestival(config)
        elif r_type == "BhadrapadaKrishnaEkamMultiVrat":
            return BhadrapadaKrishnaEkamMultiVratFestival(config)
        elif r_type == "TeenChaubisiVrat":
            return TeenChaubisiVratFestival(config)
        elif r_type == "AkshayaNidhiVrat":
            return AkshayaNidhiVratFestival(config)
        elif r_type == "ShvetambaraParyushan50Day":
            return ShvetambaraParyushan50DayFestival(config)
        elif r_type == "BhayaHaranVrat":
            return BhayaHaranVratFestival(config)
        elif r_type == "ChaitraLabdhiVidhan":
            return ChaitraLabdhiVidhanFestival(config)
        elif r_type == "LabdhiVidhanVrat":
            return LabdhiVidhanVratFestival(config)
        elif r_type == "TalaDharTapShantisagarPunyatithi":
            return TalaDharTapShantisagarPunyatithiFestival(config)
        elif r_type == "BadiPanchamiMeruSthapana":
            return BadiPanchamiMeruSthapanaFestival(config)
        elif r_type == "NihshalyaAshtamiManchinTithi":
            return NihshalyaAshtamiManchinTithiFestival(config)
        elif r_type == "SugandhDashami":
            return SugandhDashamiFestival(config)
        elif r_type == "AnantChaturdashiVrat":
            return AnantChaturdashiVratFestival(config)
        elif r_type == "RatnatrayaSankatHaranVrat":
            return RatnatrayaSankatHaranVratFestival(config)
        elif r_type == "KshamavaniMahaparv":
            return KshamavaniMahaparvFestival(config)
        elif r_type == "ShraddhaVrat":
            return ShraddhaVratFestival(config)
        elif r_type == "NavapadOliVrat":
            return NavapadOliVratFestival(config)
        elif r_type == "JeevDayaAshtami":
            return JeevDayaAshtamiFestival(config)
        elif r_type == "SharadPurnimaJayantis":
            return SharadPurnimaJayantisFestival(config)
        elif r_type == "SplitDayAhoiKarwaDampatya":
            return SplitDayAhoiKarwaDampatyaFestival(config)
        elif r_type == "GyanDhanTrayodashi":
            return GyanDhanTrayodashiFestival(config)
        elif r_type == "KartikaAmavasyaMahaviraNirvana":
            return KartikaAmavasyaMahaviraNirvanaFestival(config)
        elif r_type == "KartikaShuklaEkamNewYear":
            return KartikaShuklaEkamNewYearFestival(config)
        elif r_type == "BhaiDooj":
            return BhaiDoojFestival(config)
        elif r_type == "KartikaShuklaPanchami":
            return KartikaShuklaPanchamiFestival(config)
        elif r_type == "KartikaNandishwarAshtami":
            return KartikaNandishwarAshtamiFestival(config)
        elif r_type == "PanditJainiJiyalalPunyatithi":
            return PanditJainiJiyalalPunyatithiFestival(config)
        elif r_type == "KartikaPurnimaAshtahnikaPurna":
            return KartikaPurnimaAshtahnikaPurnaFestival(config)
        elif r_type == "MargashirshaSheetalnathStotram":
            return MargashirshaSheetalnathStotramFestival(config)
        elif r_type == "MaghaLabdhiVidhan":
            return MaghaLabdhiVidhanFestival(config)
        elif r_type == "PanditJainiJiyalalJanmaDivas":
            return PanditJainiJiyalalJanmaDivasFestival(config)
        elif r_type == "MaghaShuklaPanchamiTri":
            return MaghaShuklaPanchamiTriFestival(config)
        elif r_type == "PhalgunaPurnimaAshtahnikaPurna":
            return PhalgunaPurnimaAshtahnikaPurnaFestival(config)
        elif r_type == "ChaitraAmavasyaKalyanakVarshant":
            return ChaitraAmavasyaKalyanakVarshantFestival(config)
        elif r_type == "Namokar35Vrat":
            return Namokar35VratFestival(config)
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
        occurrences = []
        year = context["year"]

        # Partition chronological snapshots into contiguous paksha blocks
        blocks: List[List[Dict[str, Any]]] = []
        curr_block: List[Dict[str, Any]] = []

        for s in snapshots:
            if not curr_block:
                curr_block.append(s)
            else:
                prev = curr_block[-1]
                if (
                    s["paksha"] == prev["paksha"]
                    and s["hindu_month"] == prev["hindu_month"]
                    and s["is_adhika"] == prev["is_adhika"]
                    and (s["date"] - prev["date"]).days == 1
                ):
                    curr_block.append(s)
                else:
                    blocks.append(curr_block)
                    curr_block = [s]
        if curr_block:
            blocks.append(curr_block)

        # Evaluate each paksha block for Bhaktambar Vrat span (Ashtami to Chaturdashi)
        for block in blocks:
            p = block[0]["paksha"]  # "Shukla" or "Krishna"
            tithi_dates: Dict[int, List[date]] = {t: [] for t in range(7, 15)}
            for s in block:
                t_num = s["tithi_in_paksha"]
                if t_num in tithi_dates:
                    tithi_dates[t_num].append(s["date"])

            target_dates = sorted([d for t in range(8, 15) for d in tithi_dates[t]])
            if not target_dates:
                continue

            # Natural start: first Ashtami if present, else first active target date
            if tithi_dates[8]:
                start_day = tithi_dates[8][0]
            else:
                start_day = target_dates[0]

            # Natural end: last Chaturdashi if present, else last active target date
            if tithi_dates[14]:
                end_day = tithi_dates[14][-1]
            else:
                end_day = target_dates[-1]

            natural_days = (end_day - start_day).days + 1

            # Kshaya Rule: minimum 7 days guarantee
            has_kshaya = False
            if natural_days < 7:
                has_kshaya = True
                if tithi_dates[7]:
                    start_day = tithi_dates[7][0]
                else:
                    start_day = end_day - timedelta(days=6)
                total_days = (end_day - start_day).days + 1
                if total_days < 7:
                    start_day = end_day - timedelta(days=6)
                    total_days = 7
            else:
                total_days = natural_days

            has_vriddhi = total_days > 7

            # Only include if start_day is in requested year
            if start_day.year != year:
                continue

            first_snap = block[0]
            jain_m = get_jain_month(first_snap)
            prefix = "Adhik " if first_snap["is_adhika"] else ""
            month_title = f"{prefix}{jain_m.capitalize()}"

            p_hindi = "शुक्ल" if p.lower() == "shukla" else "कृष्ण"
            start_mm_dd = start_day.strftime("%m-%d")
            end_mm_dd = end_day.strftime("%m-%d")
            span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

            occ_id = f"bhaktambar_vrat_{year}_{jain_m.lower()}_{p.lower()}"

            occurrences.append({
                "id": occ_id,
                "occurrence_id": occ_id,
                "name": f"{p} Bhaktambar Vrat",
                "title": f"{p} Bhaktambar Vrat ({month_title})",
                "name_hindi": f"{p_hindi} भक्ताम्बर व्रत ({month_title})",
                "category": self.category or "vrat",
                "badge": "Bhaktambar Vrat",
                "badge_color": "purple",
                "is_span": True,
                "span_label": span_label,
                "start_date": start_day.isoformat(),
                "end_date": end_day.isoformat(),
                "duration_days": total_days,
                "has_kshaya": has_kshaya,
                "has_vriddhi": has_vriddhi,
                "status": "confirmed",
                "meaning": self.meaning or "Bhaktambar Vrat from Ashtami (8) to Chaturdashi (14) of every Paksha.",
                "observance": self.observance or "Fasting and Bhaktambar Stotra Aradhana",
                "sources": self.sources or ["Jain Traditions"]
            })
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
                start_date_str = vrat.fast_start_date
                end_date_str = vrat.fast_end_date
                from datetime import datetime
                d1 = datetime.strptime(start_date_str, "%Y-%m-%d")
                d2 = datetime.strptime(end_date_str, "%Y-%m-%d")
                span_label = f"Span: {d1.strftime('%b %d')} - {d2.strftime('%b %d')}"
                
                occurrences.append({
                    "id": f"ratnatraya_vrat_prarambh_{p_name.lower()}_{year}",
                    "occurrence_id": f"ratnatraya_vrat_prarambh_{p_name.lower()}_{year}",
                    "name": f"Ratnatraya Vrat Prarambh ({p_name})",
                    "title": f"Ratnatraya Vrat Prarambh ({p_name})",
                    "name_hindi": self.name_hindi + " प्रारम्भ",
                    "category": self.category,
                    "badge": "Vrat Start",
                    "badge_color": "rose",
                    "is_span": True,
                    "span_label": span_label,
                    "boundary_type": "START",
                    "start_date": start_date_str,
                    "end_date": start_date_str,
                    "status": "confirmed",
                    "meaning": self.meaning,
                    "observance": self.observance,
                    "sources": self.sources
                })
                p_name_upper = p_name.upper()
                purna_name = f"Ratnatraya Vrat Purna ({p_name})"
                purna_hindi = self.name_hindi + " पूर्ण"
                if p_name_upper == "CHAITRA":
                    purna_name = "Ratnatraya / Sankatharan Vrat Purna (Chaitra)"
                    purna_hindi = "रत्नत्रय / संकटहरण व्रत पूर्ण (चैत्र)"
                
                occurrences.append({
                    "id": f"ratnatraya_vrat_purna_{p_name.lower()}_{year}",
                    "occurrence_id": f"ratnatraya_vrat_purna_{p_name.lower()}_{year}",
                    "name": purna_name,
                    "title": purna_name,
                    "name_hindi": purna_hindi,
                    "category": self.category,
                    "badge": "Vrat End",
                    "badge_color": "rose",
                    "is_span": True,
                    "span_label": span_label,
                    "boundary_type": "END",
                    "start_date": end_date_str,
                    "end_date": end_date_str,
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
        
        season_months = ["ASHADHA", "KARTIKA", "PHALGUNA"]
        if target_month and target_month.upper() not in season_months:
            return []

        months_to_process = [target_month.upper()] if target_month else season_months

        occurrences = []
        for m in months_to_process:
            month_snaps = [
                s for s in snapshots
                if s["date"].year == year
                and s["hindu_month"].upper() in [m, "KARTIK" if m == "KARTIKA" else m]
            ]
            
            if not month_snaps:
                continue

            has_adhik_month_in_year = any(s["is_adhika"] for s in month_snaps)
            if has_adhik_month_in_year:
                month_snaps = [s for s in month_snaps if s["is_adhika"]]
            else:
                month_snaps = [s for s in month_snaps if not s["is_adhika"]]

            tithi_dates = {t: [] for t in range(7, 16)}
            for s in month_snaps:
                for t in range(7, 16):
                    if s["tithi"] == t or s["jain_tithi"] == t or (s["paksha"] == "Shukla" and s["tithi_in_paksha"] == t):
                        tithi_dates[t].append(s["date"])

            skipped_tithis = [t for t in range(8, 16) if not tithi_dates[t]]
            repeated_tithis = [t for t in range(8, 16) if len(tithi_dates[t]) > 1]
            active_dates = sorted(list({d for t in range(8, 16) for d in tithi_dates[t]}))
            if not active_dates:
                continue

            has_only_kshaya = len(skipped_tithis) > 0 and len(repeated_tithis) == 0

            if has_only_kshaya:
                start_date = tithi_dates[7][0] if tithi_dates[7] else active_dates[0] - timedelta(days=1)
                end_date = active_dates[-1]
            else:
                start_date = active_dates[0]
                end_date = active_dates[-1]

            if has_adhik_month_in_year:
                prefix = "Adhik "
            else:
                prefix = ""
            month_title = prefix + m.capitalize()
            title = f"Ashtahnika Mahaparv ({month_title})"

            start_mm_dd = start_date.strftime("%m-%d")
            end_mm_dd = end_date.strftime("%m-%d")
            span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

            occurrences.append({
                "id": f"ashtahnika_{m.lower()}_{year}",
                "occurrence_id": f"ashtahnika_{m.lower()}_{year}",
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
            })
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
                from datetime import datetime
                d1 = datetime.strptime(vrat.start_date, "%Y-%m-%d")
                d2 = datetime.strptime(vrat.end_date, "%Y-%m-%d")
                span_label = f"Span: {d1.strftime('%b %d')} - {d2.strftime('%b %d')}"
                
                occurrences.append({
                    "id": f"shodashkaran_{p_name}_{year}",
                    "occurrence_id": f"shodashkaran_{p_name}_{year}",
                    "name": f"Shodashkaran Vrat ({p_name})",
                    "title": f"Shodashkaran Vrat ({p_name})",
                    "name_hindi": self.name_hindi,
                    "category": self.category,
                    "badge": "Shodashkaran Vrat",
                    "badge_color": "rose",
                    "is_span": True,
                    "span_label": span_label,
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
        
        season_months = ["ASHADHA", "SHRAVANA", "BHADRAPADA", "ASHVINA", "ASHWIN"]
        if target_month and target_month.upper() not in season_months:
            return []

        months_to_process = [target_month.upper()] if target_month else ["ASHADHA", "SHRAVANA", "BHADRAPADA", "ASHVINA"]

        occurrences = []
        for m in months_to_process:
            target_months_set = {m}
            if m in ["ASHVINA", "ASHWIN"]:
                target_months_set.add("ASHVINA")
                target_months_set.add("ASHWIN")

            month_snaps = [
                s for s in snapshots
                if s["date"].year == year
                and s["hindu_month"].upper() in target_months_set
            ]
            
            if not month_snaps:
                continue

            has_adhik_month_in_year = any(s["is_adhika"] for s in month_snaps)
            
            if m == "ASHADHA":
                if has_adhik_month_in_year:
                    month_snaps = [s for s in month_snaps if s["is_adhika"]]
                else:
                    month_snaps = [s for s in month_snaps if not s["is_adhika"]]

            for s in month_snaps:
                is_tithi_14_at_sunrise = (s["tithi_in_paksha"] == 14 and s["paksha"] == "Shukla")
                
                if is_tithi_14_at_sunrise:
                    if has_adhik_month_in_year:
                        prefix = "Adhik " if s["is_adhika"] else "Nija "
                    else:
                        prefix = ""
                    
                    month_title = prefix + s["hindu_month"]
                    title = f"Karma Nirjara Vrat ({month_title})"
                    
                    occurrences.append({
                        "id": f"karma_nirjara_vrat_{month_title.lower().replace(' ', '_')}_{year}",
                        "occurrence_id": f"karma_nirjara_vrat_{s['date'].isoformat()}",
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
        
        month_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() == "CHAITRA"
        ]
        
        if not month_snaps:
            return []

        month_snaps = [s for s in month_snaps if not s["is_adhika"]]
        
        if not month_snaps:
            return []

        ekam_days = [
            s for s in month_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 1
        ]

        target_snap = None
        if ekam_days:
            target_snap = ekam_days[0]
        else:
            dwitiya_days = [
                s for s in month_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 2
            ]
            if dwitiya_days:
                first_dwitiya = dwitiya_days[0]
                idx = snapshots.index(first_dwitiya)
                if idx > 0:
                    target_snap = snapshots[idx - 1]

        if not target_snap:
            return []

        return [
            {
                "id": f"gautam_swami_janam_divas_{year}",
                "occurrence_id": f"gautam_swami_janam_divas_{year}",
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
                "meaning": "Birth anniversary of Gandhar Gautam Swami",
                "observance": "Special prayers and reading of scriptures",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"shri_mallinath_ji___garbh_{year}",
                "occurrence_id": f"shri_mallinath_ji___garbh_{year}",
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
                "meaning": "Garbha Kalyanak of 19th Tirthankara Shri Mallinath Bhagwan",
                "observance": "Special prayers and reading of scriptures",
                "sources": ["Jain Traditions"]
            }
        ]


class PushpanjaliVratFestival(FestivalRule):
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        target_month = self.jain_month # e.g. "CHAITRA", "BHADRAPADA", "MAGHA"
        
        season_months = ["CHAITRA", "BHADRAPADA", "MAGHA"]
        if target_month and target_month.upper() not in season_months:
            return []

        months_to_process = [target_month.upper()] if target_month else season_months
        season_map = {"CHAITRA": "spring", "BHADRAPADA": "monsoon", "MAGHA": "winter"}

        occurrences = []
        for m in months_to_process:
            month_snaps = [
                s for s in snapshots
                if s["date"].year == year
                and s["hindu_month"].upper() == m
            ]
            
            if not month_snaps:
                continue

            has_adhik_month_in_year = any(s["is_adhika"] for s in month_snaps)
            if has_adhik_month_in_year:
                month_snaps = [s for s in month_snaps if s["is_adhika"]]
            else:
                month_snaps = [s for s in month_snaps if not s["is_adhika"]]

            tithi_dates = {t: [] for t in range(4, 15)}
            for s in month_snaps:
                if s["paksha"] == "Shukla":
                    t = s["tithi_in_paksha"]
                    if 4 <= t <= 14:
                        tithi_dates[t].append(s["date"])

            skipped_tithis = [t for t in range(5, 15) if not tithi_dates[t]]
            repeated_tithis = [t for t in range(5, 15) if len(tithi_dates[t]) > 1]
            active_dates = sorted(list({d for t in range(5, 10) for d in tithi_dates[t] if t <= 9}))
            if not active_dates:
                continue

            has_only_kshaya = len(skipped_tithis) > 0 and len(repeated_tithis) == 0

            if has_only_kshaya:
                start_date = tithi_dates[4][0] if tithi_dates[4] else active_dates[0] - timedelta(days=1)
                end_date = active_dates[-1]
            else:
                start_date = active_dates[0]
                end_date = active_dates[-1]

            vrat_dates = []
            curr = start_date
            while curr <= end_date:
                vrat_dates.append(curr)
                curr += timedelta(days=1)

            start_mm_dd = start_date.strftime("%m-%d")
            end_mm_dd = end_date.strftime("%m-%d")
            span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

            season_tag = season_map.get(m, "spring")
            for idx, d in enumerate(vrat_dates):
                day_num = idx + 1
                title = f"Pushpanjali Vrat - Day {day_num}"
                occurrences.append({
                    "id": f"pushpanjali_vrat_{season_tag}_{d.isoformat()}",
                    "occurrence_id": f"pushpanjali_vrat_{season_tag}_{d.isoformat()}",
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
        
        # Season Filter: Month == Kartika. Use get_jain_month() (purnimanta), not raw
        # hindu_month (amanta) -- this target includes Krishna-paksha days (Chaturdashi/
        # Amavasya), which live one amanta month earlier than their purnimanta display
        # name (see KALYANAK_AUDIT_NOTES.md); a raw amanta match here silently lands one
        # full lunar month late, every year, not just in Adhik Maas years.
        month_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and get_jain_month(s) == "KARTIKA"
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


class VeerShasanJayantiShrut(FestivalRule):
    """Shravana Krishna Ekam (1): Veer Shasan Jayanti & Shrut Udbhav Divas.

    Vriddhi: 1st Ekam
    Kshaya : Ashadha Purnima (15)
    Adhik  : Strictly Adhik Shravana
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        # --- Month filter: Shravana ---
        month_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() == "SHRAVANA"
        ]

        if not month_snaps:
            return []

        # --- Adhik Maas Rule (Strictly Adhik Shravana) ---
        has_adhik = any(s["is_adhika"] for s in month_snaps)
        if has_adhik:
            month_snaps = [s for s in month_snaps if s["is_adhika"]]
        else:
            month_snaps = [s for s in month_snaps if not s["is_adhika"]]

        if not month_snaps:
            return []

        # --- Resolve target day: Krishna Ekam (1) ---
        ekam_days = [
            s for s in month_snaps
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 1
        ]

        target_snap = None
        if ekam_days:
            # Normal / Vriddhi: always use 1st Ekam
            target_snap = ekam_days[0]
        else:
            # Kshaya: fallback to Ashadha Purnima (15) — find last Shukla 15 in Ashadha
            ashadha_purnima = [
                s for s in snapshots
                if s["date"].year == year
                and s["hindu_month"].upper() == "ASHADHA"
                and not s["is_adhika"]
                and s["paksha"] == "Shukla"
                and s["tithi_in_paksha"] == 15
            ]
            if ashadha_purnima:
                target_snap = ashadha_purnima[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()
        return [
            {
                "id": f"veer_shasan_jayanti_{year}",
                "occurrence_id": f"veer_shasan_jayanti_{year}",
                "name": "Veer Shasan Jayanti",
                "title": "Veer Shasan Jayanti",
                "name_hindi": "वीर शासन जयंती",
                "category": "jayanti",
                "badge": "Veer Shasan",
                "badge_color": "green",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Commencement of Bhagwan Mahavir's Shasan and his first divine discourse",
                "meaning": self.meaning or "Commencement of Bhagwan Mahavir's Shasan",
                "observance": self.observance or "Special prayers and Swadhyay",
                "sources": self.sources or ["Jain Traditions"]
            },
            {
                "id": f"shrut_udbhav_divas_{year}",
                "occurrence_id": f"shrut_udbhav_divas_{year}",
                "name": "Shrut Udbhav Divas",
                "title": "Shrut Udbhav Divas",
                "name_hindi": "श्रुत उद्भव दिवस",
                "category": "mahaparv",
                "badge": "Shrut Udbhav",
                "badge_color": "green",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Origin of Jain Agamic knowledge and scriptural tradition",
                "meaning": "Origin of Jain Agamic knowledge and scriptural tradition",
                "observance": "Scripture recitation and Agam Puja",
                "sources": ["Jain Traditions"]
            }
        ]


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


class SaptaRishiVratFestival(FestivalRule):
    """Sapta Rishi Vrat: Ashadha Shukla 14 (Prarambh) to Shravana Krishna 5 (Nishthapan).

    Start: Ashadha Shukla 14. Vriddhi -> 2nd 14, Kshaya -> Ashadha Shukla 13.
    End: Shravana Krishna 5. Vriddhi -> 2nd 5, Kshaya -> Shravana Krishna 4.
    Adhik Maas: Execute strictly during Adhik Maas if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        # 1. Ashadha snapshots
        ashadha_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() == "ASHADHA"
        ]
        if not ashadha_snaps:
            return []

        if any(s["is_adhika"] for s in ashadha_snaps):
            ashadha_snaps = [s for s in ashadha_snaps if s["is_adhika"]]
        else:
            ashadha_snaps = [s for s in ashadha_snaps if not s["is_adhika"]]

        # Start boundary: Shukla 14 (Vriddhi -> 2nd 14, Kshaya -> Shukla 13)
        shukla_14 = [s for s in ashadha_snaps if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 14]
        if shukla_14:
            start_snap = shukla_14[-1]
        else:
            shukla_13 = [s for s in ashadha_snaps if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 13]
            start_snap = shukla_13[-1] if shukla_13 else None

        if not start_snap:
            return []

        # 2. Shravana snapshots
        shravana_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() == "SHRAVANA"
        ]
        if not shravana_snaps:
            return []

        if any(s["is_adhika"] for s in shravana_snaps):
            shravana_snaps = [s for s in shravana_snaps if s["is_adhika"]]
        else:
            shravana_snaps = [s for s in shravana_snaps if not s["is_adhika"]]

        # End boundary: Krishna 5 (Vriddhi -> 2nd 5, Kshaya -> Krishna 4)
        krishna_5 = [s for s in shravana_snaps if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 5]
        if krishna_5:
            end_snap = krishna_5[-1]
        else:
            krishna_4 = [s for s in shravana_snaps if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 4]
            end_snap = krishna_4[-1] if krishna_4 else None

        if not end_snap:
            return []

        start_date_str = start_snap["date"].isoformat()
        end_date_str = end_snap["date"].isoformat()

        start_mm_dd = start_snap["date"].strftime("%m-%d")
        end_mm_dd = end_snap["date"].strftime("%m-%d")
        span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

        return [
            {
                "id": f"sapta_rishi_vrat_prarambh_{year}",
                "occurrence_id": f"sapta_rishi_vrat_prarambh_{year}",
                "name": "Sapta Rishi Vrat Prarambh",
                "title": "Sapta Rishi Vrat Prarambh",
                "name_hindi": "सप्तऋषि व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "description": "Commencement of the holy Sapta Rishi Vrat",
                "meaning": self.meaning or "Commencement of the holy Sapta Rishi Vrat",
                "observance": self.observance or "Fasting and Sapta Rishi Puja",
                "sources": self.sources or ["Jain Traditions"]
            },
            {
                "id": f"sapta_rishi_vrat_nishthapan_{year}",
                "occurrence_id": f"sapta_rishi_vrat_nishthapan_{year}",
                "name": "Sapta Rishi Vrat Nishthapan",
                "title": "Sapta Rishi Vrat Nishthapan",
                "name_hindi": "सप्तऋषि व्रत निष्थापन",
                "category": "vrat",
                "badge": "Vrat End",
                "badge_color": "pink",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "description": "Formal completion and Nishthapan of Sapta Rishi Vrat",
                "meaning": self.meaning or "Formal completion and Nishthapan of Sapta Rishi Vrat",
                "observance": self.observance or "Formal conclusion of Sapta Rishi Vrat",
                "sources": self.sources or ["Jain Traditions"]
            }
        ]


class SaptaParamsthanVratFestival(FestivalRule):
    """Sapta Paramsthan Vrat: Shravana Shukla 1 (Prarambh) to Shravana Shukla 7 (Purna).

    Start: Shravana Shukla Ekam (1). Vriddhi -> 1st Ekam, Kshaya -> Shravana Krishna Amavasya (15).
    End: Shravana Shukla Saptami (7). Vriddhi -> 2nd Saptami, Kshaya -> Shravana Shukla Shashthi (6).
    Adhik Maas: Execute strictly during Adhik Shravana if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        shravana_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["SHRAVANA", "SAVAN", "SHRAVAN"]
        ]
        if not shravana_snaps:
            return []

        if any(s["is_adhika"] for s in shravana_snaps):
            shravana_snaps = [s for s in shravana_snaps if s["is_adhika"]]
        else:
            shravana_snaps = [s for s in shravana_snaps if not s["is_adhika"]]

        # Start boundary: Shukla Ekam (1). Vriddhi -> 1st Ekam, Kshaya -> Krishna Amavasya (15)
        shukla_1 = [
            s for s in shravana_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 1
        ]
        if shukla_1:
            start_snap = shukla_1[0]
        else:
            krishna_15 = [
                s for s in shravana_snaps
                if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 15
            ]
            if krishna_15:
                start_snap = krishna_15[-1]
            else:
                shukla_2 = [
                    s for s in shravana_snaps
                    if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 2
                ]
                if shukla_2:
                    first_dwitiya = shukla_2[0]
                    idx = snapshots.index(first_dwitiya)
                    start_snap = snapshots[idx - 1] if idx > 0 else first_dwitiya
                else:
                    start_snap = None

        if not start_snap:
            return []

        # End boundary: Shukla Saptami (7). Vriddhi -> 2nd Saptami, Kshaya -> Shukla Shashthi (6)
        shukla_7 = [
            s for s in shravana_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 7
        ]
        if shukla_7:
            end_snap = shukla_7[-1]
        else:
            shukla_6 = [
                s for s in shravana_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 6
            ]
            end_snap = shukla_6[-1] if shukla_6 else None

        if not end_snap:
            return []

        start_date_str = start_snap["date"].isoformat()
        end_date_str = end_snap["date"].isoformat()

        start_mm_dd = start_snap["date"].strftime("%m-%d")
        end_mm_dd = end_snap["date"].strftime("%m-%d")
        span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

        return [
            {
                "id": f"sapta_paramsthan_vrat_prarambh_{year}",
                "occurrence_id": f"sapta_paramsthan_vrat_prarambh_{year}",
                "name": "Sapta Paramsthan Vrat Prarambh",
                "title": "Sapta Paramsthan Vrat Prarambh",
                "name_hindi": "सप्त परमस्थान व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "START",
                "description": "Commencement of the 7-day Sapta Paramsthan Vrat",
                "meaning": self.meaning or "Commencement of the 7-day Sapta Paramsthan Vrat",
                "observance": self.observance or "Fasting and Sapta Paramsthan Aradhana",
                "sources": self.sources or ["Jain Traditions"]
            },
            {
                "id": f"sapta_paramsthan_vrat_purna_{year}",
                "occurrence_id": f"sapta_paramsthan_vrat_purna_{year}",
                "name": "Sapta Paramsthan Vrat Purna",
                "title": "Sapta Paramsthan Vrat Purna",
                "name_hindi": "सप्त परमस्थान व्रत पूर्ण",
                "category": "vrat",
                "badge": "Vrat End",
                "badge_color": "pink",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "END",
                "description": "Conclusion and completion of Sapta Paramsthan Vrat",
                "meaning": self.meaning or "Conclusion and completion of Sapta Paramsthan Vrat",
                "observance": self.observance or "Conclusion of Sapta Paramsthan Vrat",
                "sources": self.sources or ["Jain Traditions"]
            }
        ]


class RakshabandhanVratFestival(FestivalRule):
    """Rakshabandhan Vrat: Shravana Shukla Trayodashi (13) to Shravana Shukla Purnima (15).

    Strict Span Invariant: MUST run for a minimum of 3 distinct solar calendar days.
    If ANY tithi in (13, 14, 15) is skipped (Kshaya), shift start date backward to Shukla Dvadashi (12).
    Start: 1st Trayodashi (or Dvadashi on Kshaya shift).
    End: 2nd Purnima (or Shukla Chaturdashi on Purnima Kshaya).
    Adhik Maas: Execute strictly during Adhik Shravana if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        shravana_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["SHRAVANA", "SAVAN", "SHRAVAN"]
        ]
        if not shravana_snaps:
            return []

        if any(s["is_adhika"] for s in shravana_snaps):
            shravana_snaps = [s for s in shravana_snaps if s["is_adhika"]]
        else:
            shravana_snaps = [s for s in shravana_snaps if not s["is_adhika"]]

        def get_tithi_snaps(t_num):
            res = []
            for s in shravana_snaps:
                if s["tithi"] == t_num or s["jain_tithi"] == t_num or (s["paksha"] == "Shukla" and s["tithi_in_paksha"] == t_num):
                    res.append(s)
            return res

        shukla_12 = get_tithi_snaps(12)
        shukla_13 = get_tithi_snaps(13)
        shukla_14 = get_tithi_snaps(14)
        shukla_15 = get_tithi_snaps(15)

        has_any_kshaya = (not shukla_13) or (not shukla_14) or (not shukla_15)

        if has_any_kshaya:
            if shukla_12:
                start_snap = shukla_12[0]
            elif shukla_13:
                start_snap = shukla_13[0]
            else:
                first_available = shukla_14[0] if shukla_14 else (shukla_15[0] if shukla_15 else None)
                if first_available:
                    idx = snapshots.index(first_available)
                    start_snap = snapshots[idx - 1] if idx > 0 else first_available
                else:
                    start_snap = None
        else:
            start_snap = shukla_13[0]

        if not start_snap:
            return []

        if shukla_15:
            end_snap = shukla_15[-1]
        elif shukla_14:
            end_snap = shukla_14[-1]
        else:
            end_snap = None

        if not end_snap:
            return []

        start_date_str = start_snap["date"].isoformat()
        end_date_str = end_snap["date"].isoformat()

        start_mm_dd = start_snap["date"].strftime("%m-%d")
        end_mm_dd = end_snap["date"].strftime("%m-%d")
        span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

        return [
            {
                "id": f"rakshabandhan_vrat_prarambh_{year}",
                "occurrence_id": f"rakshabandhan_vrat_prarambh_{year}",
                "name": "Rakshabandhan Vrat Prarambh",
                "title": "Rakshabandhan Vrat Prarambh",
                "name_hindi": "रक्षाबंधन व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "START",
                "description": "Commencement of Rakshabandhan Vrat (Minimum 3-day span preserved)",
                "meaning": self.meaning or "Commencement of Rakshabandhan Vrat (Minimum 3-day span preserved)",
                "observance": self.observance or "Fasting and Rakshabandhan Aradhana",
                "sources": self.sources or ["Jain Traditions"]
            },
            {
                "id": f"rakshabandhan_vrat_purna_{year}",
                "occurrence_id": f"rakshabandhan_vrat_purna_{year}",
                "name": "Rakshabandhan Vrat Purna (Rakshabandhan Mahaparv)",
                "title": "Rakshabandhan Vrat Purna (Rakshabandhan Mahaparv)",
                "name_hindi": "रक्षाबंधन व्रत पूर्ण (रक्षाबंधन महापर्व)",
                "category": "mahaparv",
                "badge": "Vrat End",
                "badge_color": "pink",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "END",
                "description": "Conclusion of Rakshabandhan Vrat & Celebration of Rakshabandhan Mahaparv",
                "meaning": self.meaning or "Conclusion of Rakshabandhan Vrat & Celebration of Rakshabandhan Mahaparv",
                "observance": self.observance or "Conclusion of Rakshabandhan Vrat and Mahaparv celebration",
                "sources": self.sources or ["Jain Traditions"]
            }
        ]


class ShravanaPurnimaRakshabandhanFestival(FestivalRule):
    """Shravana Purnima: Rakshabandhan / 700 Muni Raksha Divas.

    Render 3 associated events on Shravana Shukla Purnima:
    1. Rakshabandhan (700 Muni Raksha Divas)
    2. Muni Vishnukumar avem Akampanacharya Pujan
    3. Sorana Pujan (Raksha Sutra Bandhan)

    Vriddhi: Assign strictly to 2nd Purnima instance.
    Kshaya : Trigger and render on Shravana Shukla Chaturdashi (14).
    Adhik  : Execute strictly during Adhik Shravana if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        shravana_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["SHRAVANA", "SAVAN", "SHRAVAN"]
        ]
        if not shravana_snaps:
            return []

        if any(s["is_adhika"] for s in shravana_snaps):
            shravana_snaps = [s for s in shravana_snaps if s["is_adhika"]]
        else:
            shravana_snaps = [s for s in shravana_snaps if not s["is_adhika"]]

        def get_tithi_snaps(t_num):
            res = []
            for s in shravana_snaps:
                if s["tithi"] == t_num or s["jain_tithi"] == t_num or (s["paksha"] == "Shukla" and s["tithi_in_paksha"] == t_num):
                    res.append(s)
            return res

        purnima_snaps = get_tithi_snaps(15)
        if purnima_snaps:
            target_snap = purnima_snaps[-1]  # Vriddhi -> 2nd Purnima
        else:
            chaturdashi_snaps = get_tithi_snaps(14)
            target_snap = chaturdashi_snaps[-1] if chaturdashi_snaps else None  # Kshaya -> 14

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"rakshabandhan_700_muni_raksha_divas_{year}",
                "occurrence_id": f"rakshabandhan_700_muni_raksha_divas_{year}",
                "name": "Rakshabandhan (700 Muni Raksha Divas)",
                "title": "Rakshabandhan (700 Muni Raksha Divas)",
                "name_hindi": "रक्षाबंधन (७०० मुनि रक्षा दिवस)",
                "category": "mahaparv",
                "badge": "Mahaparv",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Commemorating the protection of Acharya Akampanacharya and 700 Munis by Muni Vishnukumar at Hastinapur",
                "meaning": "Commemorating the protection of Acharya Akampanacharya and 700 Munis by Muni Vishnukumar at Hastinapur",
                "observance": "Special Mahaparv celebration, Munis Protection remembrance",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"muni_vishnukumar_akampanacharya_pujan_{year}",
                "occurrence_id": f"muni_vishnukumar_akampanacharya_pujan_{year}",
                "name": "Muni Vishnukumar avem Akampanacharya Pujan",
                "title": "Muni Vishnukumar avem Akampanacharya Pujan",
                "name_hindi": "मुनि विष्णुकुमार एवं अकंपनाचार्य पूजन",
                "category": "poojan",
                "badge": "Pujan",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Special aradhana dedicated to Muni Vishnukumar and Acharya Akampanacharya",
                "meaning": "Special aradhana dedicated to Muni Vishnukumar and Acharya Akampanacharya",
                "observance": "Special Pujan of Muni Vishnukumar and Acharya Akampanacharya",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"sorana_pujan_{year}",
                "occurrence_id": f"sorana_pujan_{year}",
                "name": "Sorana Pujan (Raksha Sutra Bandhan)",
                "title": "Sorana Pujan (Raksha Sutra Bandhan)",
                "name_hindi": "सोरना पूजन (रक्षा सूत्र बंधन)",
                "category": "parv_vidhi",
                "badge": "Sorana Pujan",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Sacred thread tying and protection ritual blessed with the Namokar Mantra",
                "meaning": "Sacred thread tying and protection ritual blessed with the Namokar Mantra",
                "observance": "Sorana Pujan and Raksha Sutra Bandhan",
                "sources": ["Jain Traditions"]
            }
        ]


class BhadrapadaKrishnaEkamMultiVratFestival(FestivalRule):
    """Bhadrapada Krishna Ekam (1): 6 Multi-Vrat Start Engine.

    Renders 6 Vrat Start events on Bhadrapada Krishna Ekam:
    1. Solah Karan Vrat Prarambh
    2. Shri Jin Mukhavlokan Vrat Prarambh
    3. Shrut Skandha Vrat Prarambh
    4. Mushti Vidhan Vrat Prarambh
    5. Dhanda Kalash Vrat Prarambh
    6. Megh Mala Vrat Prarambh

    Vriddhi: Assign strictly to 1st Ekam instance.
    Kshaya : Trigger and render on Shravana Shukla Purnima (15).
    Adhik  : Execute strictly during Adhik Bhadrapada if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        bhadra_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["BHADRAPADA", "BHADWA", "BHADRA"]
        ]
        if not bhadra_snaps:
            return []

        if any(s["is_adhika"] for s in bhadra_snaps):
            bhadra_snaps = [s for s in bhadra_snaps if s["is_adhika"]]
        else:
            bhadra_snaps = [s for s in bhadra_snaps if not s["is_adhika"]]

        ekam_days = [
            s for s in bhadra_snaps
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 1
        ]

        target_snap = None
        if ekam_days:
            target_snap = ekam_days[0]  # Vriddhi -> 1st Ekam
        else:
            # Kshaya: fallback to Shravana Shukla Purnima (15)
            shravana_purnima = [
                s for s in snapshots
                if s["date"].year == year
                and s["hindu_month"].upper() in ["SHRAVANA", "SAVAN", "SHRAVAN"]
                and not s["is_adhika"]
                and s["paksha"] == "Shukla"
                and s["tithi_in_paksha"] == 15
            ]
            if shravana_purnima:
                target_snap = shravana_purnima[-1]
            else:
                krishna_2 = [
                    s for s in bhadra_snaps
                    if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 2
                ]
                if krishna_2:
                    first_dwitiya = krishna_2[0]
                    idx = snapshots.index(first_dwitiya)
                    target_snap = snapshots[idx - 1] if idx > 0 else first_dwitiya

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"solah_karan_vrat_prarambh_{year}",
                "occurrence_id": f"solah_karan_vrat_prarambh_{year}",
                "name": "Solah Karan Vrat Prarambh",
                "title": "Solah Karan Vrat Prarambh",
                "name_hindi": "सोलह कारण व्रत प्रारम्भ",
                "category": "mahaparv_vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "is_span": True,
                "description": "Commencement of 32-day Solah Karan Bhavna Aradhana",
                "meaning": "Commencement of 32-day Solah Karan Bhavna Aradhana",
                "observance": "Solah Karan Bhavna contemplation and fasting",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"shri_jin_mukhavlokan_vrat_prarambh_{year}",
                "occurrence_id": f"shri_jin_mukhavlokan_vrat_prarambh_{year}",
                "name": "Shri Jin Mukhavlokan Vrat Prarambh",
                "title": "Shri Jin Mukhavlokan Vrat Prarambh",
                "name_hindi": "श्री जिन मुखअवलोकन व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "is_span": True,
                "description": "Commencement of Jin Mukh Avlokan Vrat",
                "meaning": "Commencement of Jin Mukh Avlokan Vrat",
                "observance": "Jina Darshan before morning meals",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"shrut_skandha_vrat_prarambh_{year}",
                "occurrence_id": f"shrut_skandha_vrat_prarambh_{year}",
                "name": "Shrut Skandha Vrat Prarambh",
                "title": "Shrut Skandha Vrat Prarambh",
                "name_hindi": "श्रुत स्कंध व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Commencement of Shrut Skandha Vrat dedicated to Jinvani",
                "meaning": "Commencement of Shrut Skandha Vrat dedicated to Jinvani",
                "observance": "Scripture reverence and Swadhyay",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"mushti_vidhan_vrat_prarambh_{year}",
                "occurrence_id": f"mushti_vidhan_vrat_prarambh_{year}",
                "name": "Mushti Vidhan Vrat Prarambh",
                "title": "Mushti Vidhan Vrat Prarambh",
                "name_hindi": "मुष्टि विधान व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Commencement of Mushti Vidhan Aradhana",
                "meaning": "Commencement of Mushti Vidhan Aradhana",
                "observance": "Fistful grain donation/restriction fasting",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"dhanda_kalash_vrat_prarambh_{year}",
                "occurrence_id": f"dhanda_kalash_vrat_prarambh_{year}",
                "name": "Dhanda Kalash Vrat Prarambh",
                "title": "Dhanda Kalash Vrat Prarambh",
                "name_hindi": "धनद कलश व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Commencement of Dhanda Kalash Vrat",
                "meaning": "Commencement of Dhanda Kalash Vrat",
                "observance": "Mangal Kalash worship and spiritual purification",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"megh_mala_vrat_prarambh_{year}",
                "occurrence_id": f"megh_mala_vrat_prarambh_{year}",
                "name": "Megh Mala Vrat Prarambh",
                "title": "Megh Mala Vrat Prarambh",
                "name_hindi": "मेघ माला व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Commencement of Megh Mala Vrat during Varsha Ritu",
                "meaning": "Commencement of Megh Mala Vrat during Varsha Ritu",
                "observance": "Monsoon penance and Nirjara aradhana",
                "sources": ["Jain Traditions"]
            }
        ]


class TeenChaubisiVratFestival(FestivalRule):
    """Bhadrapada Krishna Tritiya (3): Teen Chaubisi Vrat Prarambh.

    Commencement of the 72 Tirthankaras Vrat.
    Vriddhi: Assign strictly to 1st Tritiya.
    Kshaya : Trigger and render on Bhadrapada Krishna Dwitiya (2).
    Adhik  : Execute strictly during Adhik Bhadrapada if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        bhadra_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["BHADRAPADA", "BHADWA", "BHADRA"]
        ]
        if not bhadra_snaps:
            return []

        if any(s["is_adhika"] for s in bhadra_snaps):
            bhadra_snaps = [s for s in bhadra_snaps if s["is_adhika"]]
        else:
            bhadra_snaps = [s for s in bhadra_snaps if not s["is_adhika"]]

        tritiya_days = [
            s for s in bhadra_snaps
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 3
        ]

        target_snap = None
        if tritiya_days:
            target_snap = tritiya_days[0]  # Vriddhi -> 1st Tritiya
        else:
            # Kshaya: fallback to Bhadrapada Krishna Dwitiya (2)
            dwitiya_days = [
                s for s in bhadra_snaps
                if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 2
            ]
            if dwitiya_days:
                target_snap = dwitiya_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"teen_chaubisi_vrat_prarambh_{year}",
                "occurrence_id": f"teen_chaubisi_vrat_prarambh_{year}",
                "name": "Teen Chaubisi Vrat Prarambh",
                "title": "Teen Chaubisi Vrat Prarambh",
                "name_hindi": "तीन चौबीसी व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "is_span": True,
                "boundary_type": "START",
                "description": "Commencement of Teen Chaubisi Vrat (Aradhana of 72 Tirthankaras: Bhoot, Vartaman, and Bhavishya)",
                "meaning": "Commencement of Teen Chaubisi Vrat (Aradhana of 72 Tirthankaras: Bhoot, Vartaman, and Bhavishya)",
                "observance": "Fasting and Teen Chaubisi Tirthankara Aradhana",
                "sources": ["Jain Traditions"]
            }
        ]


class AkshayaNidhiVratFestival(FestivalRule):
    """Akshaya Nidhi Vrat: Shravana Shukla Dashami (10) to Bhadrapada Krishna Dashami (10).

    Start: Shravana Shukla Dashami (Vriddhi -> 1st Dashami, Kshaya -> Shravana Shukla Navami 9).
    End: Bhadrapada Krishna Dashami (Vriddhi -> 2nd Dashami, Kshaya -> Bhadrapada Krishna Navami 9).
    Adhik Maas: Execute strictly during Adhik Maas if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        shravana_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["SHRAVANA", "SAVAN", "SHRAVAN"]
        ]
        if any(s["is_adhika"] for s in shravana_snaps):
            shravana_snaps = [s for s in shravana_snaps if s["is_adhika"]]
        else:
            shravana_snaps = [s for s in shravana_snaps if not s["is_adhika"]]

        bhadra_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["BHADRAPADA", "BHADWA", "BHADRA"]
        ]
        if any(s["is_adhika"] for s in bhadra_snaps):
            bhadra_snaps = [s for s in bhadra_snaps if s["is_adhika"]]
        else:
            bhadra_snaps = [s for s in bhadra_snaps if not s["is_adhika"]]

        # Start boundary: Shravana Shukla Dashami (10)
        shravana_shukla_10 = [
            s for s in shravana_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 10
        ]
        if shravana_shukla_10:
            start_snap = shravana_shukla_10[0]  # Vriddhi -> 1st Dashami
        else:
            shravana_shukla_9 = [
                s for s in shravana_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 9
            ]
            start_snap = shravana_shukla_9[-1] if shravana_shukla_9 else None

        # End boundary: Bhadrapada Krishna Dashami (10)
        bhadra_krishna_10 = [
            s for s in bhadra_snaps
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 10
        ]
        if bhadra_krishna_10:
            end_snap = bhadra_krishna_10[-1]  # Vriddhi -> 2nd Dashami
        else:
            bhadra_krishna_9 = [
                s for s in bhadra_snaps
                if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 9
            ]
            end_snap = bhadra_krishna_9[-1] if bhadra_krishna_9 else None

        if not start_snap or not end_snap:
            return []

        start_date_str = start_snap["date"].isoformat()
        end_date_str = end_snap["date"].isoformat()

        start_mm_dd = start_snap["date"].strftime("%m-%d")
        end_mm_dd = end_snap["date"].strftime("%m-%d")
        span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

        return [
            {
                "id": f"akshaya_nidhi_vrat_prarambh_{year}",
                "occurrence_id": f"akshaya_nidhi_vrat_prarambh_{year}",
                "name": "Akshaya Nidhi Vrat Prarambh",
                "title": "Akshaya Nidhi Vrat Prarambh",
                "name_hindi": "अक्षय निधि व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "START",
                "description": "Commencement of Akshaya Nidhi Vrat",
                "meaning": self.meaning or "Commencement of Akshaya Nidhi Vrat",
                "observance": self.observance or "Fasting and Akshaya Nidhi Aradhana",
                "sources": self.sources or ["Jain Traditions"]
            },
            {
                "id": f"akshaya_nidhi_vrat_purna_{year}",
                "occurrence_id": f"akshaya_nidhi_vrat_purna_{year}",
                "name": "Akshaya Nidhi Vrat Purna",
                "title": "Akshaya Nidhi Vrat Purna",
                "name_hindi": "अक्षय निधि व्रत पूर्ण",
                "category": "vrat",
                "badge": "Vrat End",
                "badge_color": "pink",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "END",
                "description": "Conclusion and Nishthapan of Akshaya Nidhi Vrat",
                "meaning": self.meaning or "Conclusion and Nishthapan of Akshaya Nidhi Vrat",
                "observance": self.observance or "Conclusion of Akshaya Nidhi Vrat",
                "sources": self.sources or ["Jain Traditions"]
            }
        ]


class ShvetambaraParyushan50DayFestival(FestivalRule):
    """Shvetambara Paryushan & Samvatsari 50-Day Rule Engine Logic.

    Anchor: Ashadha Shukla Chaturdashi (14).
    Vriddhi on Anchor: 2nd Chaturdashi.
    50-Day Count Stream: Increments on active solar sunrises (49 calendar days).
    Adhik Shravana Rule: If Adhik Shravana occurs, the 50-day count stream runs
    strictly through the designated Adhik Maas cycle stream (which naturally occurs
    on solar days).
    Emits:
    Day 1: Chaturmas Prarambh (50-Day Paryushan Cycle Start)
    Day 43..49: Paryushan Parv Days 1 to 7
    Day 50: Samvatsari Mahaparv (Kshamavani Divas)
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        ashadha_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["ASHADHA", "ASADH", "ASADHA"]
            and not s["is_adhika"]
            and s["paksha"] == "Shukla"
            and s["tithi_in_paksha"] == 14
        ]

        if not ashadha_snaps:
            return []

        # Vriddhi Rule on Anchor: 2nd Chaturdashi
        anchor_snap = ashadha_snaps[-1]
        start_date = anchor_snap["date"]

        events = []

        # Day 1
        d1_date_str = start_date.isoformat()
        events.append({
            "id": f"shvetambara_chaturmas_prarambh_{year}",
            "occurrence_id": f"shvetambara_chaturmas_prarambh_{year}",
            "name": "Chaturmas Prarambh (50-Day Paryushan Cycle Start)",
            "title": "Chaturmas Prarambh (50-Day Paryushan Cycle Start)",
            "name_hindi": "चातुर्मास प्रारम्भ (५० दिवसीय पर्युषण चक्र प्रारम्भ)",
            "category": "mahaparv",
            "badge": "Cycle Start",
            "badge_color": "pink",
            "start_date": d1_date_str,
            "end_date": d1_date_str,
            "status": "confirmed",
            "is_span": True,
            "span_label": "Day 1 of 50",
            "day_index": 1,
            "total_cycle_days": 50,
            "boundary_type": "START",
            "description": "Commencement of Chaturmas and 50-day countdown to Samvatsari Mahaparv (Adhik Maas stream active)",
            "meaning": "Commencement of Chaturmas and 50-day countdown to Samvatsari Mahaparv",
            "observance": "Chaturmas Sthirata and Svadhyay Span",
            "sources": ["Jain Traditions"]
        })

        # Days 43 to 49 (Paryushan Parv Days 1 to 7)
        paryushan_titles = [
            "Paryushan Parv Day 1 (Prarambh)",
            "Paryushan Parv Day 2 (Pothi Vadhawan)",
            "Paryushan Parv Day 3 (Kalpasutra Agaman)",
            "Paryushan Parv Day 4 (Kalpasutra Pathan)",
            "Paryushan Parv Day 5 (14 Swapna Darshan)",
            "Paryushan Parv Day 6 (Janmotsav Palna Pujan)",
            "Paryushan Parv Day 7 (Barsa Sutra)"
        ]

        for i, title in enumerate(paryushan_titles, start=43):
            d_date = start_date + timedelta(days=i - 1)
            d_str = d_date.isoformat()
            p_day_num = i - 42
            events.append({
                "id": f"paryushan_parv_day_{p_day_num}_{year}",
                "occurrence_id": f"paryushan_parv_day_{p_day_num}_{year}",
                "name": title,
                "title": title,
                "name_hindi": f"पर्युषण पर्व दिवस {p_day_num}",
                "category": "mahaparv",
                "badge": f"Day {p_day_num}",
                "badge_color": "pink",
                "start_date": d_str,
                "end_date": d_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": f"Day {i} of 50",
                "day_index": i,
                "total_cycle_days": 50,
                "description": f"Paryushan Parv Day {p_day_num} Observance",
                "meaning": title,
                "observance": "Kalpasutra Swadhyay and Tap-Aradhana",
                "sources": ["Jain Traditions"]
            })

        # Day 50 (Samvatsari Mahaparv)
        d50_date = start_date + timedelta(days=49)
        d50_str = d50_date.isoformat()
        events.append({
            "id": f"samvatsari_mahaparv_{year}",
            "occurrence_id": f"samvatsari_mahaparv_{year}",
            "name": "Samvatsari Mahaparv (Kshamavani Divas)",
            "title": "Samvatsari Mahaparv (Kshamavani Divas)",
            "name_hindi": "संवत्सरी महापर्व (क्षमावाणी दिवस)",
            "category": "mahaparv",
            "badge": "Samvatsari",
            "badge_color": "pink",
            "start_date": d50_str,
            "end_date": d50_str,
            "status": "confirmed",
            "is_span": True,
            "span_label": "Day 50 of 50",
            "paryushan_day": 8,
            "paryushan_total": 8,
            "boundary_type": "END",
            "description": "50th Day Culmination of Chaturmas cycle: Samvatsari Pratikramana and Universal Forgiveness (Micchami Dukkadam)",
            "meaning": "Samvatsari Pratikramana and Universal Forgiveness (Micchami Dukkadam)",
            "observance": "Samvatsari Pratikramana, Fasting, Kshamavani",
            "sources": ["Jain Traditions"]
        })

        return events


class BhayaHaranVratFestival(FestivalRule):
    """Bhadrapada Krishna Chaturthi (4): Bhaya Haran Vrat Engine Logic.

    Target: Bhadrapada Krishna Chaturthi (4).
    Vriddhi: Assign strictly to 1st Chaturthi.
    Kshaya : Trigger and render on Bhadrapada Krishna Tritiya (3).
    Adhik  : Execute strictly during Adhik Bhadrapada if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        bhadra_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["BHADRAPADA", "BHADWA", "BHADRA"]
        ]
        if not bhadra_snaps:
            return []

        if any(s["is_adhika"] for s in bhadra_snaps):
            bhadra_snaps = [s for s in bhadra_snaps if s["is_adhika"]]
        else:
            bhadra_snaps = [s for s in bhadra_snaps if not s["is_adhika"]]

        chaturthi_days = [
            s for s in bhadra_snaps
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 4
        ]

        target_snap = None
        if chaturthi_days:
            target_snap = chaturthi_days[0]  # Vriddhi -> 1st Chaturthi
        else:
            # Kshaya: fallback to Bhadrapada Krishna Tritiya (3)
            tritiya_days = [
                s for s in bhadra_snaps
                if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 3
            ]
            if tritiya_days:
                target_snap = tritiya_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"bhaya_haran_vrat_{year}",
                "occurrence_id": f"bhaya_haran_vrat_{year}",
                "name": "Bhaya Haran Vrat",
                "title": "Bhaya Haran Vrat",
                "name_hindi": "भय हरण व्रत",
                "category": "vrat",
                "badge": "Vrat",
                "badge_color": "green",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Bhadrapada Krishna Chaturthi vrat dedicated to the aradhana of fearlessness (Abhaya) and dispelling worldly fears",
                "meaning": "Bhadrapada Krishna Chaturthi vrat dedicated to the aradhana of fearlessness (Abhaya) and dispelling worldly fears",
                "observance": "Fasting and Abhaya Aradhana",
                "sources": ["Jain Traditions"]
            }
        ]


class LabdhiVidhanVratFestival(FestivalRule):
    """Labdhi Vidhan Vrat: Bhadrapada Krishna Amavasya to Samvatsari Day.

    Start: Bhadrapada Krishna Amavasya.
    End: Samvatsari Mahaparv (Day 50 from Ashadha Shukla 14).
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        jain_snaps = [s for s in snapshots if s["date"].year == year and get_jain_month(s) == "BHADRAPADA"]
        if not jain_snaps: return []
        if any(s["is_adhika"] for s in jain_snaps):
            jain_snaps = [s for s in jain_snaps if s["is_adhika"]]
        else:
            jain_snaps = [s for s in jain_snaps if not s["is_adhika"]]
            
        amavasya_days = [s for s in jain_snaps if s["paksha"] == "Krishna" and s["tithi_in_paksha"] in [15, 30]]
        start_snap = amavasya_days[0] if amavasya_days else None
        if not start_snap:
            k14 = [s for s in jain_snaps if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 14]
            if k14: start_snap = k14[-1]
            
        ashadha_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and get_jain_month(s) == "ASHADHA"
            and not s["is_adhika"]
            and s["paksha"] == "Shukla"
            and s["tithi_in_paksha"] == 14
        ]
        if ashadha_snaps:
            anchor_date = ashadha_snaps[-1]["date"]
            end_date = anchor_date + timedelta(days=49)
        else:
            end_date = None
            
        if not start_snap or not end_date: return []
        
        start_date_str = start_snap["date"].isoformat()
        end_date_str = end_date.isoformat()
        start_mm_dd = start_snap["date"].strftime("%b %d")
        end_mm_dd = end_date.strftime("%b %d")
        
        return [
            {
                "id": f"labdhi_vidhan_vrat_prarambh_{year}",
                "occurrence_id": f"labdhi_vidhan_vrat_prarambh_{year}",
                "name": "Labdhi Vidhan Vrat Prarambh",
                "title": "Labdhi Vidhan Vrat Prarambh",
                "name_hindi": "लब्धि विधान व्रत प्रारम्भ",
                "category": self.category,
                "badge": "Vrat Start",
                "badge_color": "pink",
                "is_span": True,
                "span_label": f"Span: {start_mm_dd} - {end_mm_dd}",
                "boundary_type": "START",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "description": self.meaning or "Commencement of Labdhi Vidhan Vrat",
                "meaning": self.meaning or "Commencement of Labdhi Vidhan Vrat",
                "observance": self.observance or "Labdhi Vrat Start",
                "sources": self.sources
            },
            {
                "id": f"labdhi_vidhan_vrat_purna_{year}",
                "occurrence_id": f"labdhi_vidhan_vrat_purna_{year}",
                "name": "Labdhi Vidhan Vrat Purna",
                "title": "Labdhi Vidhan Vrat Purna",
                "name_hindi": "लब्धि विधान व्रत पूर्ण",
                "category": self.category,
                "badge": "Vrat End",
                "badge_color": "pink",
                "is_span": True,
                "span_label": f"Span: {start_mm_dd} - {end_mm_dd}",
                "boundary_type": "END",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "description": self.meaning or "Conclusion of Labdhi Vidhan Vrat",
                "meaning": self.meaning or "Conclusion of Labdhi Vidhan Vrat",
                "observance": self.observance or "Labdhi Vrat End",
                "sources": self.sources
            }
        ]

class TalaDharTapShantisagarPunyatithiFestival(FestivalRule):
    """Bhadrapada Shukla Dwitiya (2): Tala Dhar Tap & Acharya Shantisagar Punyatithi.

    Render 2 events on Bhadrapada Shukla Dwitiya:
    1. Acharya Shantisagar Punyatithi (Samadhi Divas)
    2. Tala Dhar Tap

    Vriddhi: Assign strictly to 1st Dwitiya instance.
    Kshaya : Trigger and render on Bhadrapada Shukla Ekam (1).
    Adhik  : Execute strictly during Adhik Bhadrapada if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        bhadra_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["BHADRAPADA", "BHADWA", "BHADRA"]
        ]
        if not bhadra_snaps:
            return []

        if any(s["is_adhika"] for s in bhadra_snaps):
            bhadra_snaps = [s for s in bhadra_snaps if s["is_adhika"]]
        else:
            bhadra_snaps = [s for s in bhadra_snaps if not s["is_adhika"]]

        dwitiya_days = [
            s for s in bhadra_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 2
        ]

        target_snap = None
        if dwitiya_days:
            target_snap = dwitiya_days[0]  # Vriddhi -> 1st Dwitiya
        else:
            # Kshaya: fallback to Bhadrapada Shukla Ekam (1)
            ekam_days = [
                s for s in bhadra_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 1
            ]
            if ekam_days:
                target_snap = ekam_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"acharya_shantisagar_punyatithi_{year}",
                "occurrence_id": f"acharya_shantisagar_punyatithi_{year}",
                "name": "Acharya Shantisagar Punyatithi (Samadhi Divas)",
                "title": "Acharya Shantisagar Punyatithi (Samadhi Divas)",
                "name_hindi": "आचार्य शांतिसागर पुण्यतिथि (समाधि दिवस)",
                "category": "punyatithi",
                "badge": "Samadhi Divas",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Punyatithi and Samadhi aradhana of Charitra Chakravarti 108 Acharya Shri Shantisagar Ji Maharaj",
                "meaning": "Punyatithi and Samadhi aradhana of Charitra Chakravarti 108 Acharya Shri Shantisagar Ji Maharaj",
                "observance": "Samadhi Aradhana, Swadhyay, and Viniyojita Tap",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"tala_dhar_tap_{year}",
                "occurrence_id": f"tala_dhar_tap_{year}",
                "name": "Tala Dhar Tap",
                "title": "Tala Dhar Tap",
                "name_hindi": "ताला धार तप",
                "category": "tap_vrat",
                "badge": "Tap",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Observance of Tala Dhar Tap aradhana on Bhadrapada Shukla Dwitiya",
                "meaning": "Observance of Tala Dhar Tap aradhana on Bhadrapada Shukla Dwitiya",
                "observance": "Austere penance and Tala Dhar Tap fasting",
                "sources": ["Jain Traditions"]
            }
        ]


class BadiPanchamiMeruSthapanaFestival(FestivalRule):
    """Bhadrapada Shukla Panchami (5): Badi Panchami & Meru Sthapana Engine Logic.

    Render 2 events on Bhadrapada Shukla Panchami:
    1. Badi Panchami
    2. Meru Sthapana (Sudarshan Meru Pujan)

    Vriddhi: Assign strictly to 1st Panchami instance.
    Kshaya : Trigger and render on Bhadrapada Shukla Chaturthi (4).
    Adhik  : Execute strictly during Adhik Bhadrapada if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        bhadra_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["BHADRAPADA", "BHADWA", "BHADRA"]
        ]
        if not bhadra_snaps:
            return []

        if any(s["is_adhika"] for s in bhadra_snaps):
            bhadra_snaps = [s for s in bhadra_snaps if s["is_adhika"]]
        else:
            bhadra_snaps = [s for s in bhadra_snaps if not s["is_adhika"]]

        panchami_days = [
            s for s in bhadra_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 5
        ]

        target_snap = None
        if panchami_days:
            target_snap = panchami_days[0]  # Vriddhi -> 1st Panchami
        else:
            # Kshaya: fallback to Bhadrapada Shukla Chaturthi (4)
            chaturthi_days = [
                s for s in bhadra_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 4
            ]
            if chaturthi_days:
                target_snap = chaturthi_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"badi_panchami_{year}",
                "occurrence_id": f"badi_panchami_{year}",
                "name": "Badi Panchami",
                "title": "Badi Panchami",
                "name_hindi": "बड़ी पंचमी",
                "category": "mahaparv",
                "badge": "Badi Panchami",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Bhadrapada Shukla Panchami aradhana dedicated to Badi Panchami (Jain Rishi Panchami aradhana)",
                "meaning": "Bhadrapada Shukla Panchami aradhana dedicated to Badi Panchami (Jain Rishi Panchami aradhana)",
                "observance": "Swadhyay, Muni Vandan, and Rishi Panchami Aradhana",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"meru_sthapana_{year}",
                "occurrence_id": f"meru_sthapana_{year}",
                "name": "Meru Sthapana (Sudarshan Meru Pujan)",
                "title": "Meru Sthapana (Sudarshan Meru Pujan)",
                "name_hindi": "मेरु स्थापना (सुदर्शन मेरु पूजन)",
                "category": "parv_vidhi",
                "badge": "Meru Sthapana",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Ceremonial sthapana and pujan of Sumeru Parvat and Akrtrim Jinalayas",
                "meaning": "Ceremonial sthapana and pujan of Sumeru Parvat and Akrtrim Jinalayas",
                "observance": "Meru Sthapana, Akrtrim Chaityalaya Pujan",
                "sources": ["Jain Traditions"]
            }
        ]


class NihshalyaAshtamiManchinTithiFestival(FestivalRule):
    """Bhadrapada Shukla Ashtami (8): Nihshalya Ashtami Vrat & Manchin Tithi Ashtami.

    Render 2 events on Bhadrapada Shukla Ashtami:
    1. Nihshalya Ashtami Vrat
    2. Manchin Tithi Ashtami

    Vriddhi: Assign strictly to 1st Ashtami instance.
    Kshaya : Trigger and render on Bhadrapada Shukla Saptami (7).
    Adhik  : Execute strictly during Adhik Bhadrapada if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        bhadra_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["BHADRAPADA", "BHADWA", "BHADRA"]
        ]
        if not bhadra_snaps:
            return []

        if any(s["is_adhika"] for s in bhadra_snaps):
            bhadra_snaps = [s for s in bhadra_snaps if s["is_adhika"]]
        else:
            bhadra_snaps = [s for s in bhadra_snaps if not s["is_adhika"]]

        ashtami_days = [
            s for s in bhadra_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 8
        ]

        target_snap = None
        if ashtami_days:
            target_snap = ashtami_days[0]  # Vriddhi -> 1st Ashtami
        else:
            # Kshaya: fallback to Bhadrapada Shukla Saptami (7)
            saptami_days = [
                s for s in bhadra_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 7
            ]
            if saptami_days:
                target_snap = saptami_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"nihshalya_ashtami_vrat_{year}",
                "occurrence_id": f"nihshalya_ashtami_vrat_{year}",
                "name": "Nihshalya Ashtami Vrat",
                "title": "Nihshalya Ashtami Vrat",
                "name_hindi": "निःशल्य अष्टमी व्रत",
                "category": "vrat",
                "badge": "Vrat",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Bhadrapada Shukla Ashtami aradhana dedicated to eradication of the three inner shalyas (Maya, Mithya, Nidan)",
                "meaning": "Bhadrapada Shukla Ashtami aradhana dedicated to eradication of the three inner shalyas (Maya, Mithya, Nidan)",
                "observance": "Fasting and Shalya-Tyaga Aradhana",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"manchin_tithi_ashtami_{year}",
                "occurrence_id": f"manchin_tithi_ashtami_{year}",
                "name": "Manchin Tithi Ashtami",
                "title": "Manchin Tithi Ashtami",
                "name_hindi": "मानछीन तिथि अष्टमी",
                "category": "parv_vidhi",
                "badge": "Manchin Tithi",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Contemplative aradhana focused on shedding ego and subduing Maan Kashaya",
                "meaning": "Contemplative aradhana focused on shedding ego and subduing Maan Kashaya",
                "observance": "Uttama Mardava Swadhyay and Maan-Chheen Dhyana",
                "sources": ["Jain Traditions"]
            }
        ]


class SugandhDashamiFestival(FestivalRule):
    """Bhadrapada Shukla Dashami (10): Sugandh Dashami / Dhoop Dashami Engine Logic.

    Render 2 events on Bhadrapada Shukla Dashami:
    1. Sugandh Dashami (Dhoop Dashami Mahaparv)
    2. Sugandh Dashami Vrat

    Vriddhi: Assign strictly to 1st Dashami instance.
    Kshaya : Trigger and render on Bhadrapada Shukla Navami (9).
    Adhik  : Execute strictly during Adhik Bhadrapada if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        bhadra_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["BHADRAPADA", "BHADWA", "BHADRA"]
        ]
        if not bhadra_snaps:
            return []

        if any(s["is_adhika"] for s in bhadra_snaps):
            bhadra_snaps = [s for s in bhadra_snaps if s["is_adhika"]]
        else:
            bhadra_snaps = [s for s in bhadra_snaps if not s["is_adhika"]]

        dashami_days = [
            s for s in bhadra_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 10
        ]

        target_snap = None
        if dashami_days:
            target_snap = dashami_days[0]  # Vriddhi -> 1st Dashami
        else:
            # Kshaya: fallback to Bhadrapada Shukla Navami (9)
            navami_days = [
                s for s in bhadra_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 9
            ]
            if navami_days:
                target_snap = navami_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"sugandh_dashami_mahaparv_{year}",
                "occurrence_id": f"sugandh_dashami_mahaparv_{year}",
                "name": "Sugandh Dashami (Dhoop Dashami Mahaparv)",
                "title": "Sugandh Dashami (Dhoop Dashami Mahaparv)",
                "name_hindi": "सुगन्ध दशमी (धूप दशमी महापर्व)",
                "category": "mahaparv",
                "badge": "Sugandh Dashami",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Bhadrapada Shukla Dashami aradhana: Offering sacred Dhoop in Jinalayas to destroy internal karmas and cultivate spiritual purity",
                "meaning": "Bhadrapada Shukla Dashami aradhana: Offering sacred Dhoop in Jinalayas to destroy internal karmas and cultivate spiritual purity",
                "observance": "Dhoop Aradhana in Jinalayas, Jin Pujan, Swadhyay",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"sugandh_dashami_vrat_{year}",
                "occurrence_id": f"sugandh_dashami_vrat_{year}",
                "name": "Sugandh Dashami Vrat",
                "title": "Sugandh Dashami Vrat",
                "name_hindi": "सुगन्ध दशमी व्रत",
                "category": "vrat",
                "badge": "Vrat",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Fasting and aradhana dedicated to Sugandh Dashami during Das Lakshan Parv",
                "meaning": "Fasting and aradhana dedicated to Sugandh Dashami during Das Lakshan Parv",
                "observance": "Fasting, Swadhyay, and Dhoop Dashami Aradhana",
                "sources": ["Jain Traditions"]
            }
        ]


class AnantChaturdashiVratFestival(FestivalRule):
    """Anant Chaturdashi Vrat: Bhadrapada Shukla Ekadashi to Chaturdashi.

    Start: Bhadrapada Shukla Ekadashi (11) (Vriddhi -> 1st Ekadashi, Kshaya -> Bhadrapada Shukla Dashami 10).
    End: Bhadrapada Shukla Chaturdashi (14) (Vriddhi -> 2nd Chaturdashi, Kshaya -> Bhadrapada Shukla Trayodashi 13).
    Adhik Maas: Execute strictly during Adhik Bhadrapada if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        bhadra_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["BHADRAPADA", "BHADWA", "BHADRA"]
        ]
        if not bhadra_snaps:
            return []

        if any(s["is_adhika"] for s in bhadra_snaps):
            bhadra_snaps = [s for s in bhadra_snaps if s["is_adhika"]]
        else:
            bhadra_snaps = [s for s in bhadra_snaps if not s["is_adhika"]]

        # Start boundary: Ekadashi (11) -> Vriddhi: 1st Ekadashi, Kshaya: Dashami (10)
        ekadashi_days = [
            s for s in bhadra_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 11
        ]
        if ekadashi_days:
            start_snap = ekadashi_days[0]
        else:
            dashami_days = [
                s for s in bhadra_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 10
            ]
            start_snap = dashami_days[-1] if dashami_days else None

        # End boundary: Chaturdashi (14) -> Vriddhi: 2nd Chaturdashi, Kshaya: Trayodashi (13)
        chaturdashi_days = [
            s for s in bhadra_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 14
        ]
        if chaturdashi_days:
            end_snap = chaturdashi_days[-1]  # Vriddhi -> 2nd Chaturdashi
        else:
            trayodashi_days = [
                s for s in bhadra_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 13
            ]
            end_snap = trayodashi_days[-1] if trayodashi_days else None

        if not start_snap or not end_snap:
            return []

        start_date_str = start_snap["date"].isoformat()
        end_date_str = end_snap["date"].isoformat()

        start_mm_dd = start_snap["date"].strftime("%m-%d")
        end_mm_dd = end_snap["date"].strftime("%m-%d")
        span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

        return [
            {
                "id": f"anant_vrat_prarambh_{year}",
                "occurrence_id": f"anant_vrat_prarambh_{year}",
                "name": "Anant Vrat Prarambh",
                "title": "Anant Vrat Prarambh",
                "name_hindi": "अनंत व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "START",
                "description": "Commencement of Anant Chaturdashi Vrat (Aradhana of 14-Guṇa Anant Dharma)",
                "meaning": "Commencement of Anant Chaturdashi Vrat (Aradhana of 14-Guṇa Anant Dharma)",
                "observance": "Fasting, Anant Sutra Aradhana",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"anant_chaturdashi_purna_{year}",
                "occurrence_id": f"anant_chaturdashi_purna_{year}",
                "name": "Anant Chaturdashi (Anant Vrat Purna)",
                "title": "Anant Chaturdashi (Anant Vrat Purna)",
                "name_hindi": "अनंत चतुर्दशी (अनंत व्रत पूर्ण)",
                "category": "mahaparv",
                "badge": "Mahaparv",
                "badge_color": "pink",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "END",
                "description": "Conclusion of Anant Vrat, Das Lakshan Parv finale, and 14th Tirthankara Shri Anantnath Bhagwan Moksha Kalyanak",
                "meaning": "Conclusion of Anant Vrat, Das Lakshan Parv finale, and 14th Tirthankara Shri Anantnath Bhagwan Moksha Kalyanak",
                "observance": "Das Lakshan Purna, Anantnath Bhagwan Moksha Kalyanak Pujan",
                "sources": ["Jain Traditions"]
            }
        ]


class RatnatrayaSankatHaranVratFestival(FestivalRule):
    """Ratnatraya Vrat & Sankat Haran Vrat: Bhadrapada Shukla Trayodashi to Purnima.

    Start: Bhadrapada Shukla Trayodashi (13) (Vriddhi -> 1st Trayodashi, Kshaya -> Dvadashi 12).
    End: Bhadrapada Shukla Purnima (15) (Vriddhi -> 2nd Purnima, Kshaya -> Chaturdashi 14).
    Adhik Maas: Execute strictly during Adhik Bhadrapada if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        bhadra_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["BHADRAPADA", "BHADWA", "BHADRA"]
        ]
        if not bhadra_snaps:
            return []

        if any(s["is_adhika"] for s in bhadra_snaps):
            bhadra_snaps = [s for s in bhadra_snaps if s["is_adhika"]]
        else:
            bhadra_snaps = [s for s in bhadra_snaps if not s["is_adhika"]]

        # Start boundary: Trayodashi (13) -> Vriddhi: 1st Trayodashi, Kshaya: Dvadashi (12)
        trayodashi_days = [
            s for s in bhadra_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 13
        ]
        if trayodashi_days:
            start_snap = trayodashi_days[0]
        else:
            dvadashi_days = [
                s for s in bhadra_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 12
            ]
            start_snap = dvadashi_days[-1] if dvadashi_days else None

        # End boundary: Purnima (15) -> Vriddhi: 2nd Purnima, Kshaya: Chaturdashi (14)
        purnima_days = [
            s for s in bhadra_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] in [15, 30]
        ]
        if purnima_days:
            end_snap = purnima_days[-1]  # Vriddhi -> 2nd Purnima
        else:
            chaturdashi_days = [
                s for s in bhadra_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 14
            ]
            end_snap = chaturdashi_days[-1] if chaturdashi_days else None

        if not start_snap or not end_snap:
            return []

        start_date_str = start_snap["date"].isoformat()
        end_date_str = end_snap["date"].isoformat()

        start_mm_dd = start_snap["date"].strftime("%m-%d")
        end_mm_dd = end_snap["date"].strftime("%m-%d")
        span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

        return [
            {
                "id": f"ratnatraya_vrat_prarambh_{year}",
                "occurrence_id": f"ratnatraya_vrat_prarambh_{year}",
                "name": "Ratnatraya Vrat Prarambh",
                "title": "Ratnatraya Vrat Prarambh",
                "name_hindi": "रत्नत्रय व्रत प्रारम्भ",
                "category": "mahaparv_vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "START",
                "description": "Commencement of 3-day Ratnatraya Vrat (Aradhana of Samyak Darshan, Jnana, Charitra)",
                "meaning": "Commencement of 3-day Ratnatraya Vrat (Aradhana of Samyak Darshan, Jnana, Charitra)",
                "observance": "Fasting, Ratnatraya Aradhana, Swadhyay",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"sankat_haran_vrat_prarambh_{year}",
                "occurrence_id": f"sankat_haran_vrat_prarambh_{year}",
                "name": "Sankat Haran Vrat Prarambh",
                "title": "Sankat Haran Vrat Prarambh",
                "name_hindi": "संकट हरण व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "START",
                "description": "Commencement of Sankat Haran Vrat on Bhadrapada Shukla Trayodashi",
                "meaning": "Commencement of Sankat Haran Vrat on Bhadrapada Shukla Trayodashi",
                "observance": "Fasting and Sankat Haran Aradhana",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"ratnatraya_vrat_purna_{year}",
                "occurrence_id": f"ratnatraya_vrat_purna_{year}",
                "name": "Ratnatraya Vrat Purna",
                "title": "Ratnatraya Vrat Purna",
                "name_hindi": "रत्नत्रय व्रत पूर्ण",
                "category": "mahaparv_vrat",
                "badge": "Vrat End",
                "badge_color": "pink",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "END",
                "description": "Conclusion and Nishthapan of Ratnatraya Vrat on Bhadrapada Purnima",
                "meaning": "Conclusion and Nishthapan of Ratnatraya Vrat on Bhadrapada Purnima",
                "observance": "Ratnatraya Vrat Conclusion, Purna Ahuti",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"sankat_haran_vrat_purna_{year}",
                "occurrence_id": f"sankat_haran_vrat_purna_{year}",
                "name": "Sankat Haran Vrat Purna",
                "title": "Sankat Haran Vrat Purna",
                "name_hindi": "संकट हरण व्रत पूर्ण",
                "category": "vrat",
                "badge": "Vrat End",
                "badge_color": "pink",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "END",
                "description": "Conclusion and Nishthapan of Sankat Haran Vrat",
                "meaning": "Conclusion and Nishthapan of Sankat Haran Vrat",
                "observance": "Conclusion of Sankat Haran Vrat",
                "sources": ["Jain Traditions"]
            }
        ]


class KshamavaniMahaparvFestival(FestivalRule):
    """Ashwin Krishna Ekam (1): Kshamavani Mahaparv (Kshamadwani Divas) Engine Logic.

    Target: Ashwin Krishna Ekam (1).
    Vriddhi: Assign strictly to 1st Ekam.
    Kshaya : Fallback to Bhadrapada Shukla Purnima (15).
    Adhik  : Execute strictly during Adhik Ashwin if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        ashwin_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["ASHWIN", "ASO", "ASOJ", "ASHVINA"]
        ]
        if not ashwin_snaps:
            return []

        if any(s["is_adhika"] for s in ashwin_snaps):
            ashwin_snaps = [s for s in ashwin_snaps if s["is_adhika"]]
        else:
            ashwin_snaps = [s for s in ashwin_snaps if not s["is_adhika"]]

        ekam_days = [
            s for s in ashwin_snaps
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 1
        ]

        target_snap = None
        if ekam_days:
            target_snap = ekam_days[0]  # Vriddhi -> 1st Ekam
        else:
            # Kshaya: fallback to Bhadrapada Shukla Purnima (15)
            bhadra_snaps = [
                s for s in snapshots
                if s["date"].year == year
                and s["hindu_month"].upper() in ["BHADRAPADA", "BHADWA", "BHADRA"]
                and not s["is_adhika"]
                and s["paksha"] == "Shukla"
                and s["tithi_in_paksha"] in [15, 30]
            ]
            if bhadra_snaps:
                target_snap = bhadra_snaps[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"kshamavani_mahaparv_{year}",
                "occurrence_id": f"kshamavani_mahaparv_{year}",
                "name": "Kshamavani Mahaparv (Kshamadwani Divas)",
                "title": "Kshamavani Mahaparv (Kshamadwani Divas)",
                "name_hindi": "क्षमावाणी महापर्व (क्षमावाणी दिवस)",
                "category": "mahaparv",
                "badge": "Kshamavani",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Grand Day of Universal Forgiveness (Digambara tradition) following Das Lakshan Parv: Seeking and extending Uttam Kshama to all living beings",
                "meaning": "Grand Day of Universal Forgiveness (Digambara tradition) following Das Lakshan Parv: Seeking and extending Uttam Kshama to all living beings",
                "observance": "Uttam Kshama, Universal Forgiveness (Micchami Dukkadam), Kshamavani Gathering",
                "sources": ["Jain Traditions"]
            }
        ]


class ShraddhaVratFestival(FestivalRule):
    """Shraddha Vrat: Ashwin Shukla Ekam (1) to Kartika Krishna Ekam (1).

    Start: Ashwin Shukla Ekam (Vriddhi -> 1st Ekam, Kshaya -> Ashwin Krishna Amavasya).
    End: Kartika Krishna Ekam (Vriddhi -> 2nd Ekam, Kshaya -> Ashwin Shukla Purnima).
    Adhik Maas: Execute strictly during Adhik Maas if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        # Ashwin snapshots
        ashwin_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["ASHWIN", "ASO", "ASOJ", "ASHVINA"]
        ]
        if not ashwin_snaps:
            return []

        if any(s["is_adhika"] for s in ashwin_snaps):
            ashwin_snaps = [s for s in ashwin_snaps if s["is_adhika"]]
        else:
            ashwin_snaps = [s for s in ashwin_snaps if not s["is_adhika"]]

        # Kartika snapshots
        kartika_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["KARTIKA", "KATAK", "KARTIK"]
        ]

        if any(s["is_adhika"] for s in kartika_snaps):
            kartika_snaps = [s for s in kartika_snaps if s["is_adhika"]]
        else:
            kartika_snaps = [s for s in kartika_snaps if not s["is_adhika"]]

        # Start boundary: Ashwin Shukla Ekam (1) -> Vriddhi: 1st Ekam, Kshaya: Ashwin Krishna Amavasya (15/30)
        ashwin_shukla_ekam = [
            s for s in ashwin_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 1
        ]
        if ashwin_shukla_ekam:
            start_snap = ashwin_shukla_ekam[0]
        else:
            ashwin_krishna_amavasya = [
                s for s in ashwin_snaps
                if s["paksha"] == "Krishna" and s["tithi_in_paksha"] in [15, 30]
            ]
            start_snap = ashwin_krishna_amavasya[-1] if ashwin_krishna_amavasya else None

        # End boundary: Kartika Krishna Ekam (1) -> Vriddhi: 2nd Ekam, Kshaya: Ashwin Shukla Purnima (15/30)
        kartika_krishna_ekam = [
            s for s in kartika_snaps
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 1
        ]
        if kartika_krishna_ekam:
            end_snap = kartika_krishna_ekam[-1]  # Vriddhi -> 2nd Ekam
        else:
            ashwin_purnima = [
                s for s in ashwin_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] in [15, 30]
            ]
            end_snap = ashwin_purnima[-1] if ashwin_purnima else None

        if not start_snap or not end_snap:
            return []

        start_date_str = start_snap["date"].isoformat()
        end_date_str = end_snap["date"].isoformat()

        start_mm_dd = start_snap["date"].strftime("%m-%d")
        end_mm_dd = end_snap["date"].strftime("%m-%d")
        span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

        return [
            {
                "id": f"shraddha_vrat_prarambh_{year}",
                "occurrence_id": f"shraddha_vrat_prarambh_{year}",
                "name": "Shraddha Vrat Prarambh",
                "title": "Shraddha Vrat Prarambh",
                "name_hindi": "श्रद्धा व्रत प्रारम्भ",
                "category": "vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "START",
                "description": "Commencement of month-long Shraddha Vrat (Aradhana of Samyak Darshan and pure faith)",
                "meaning": "Commencement of month-long Shraddha Vrat (Aradhana of Samyak Darshan and pure faith)",
                "observance": "Fasting and Samyak Shraddha Aradhana",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"shraddha_vrat_purna_{year}",
                "occurrence_id": f"shraddha_vrat_purna_{year}",
                "name": "Shraddha Vrat Purna",
                "title": "Shraddha Vrat Purna",
                "name_hindi": "श्रद्धा व्रत पूर्ण",
                "category": "vrat",
                "badge": "Vrat End",
                "badge_color": "pink",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "END",
                "description": "Conclusion and Nishthapan of Shraddha Vrat",
                "meaning": "Conclusion and Nishthapan of Shraddha Vrat",
                "observance": "Conclusion of Shraddha Vrat",
                "sources": ["Jain Traditions"]
            }
        ]


class NavapadOliVratFestival(FestivalRule):
    """Navapad Oli (Ayambil Oli) Vrat: Shukla Saptami (7) to Purnima (15) Boundaries.

    Executes for Chaitra and Ashwin.
    Start: Shukla Saptami (7) (Vriddhi -> 1st Saptami, Kshaya -> Shukla Shashthi 6).
    End: Shukla Purnima (15) (Vriddhi -> 2nd Purnima, Kshaya -> Shukla Chaturdashi 14).
    Adhik Maas: Execute strictly during Adhik Maas if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        events = []

        for target_month, season_key in [("CHAITRA", "chaitra"), ("ASHWIN", "ashwin")]:
            m_snaps = [
                s for s in snapshots
                if s["date"].year == year
                and s["hindu_month"].upper() in [target_month, "ASO", "ASOJ", "ASHVINA"]
            ]
            if not m_snaps:
                continue

            if any(s["is_adhika"] for s in m_snaps):
                m_snaps = [s for s in m_snaps if s["is_adhika"]]
            else:
                m_snaps = [s for s in m_snaps if not s["is_adhika"]]

            # Start boundary: Shukla Saptami (7) -> Vriddhi: 1st Saptami, Kshaya: Shukla Shashthi (6)
            saptami_days = [
                s for s in m_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 7
            ]
            if saptami_days:
                start_snap = saptami_days[0]
            else:
                shashthi_days = [
                    s for s in m_snaps
                    if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 6
                ]
                start_snap = shashthi_days[-1] if shashthi_days else None

            # End boundary: Shukla Purnima (15) -> Vriddhi: 2nd Purnima, Kshaya: Shukla Chaturdashi (14)
            purnima_days = [
                s for s in m_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] in [15, 30]
            ]
            if purnima_days:
                end_snap = purnima_days[-1]
            else:
                chaturdashi_days = [
                    s for s in m_snaps
                    if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 14
                ]
                end_snap = chaturdashi_days[-1] if chaturdashi_days else None

            if not start_snap or not end_snap:
                continue

            start_date_str = start_snap["date"].isoformat()
            end_date_str = end_snap["date"].isoformat()

            start_mm_dd = start_snap["date"].strftime("%m-%d")
            end_mm_dd = end_snap["date"].strftime("%m-%d")
            span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

            events.append({
                "id": f"navapad_oli_vrat_prarambh_{season_key}_{year}",
                "occurrence_id": f"navapad_oli_vrat_prarambh_{season_key}_{year}",
                "name": "Navapad Oli Prarambh (Ayambil Oli Start)",
                "title": "Navapad Oli Prarambh (Ayambil Oli Start)",
                "name_hindi": "नवपद ओली प्रारम्भ (आयांबिल ओली प्रारम्भ)",
                "category": "mahaparv_vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "START",
                "description": "Commencement of the 9-day Navapad Ayambil Oli aradhana (Shri Navapad Pujan & Tap)",
                "meaning": "Commencement of the 9-day Navapad Ayambil Oli aradhana (Shri Navapad Pujan & Tap)",
                "observance": "Ayambil Fasting, Navapad Pujan & Tap",
                "sources": ["Jain Traditions"]
            })

            events.append({
                "id": f"navapad_oli_vrat_purna_{season_key}_{year}",
                "occurrence_id": f"navapad_oli_vrat_purna_{season_key}_{year}",
                "name": "Navapad Oli Purna (Ayambil Oli Nishthapan)",
                "title": "Navapad Oli Purna (Ayambil Oli Nishthapan)",
                "name_hindi": "नवपद ओली पूर्ण (आयांबिल ओली निष्ठापन)",
                "category": "mahaparv_vrat",
                "badge": "Vrat End",
                "badge_color": "pink",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "is_span": True,
                "span_label": span_label,
                "boundary_type": "END",
                "description": "Conclusion and Nishthapan of 9-day Navapad Oli (Purnima Aradhana & Shripal Raja Smruti)",
                "meaning": "Conclusion and Nishthapan of 9-day Navapad Oli (Purnima Aradhana & Shripal Raja Smruti)",
                "observance": "Navapad Oli Nishthapan, Purnima Aradhana",
                "sources": ["Jain Traditions"]
            })

        return events


class JeevDayaAshtamiFestival(FestivalRule):
    """Ashwin Shukla Ashtami (8): Jeev Daya Ashtami Engine Logic.

    Target: Ashwin Shukla Ashtami (8).
    Vriddhi: Assign strictly to 1st Ashtami.
    Kshaya : Fallback to Ashwin Shukla Saptami (7).
    Adhik  : Execute strictly during Adhik Ashwin if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        ashwin_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["ASHWIN", "ASO", "ASOJ", "ASHVINA"]
        ]
        if not ashwin_snaps:
            return []

        if any(s["is_adhika"] for s in ashwin_snaps):
            ashwin_snaps = [s for s in ashwin_snaps if s["is_adhika"]]
        else:
            ashwin_snaps = [s for s in ashwin_snaps if not s["is_adhika"]]

        ashtami_days = [
            s for s in ashwin_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 8
        ]

        target_snap = None
        if ashtami_days:
            target_snap = ashtami_days[0]  # Vriddhi -> 1st Ashtami
        else:
            saptami_days = [
                s for s in ashwin_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 7
            ]
            if saptami_days:
                target_snap = saptami_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"jeev_daya_ashtami_{year}",
                "occurrence_id": f"jeev_daya_ashtami_{year}",
                "name": "Jeev Daya Ashtami",
                "title": "Jeev Daya Ashtami",
                "name_hindi": "जीव दया अष्टमी",
                "category": "mahaparv_vrat",
                "badge": "Jeev Daya",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Ashwin Shukla Ashtami aradhana dedicated to supreme non-violence (Ahimsa), animal protection (Abhayadan), and Karuna Bhavna during Navapad Oli",
                "meaning": "Ashwin Shukla Ashtami aradhana dedicated to supreme non-violence (Ahimsa), animal protection (Abhayadan), and Karuna Bhavna during Navapad Oli",
                "observance": "Ahimsa, Abhayadan, Gaushala Seva, Karuna Bhavna",
                "sources": ["Jain Traditions"]
            }
        ]


class SharadPurnimaJayantisFestival(FestivalRule):
    """Ashwin Shukla Purnima (15): Sharad Purnima, Acharya Vidyasagar Ji & Aryika Gyanmati Mataji Janma Jayanti Engine Logic.

    Target: Ashwin Shukla Purnima (15).
    Vriddhi: Assign strictly to 2nd Purnima.
    Kshaya : Fallback to Ashwin Shukla Chaturdashi (14).
    Adhik  : Execute strictly during Adhik Ashwin if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        ashwin_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["ASHWIN", "ASO", "ASOJ", "ASHVINA"]
        ]
        if not ashwin_snaps:
            return []

        if any(s["is_adhika"] for s in ashwin_snaps):
            ashwin_snaps = [s for s in ashwin_snaps if s["is_adhika"]]
        else:
            ashwin_snaps = [s for s in ashwin_snaps if not s["is_adhika"]]

        purnima_days = [
            s for s in ashwin_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] in [15, 30]
        ]

        target_snap = None
        if purnima_days:
            target_snap = purnima_days[-1]  # Vriddhi -> 2nd Purnima
        else:
            chaturdashi_days = [
                s for s in ashwin_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 14
            ]
            if chaturdashi_days:
                target_snap = chaturdashi_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"acharya_vidyasagar_jayanti_{year}",
                "occurrence_id": f"acharya_vidyasagar_jayanti_{year}",
                "name": "Acharya Vidyasagar Ji Maharaj Janma Jayanti",
                "title": "Acharya Vidyasagar Ji Maharaj Janma Jayanti",
                "name_hindi": "आचार्य विद्यासागर जी महाराज जन्म जयंती",
                "category": "jayanti",
                "badge": "Janma Jayanti",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Birth anniversary of Sant Shiromani 108 Acharya Shri Vidyasagar Ji Maharaj (Born on Sharad Purnima, Sadalga)",
                "meaning": "Birth anniversary of Sant Shiromani 108 Acharya Shri Vidyasagar Ji Maharaj (Born on Sharad Purnima, Sadalga)",
                "observance": "Gurudev Pujan, Gunasmaran, Pravachan, Sanyam Diwas",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"ganini_gyanmati_mataji_jayanti_{year}",
                "occurrence_id": f"ganini_gyanmati_mataji_jayanti_{year}",
                "name": "Ganini Aryika Gyanmati Mataji Janma Jayanti",
                "title": "Ganini Aryika Gyanmati Mataji Janma Jayanti",
                "name_hindi": "गणिनी आर्यिका ज्ञानमती माताजी जन्म जयंती",
                "category": "jayanti",
                "badge": "Janma Jayanti",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Birth anniversary celebration (Sharadotsav) of Ganini Pramukh Aryika Shri 105 Gyanmati Mataji",
                "meaning": "Birth anniversary celebration (Sharadotsav) of Ganini Pramukh Aryika Shri 105 Gyanmati Mataji",
                "observance": "Sharadotsav, Aryika Pujan, Agam Swadhyay",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"sharad_purnima_{year}",
                "occurrence_id": f"sharad_purnima_{year}",
                "name": "Sharad Purnima (Kojagiri Purnima)",
                "title": "Sharad Purnima (Kojagiri Purnima)",
                "name_hindi": "शरद पूर्णिमा (कोजागिरी पूर्णिमा)",
                "category": "mahaparv",
                "badge": "Sharad Purnima",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Ashwin Shukla Purnima aradhana, moonlight meditation, and conclusion of Ashwin Navapad Oli",
                "meaning": "Ashwin Shukla Purnima aradhana, moonlight meditation, and conclusion of Ashwin Navapad Oli",
                "observance": "Kojagiri Moonlight Aradhana, Kheer Bhog, Jin Pujan",
                "sources": ["Jain Traditions"]
            }
        ]


class SplitDayAhoiKarwaDampatyaFestival(FestivalRule):
    """Implementation of Vyapini vs Udaya Tithi engine logic:

    1. Karwa Chauth: Kartika Krishna Chaturthi (4) - Chandrodaya (Moonrise) Vyapini Rule.
    2. Ahoi Ashtami: Kartika Krishna Ashtami (8) - Pradosha (Sunset/Star Sighting) Vyapini Rule.
    3. Dampatya Ashtami: Kartika Krishna Ashtami (8) - Udaya Tithi (Sunrise) Rule.

    Adhik Maas: Execute strictly during Adhik Kartika if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        # Use get_jain_month() (purnimanta), not raw hindu_month (amanta) -- every target
        # tithi here is Krishna-paksha, which lives one amanta month earlier than its
        # purnimanta display name (see KALYANAK_AUDIT_NOTES.md); a raw amanta match here
        # silently lands one full lunar month late, every year.
        kartika_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and get_jain_month(s) == "KARTIKA"
        ]
        if not kartika_snaps:
            return []

        if any(s["is_adhika"] for s in kartika_snaps):
            kartika_snaps = [s for s in kartika_snaps if s["is_adhika"]]
        else:
            kartika_snaps = [s for s in kartika_snaps if not s["is_adhika"]]

        events = []

        # 1. Karwa Chauth (Chandrodaya Vyapini - Chaturthi 4)
        chaturthi_snaps = [
            s for s in kartika_snaps
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 4
        ]
        if chaturthi_snaps:
            kc_snap = chaturthi_snaps[0]
            kc_date_str = kc_snap["date"].isoformat()
            events.append({
                "id": f"karwa_chauth_{year}",
                "occurrence_id": f"karwa_chauth_{year}",
                "name": "Karwa Chauth (Kark Chaturthi)",
                "title": "Karwa Chauth (Kark Chaturthi)",
                "name_hindi": "करवा चौथ (करक चतुर्थी)",
                "category": "vrat",
                "badge": "Karwa Chauth",
                "badge_color": "pink",
                "start_date": kc_date_str,
                "end_date": kc_date_str,
                "status": "confirmed",
                "description": "Kartika Krishna Chaturthi fast observed during Chandrodaya (Moonrise) window",
                "meaning": "Kartika Krishna Chaturthi fast observed during Chandrodaya (Moonrise) window",
                "observance": "Chandrodaya Fasting, Moon Worship",
                "sources": ["Panchang Traditions"]
            })
        else:
            tritiya_snaps = [
                s for s in kartika_snaps
                if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 3
            ]
            if tritiya_snaps:
                kc_snap = tritiya_snaps[-1]
                kc_date_str = kc_snap["date"].isoformat()
                events.append({
                    "id": f"karwa_chauth_{year}",
                    "occurrence_id": f"karwa_chauth_{year}",
                    "name": "Karwa Chauth (Kark Chaturthi)",
                    "title": "Karwa Chauth (Kark Chaturthi)",
                    "name_hindi": "करवा चौथ (करक चतुर्थी)",
                    "category": "vrat",
                    "badge": "Karwa Chauth",
                    "badge_color": "pink",
                    "start_date": kc_date_str,
                    "end_date": kc_date_str,
                    "status": "confirmed",
                    "description": "Kartika Krishna Chaturthi fast observed during Chandrodaya (Moonrise) window",
                    "meaning": "Kartika Krishna Chaturthi fast observed during Chandrodaya (Moonrise) window",
                    "observance": "Chandrodaya Fasting, Moon Worship",
                    "sources": ["Panchang Traditions"]
                })

        # 2. Ahoi Ashtami (Pradosha Vyapini - Ashtami 8)
        # 3. Dampatya Ashtami (Udaya Tithi - Ashtami 8)
        ashtami_snaps = [
            s for s in kartika_snaps
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 8
        ]

        if ashtami_snaps:
            ahoi_snap = ashtami_snaps[0]
            ahoi_date_str = ahoi_snap["date"].isoformat()
            events.append({
                "id": f"ahoi_ashtami_{year}",
                "occurrence_id": f"ahoi_ashtami_{year}",
                "name": "Ahoi Ashtami",
                "title": "Ahoi Ashtami",
                "name_hindi": "अहोई अष्टमी",
                "category": "vrat",
                "badge": "Ahoi Ashtami",
                "badge_color": "pink",
                "start_date": ahoi_date_str,
                "end_date": ahoi_date_str,
                "status": "confirmed",
                "description": "Kartika Krishna Ashtami fast observed during Pradosha (Evening Star sighting) window",
                "meaning": "Kartika Krishna Ashtami fast observed during Pradosha (Evening Star sighting) window",
                "observance": "Pradosha Evening Fasting, Star Sighting",
                "sources": ["Panchang Traditions"]
            })

            dampatya_snap = ashtami_snaps[0]
            dampatya_date_str = dampatya_snap["date"].isoformat()
            events.append({
                "id": f"dampatya_ashtami_{year}",
                "occurrence_id": f"dampatya_ashtami_{year}",
                "name": "Dampatya Ashtami",
                "title": "Dampatya Ashtami",
                "name_hindi": "दम्पत्य अष्टमी",
                "category": "vrat",
                "badge": "Dampatya Ashtami",
                "badge_color": "pink",
                "start_date": dampatya_date_str,
                "end_date": dampatya_date_str,
                "status": "confirmed",
                "description": "Kartika Krishna Ashtami daytime vow and aradhana observed on Udaya Tithi",
                "meaning": "Kartika Krishna Ashtami daytime vow and aradhana observed on Udaya Tithi",
                "observance": "Udaya Tithi Vrat, Daytime Aradhana",
                "sources": ["Panchang Traditions"]
            })
        else:
            saptami_snaps = [
                s for s in kartika_snaps
                if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 7
            ]
            if saptami_snaps:
                snap = saptami_snaps[-1]
                date_str = snap["date"].isoformat()
                events.append({
                    "id": f"ahoi_ashtami_{year}",
                    "occurrence_id": f"ahoi_ashtami_{year}",
                    "name": "Ahoi Ashtami",
                    "title": "Ahoi Ashtami",
                    "name_hindi": "अहोई अष्टमी",
                    "category": "vrat",
                    "badge": "Ahoi Ashtami",
                    "badge_color": "pink",
                    "start_date": date_str,
                    "end_date": date_str,
                    "status": "confirmed",
                    "description": "Kartika Krishna Ashtami fast observed during Pradosha (Evening Star sighting) window",
                    "meaning": "Kartika Krishna Ashtami fast observed during Pradosha (Evening Star sighting) window",
                    "observance": "Pradosha Evening Fasting, Star Sighting",
                    "sources": ["Panchang Traditions"]
                })
                events.append({
                    "id": f"dampatya_ashtami_{year}",
                    "occurrence_id": f"dampatya_ashtami_{year}",
                    "name": "Dampatya Ashtami",
                    "title": "Dampatya Ashtami",
                    "name_hindi": "दम्पत्य अष्टमी",
                    "category": "vrat",
                    "badge": "Dampatya Ashtami",
                    "badge_color": "pink",
                    "start_date": date_str,
                    "end_date": date_str,
                    "status": "confirmed",
                    "description": "Kartika Krishna Ashtami daytime vow and aradhana observed on Udaya Tithi",
                    "meaning": "Kartika Krishna Ashtami daytime vow and aradhana observed on Udaya Tithi",
                    "observance": "Udaya Tithi Vrat, Daytime Aradhana",
                    "sources": ["Panchang Traditions"]
                })

        return events


class GyanDhanTrayodashiFestival(FestivalRule):
    """Kartika Krishna Trayodashi (13): Gyan Trayodashi & Dhan Trayodashi Engine Logic.

    Target: Kartika Krishna Trayodashi (13).
    Vriddhi: Assign strictly to 1st Trayodashi.
    Kshaya : Fallback to Kartika Krishna Dvadashi (12).
    Adhik  : Execute strictly during Adhik Kartika if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        # Use get_jain_month() (purnimanta), not raw hindu_month (amanta) -- the target
        # tithi is Krishna-paksha Trayodashi, which lives one amanta month earlier than
        # its purnimanta display name (see KALYANAK_AUDIT_NOTES.md); a raw amanta match
        # here silently lands one full lunar month late, every year.
        kartika_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and get_jain_month(s) == "KARTIKA"
        ]
        if not kartika_snaps:
            return []

        if any(s["is_adhika"] for s in kartika_snaps):
            kartika_snaps = [s for s in kartika_snaps if s["is_adhika"]]
        else:
            kartika_snaps = [s for s in kartika_snaps if not s["is_adhika"]]

        trayodashi_days = [
            s for s in kartika_snaps
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 13
        ]

        target_snap = None
        if trayodashi_days:
            target_snap = trayodashi_days[0]  # Vriddhi -> 1st Trayodashi
        else:
            dvadashi_days = [
                s for s in kartika_snaps
                if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 12
            ]
            if dvadashi_days:
                target_snap = dvadashi_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"gyan_trayodashi_{year}",
                "occurrence_id": f"gyan_trayodashi_{year}",
                "name": "Gyan Trayodashi (Jnana Trayodashi)",
                "title": "Gyan Trayodashi (Jnana Trayodashi)",
                "name_hindi": "ज्ञान त्रयोदशी (ज्ञान तेरस)",
                "category": "mahaparv_vrat",
                "badge": "Gyan Trayodashi",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Kartika Krishna Trayodashi aradhana dedicated to pure knowledge (Samyak Jnana), Shastra Pujan, and commencement of Diwali Mahaparv",
                "meaning": "Kartika Krishna Trayodashi aradhana dedicated to pure knowledge (Samyak Jnana), Shastra Pujan, and commencement of Diwali Mahaparv",
                "observance": "Samyak Jnana Aradhana, Shastra Pujan, Jin Agam Vachana",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"dhan_teras_{year}",
                "occurrence_id": f"dhan_teras_{year}",
                "name": "Dhan Trayodashi (Dhanteras)",
                "title": "Dhan Trayodashi (Dhanteras)",
                "name_hindi": "धन त्रयोदशी (धनतेरस)",
                "category": "mahaparv",
                "badge": "Dhanteras",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Aradhana of spiritual wealth (Ratnatraya / Atma-Dhan) and initiation of the 5-day Mahavira Nirvana Mahotsav",
                "meaning": "Aradhana of spiritual wealth (Ratnatraya / Atma-Dhan) and initiation of the 5-day Mahavira Nirvana Mahotsav",
                "observance": "Atma-Dhan Aradhana, Deepotsav Initiation, Lakshmi-Saraswati Pujan",
                "sources": ["Jain Traditions"]
            }
        ]


class KartikaAmavasyaMahaviraNirvanaFestival(FestivalRule):
    """Kartika Krishna Amavasya (30/15): Bhagwan Mahavira Nirvana, Varsha Yog Nishthapan & Gautam Swami Kevalgyan Engine Logic.

    Target: Kartika Krishna Amavasya (30/15).
    Vriddhi: 1st Amavasya for Nirvana Kalyanak & Varsha Yog Nishthapan; 2nd Amavasya for Gautam Gandhar Kevalgyan.
    Kshaya : Fallback to Kartika Krishna Chaturdashi (14).
    Adhik  : Execute strictly during Adhik Kartika if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        # Use get_jain_month() (purnimanta), not raw hindu_month (amanta) -- the target
        # tithi is Krishna-paksha Amavasya, which lives one amanta month earlier than its
        # purnimanta display name (see KALYANAK_AUDIT_NOTES.md); a raw amanta match here
        # silently lands one full lunar month late, every year -- this was duplicating the
        # whole Mahavir Nirvana/Diwali cluster a month after its correct occurrence.
        kartika_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and get_jain_month(s) == "KARTIKA"
        ]
        if not kartika_snaps:
            return []

        if any(s["is_adhika"] for s in kartika_snaps):
            kartika_snaps = [s for s in kartika_snaps if s["is_adhika"]]
        else:
            kartika_snaps = [s for s in kartika_snaps if not s["is_adhika"]]

        amavasya_days = [
            s for s in kartika_snaps
            if s["paksha"] == "Krishna" and s["tithi_in_paksha"] in [15, 30]
        ]

        events = []
        if len(amavasya_days) >= 2:
            # Vriddhi
            d1_str = amavasya_days[0]["date"].isoformat()
            d2_str = amavasya_days[1]["date"].isoformat()

            events.append({
                "id": f"mahavira_nirvana_kalyanak_{year}",
                "occurrence_id": f"mahavira_nirvana_kalyanak_{year}",
                "name": "Bhagwan Mahavira Nirvana Kalyanak (Diwali)",
                "title": "Bhagwan Mahavira Nirvana Kalyanak (Diwali)",
                "name_hindi": "भगवान महावीर निर्वाण कल्याणक (दीपावली)",
                "category": "mahaparv",
                "badge": "Moksha Kalyanak",
                "badge_color": "pink",
                "start_date": d1_str,
                "end_date": d1_str,
                "status": "confirmed",
                "description": "Liberation (Moksha) of 24th Tirthankara Bhagwan Mahavira at Pavapuri; offering of the sacred Nirvana Laddu at dawn",
                "meaning": "Liberation (Moksha) of 24th Tirthankara Bhagwan Mahavira at Pavapuri; offering of the sacred Nirvana Laddu at dawn",
                "observance": "Nirvana Laddu Offering, Moksha Kalyan Pujan, Deepotsav",
                "sources": ["Jain Traditions"]
            })
            events.append({
                "id": f"varsha_yog_nishthapan_{year}",
                "occurrence_id": f"varsha_yog_nishthapan_{year}",
                "name": "Varsha Yog Nishthapan (Chaturmas Conclusion)",
                "title": "Varsha Yog Nishthapan (Chaturmas Conclusion)",
                "name_hindi": "वर्षा योग निष्ठापन (चातुर्मास समाप्ति)",
                "category": "mahaparv",
                "badge": "Nishthapan",
                "badge_color": "pink",
                "start_date": d1_str,
                "end_date": d1_str,
                "status": "confirmed",
                "description": "Formal completion and conclusion of the 4-month monsoon ascetic stay (Varshayoga / Chaturmas) for Jain sadhus",
                "meaning": "Formal completion and conclusion of the 4-month monsoon ascetic stay (Varshayoga / Chaturmas) for Jain sadhus",
                "observance": "Varsha Yog Nishthapan Vidhi, Chaturmas Parana",
                "sources": ["Jain Traditions"]
            })
            events.append({
                "id": f"gautam_gandhar_kevalgyan_{year}",
                "occurrence_id": f"gautam_gandhar_kevalgyan_{year}",
                "name": "Gautam Gandhar Kevalgyan Mahotsav",
                "title": "Gautam Gandhar Kevalgyan Mahotsav",
                "name_hindi": "गौतम गणधर केवलज्ञान महोत्सव",
                "category": "mahaparv",
                "badge": "Kevalgyan",
                "badge_color": "pink",
                "start_date": d2_str,
                "end_date": d2_str,
                "status": "confirmed",
                "description": "Attainment of supreme omniscience (Kevalgyana) by Pratham Gandhar Gautam Swami",
                "meaning": "Attainment of supreme omniscience (Kevalgyana) by Pratham Gandhar Gautam Swami",
                "observance": "Gautam Swami Pujan, Kevalgyan Aradhana",
                "sources": ["Jain Traditions"]
            })
        elif len(amavasya_days) == 1:
            # Normal
            d_str = amavasya_days[0]["date"].isoformat()
            events.append({
                "id": f"mahavira_nirvana_kalyanak_{year}",
                "occurrence_id": f"mahavira_nirvana_kalyanak_{year}",
                "name": "Bhagwan Mahavira Nirvana Kalyanak (Diwali)",
                "title": "Bhagwan Mahavira Nirvana Kalyanak (Diwali)",
                "name_hindi": "भगवान महावीर निर्वाण कल्याणक (दीपावली)",
                "category": "mahaparv",
                "badge": "Moksha Kalyanak",
                "badge_color": "pink",
                "start_date": d_str,
                "end_date": d_str,
                "status": "confirmed",
                "description": "Liberation (Moksha) of 24th Tirthankara Bhagwan Mahavira at Pavapuri; offering of the sacred Nirvana Laddu at dawn",
                "meaning": "Liberation (Moksha) of 24th Tirthankara Bhagwan Mahavira at Pavapuri; offering of the sacred Nirvana Laddu at dawn",
                "observance": "Nirvana Laddu Offering, Moksha Kalyan Pujan, Deepotsav",
                "sources": ["Jain Traditions"]
            })
            events.append({
                "id": f"varsha_yog_nishthapan_{year}",
                "occurrence_id": f"varsha_yog_nishthapan_{year}",
                "name": "Varsha Yog Nishthapan (Chaturmas Conclusion)",
                "title": "Varsha Yog Nishthapan (Chaturmas Conclusion)",
                "name_hindi": "वर्षा योग निष्ठापन (चातुर्मास समाप्ति)",
                "category": "mahaparv",
                "badge": "Nishthapan",
                "badge_color": "pink",
                "start_date": d_str,
                "end_date": d_str,
                "status": "confirmed",
                "description": "Formal completion and conclusion of the 4-month monsoon ascetic stay (Varshayoga / Chaturmas) for Jain sadhus",
                "meaning": "Formal completion and conclusion of the 4-month monsoon ascetic stay (Varshayoga / Chaturmas) for Jain sadhus",
                "observance": "Varsha Yog Nishthapan Vidhi, Chaturmas Parana",
                "sources": ["Jain Traditions"]
            })
            events.append({
                "id": f"gautam_gandhar_kevalgyan_{year}",
                "occurrence_id": f"gautam_gandhar_kevalgyan_{year}",
                "name": "Gautam Gandhar Kevalgyan Mahotsav",
                "title": "Gautam Gandhar Kevalgyan Mahotsav",
                "name_hindi": "गौतम गणधर केवलज्ञान महोत्सव",
                "category": "mahaparv",
                "badge": "Kevalgyan",
                "badge_color": "pink",
                "start_date": d_str,
                "end_date": d_str,
                "status": "confirmed",
                "description": "Attainment of supreme omniscience (Kevalgyana) by Pratham Gandhar Gautam Swami",
                "meaning": "Attainment of supreme omniscience (Kevalgyana) by Pratham Gandhar Gautam Swami",
                "observance": "Gautam Swami Pujan, Kevalgyan Aradhana",
                "sources": ["Jain Traditions"]
            })
        else:
            # Kshaya: fallback to Kartika Krishna Chaturdashi (14)
            chaturdashi_days = [
                s for s in kartika_snaps
                if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 14
            ]
            if chaturdashi_days:
                d_str = chaturdashi_days[-1]["date"].isoformat()
                events.append({
                    "id": f"mahavira_nirvana_kalyanak_{year}",
                    "occurrence_id": f"mahavira_nirvana_kalyanak_{year}",
                    "name": "Bhagwan Mahavira Nirvana Kalyanak (Diwali)",
                    "title": "Bhagwan Mahavira Nirvana Kalyanak (Diwali)",
                    "name_hindi": "भगवान महावीर निर्वाण कल्याणक (दीपावली)",
                    "category": "mahaparv",
                    "badge": "Moksha Kalyanak",
                    "badge_color": "pink",
                    "start_date": d_str,
                    "end_date": d_str,
                    "status": "confirmed",
                    "description": "Liberation (Moksha) of 24th Tirthankara Bhagwan Mahavira at Pavapuri; offering of the sacred Nirvana Laddu at dawn",
                    "meaning": "Liberation (Moksha) of 24th Tirthankara Bhagwan Mahavira at Pavapuri; offering of the sacred Nirvana Laddu at dawn",
                    "observance": "Nirvana Laddu Offering, Moksha Kalyan Pujan, Deepotsav",
                    "sources": ["Jain Traditions"]
                })
                events.append({
                    "id": f"varsha_yog_nishthapan_{year}",
                    "occurrence_id": f"varsha_yog_nishthapan_{year}",
                    "name": "Varsha Yog Nishthapan (Chaturmas Conclusion)",
                    "title": "Varsha Yog Nishthapan (Chaturmas Conclusion)",
                    "name_hindi": "वर्षा योग निष्ठापन (चातुर्मास समाप्ति)",
                    "category": "mahaparv",
                    "badge": "Nishthapan",
                    "badge_color": "pink",
                    "start_date": d_str,
                    "end_date": d_str,
                    "status": "confirmed",
                    "description": "Formal completion and conclusion of the 4-month monsoon ascetic stay (Varshayoga / Chaturmas) for Jain sadhus",
                    "meaning": "Formal completion and conclusion of the 4-month monsoon ascetic stay (Varshayoga / Chaturmas) for Jain sadhus",
                    "observance": "Varsha Yog Nishthapan Vidhi, Chaturmas Parana",
                    "sources": ["Jain Traditions"]
                })
                events.append({
                    "id": f"gautam_gandhar_kevalgyan_{year}",
                    "occurrence_id": f"gautam_gandhar_kevalgyan_{year}",
                    "name": "Gautam Gandhar Kevalgyan Mahotsav",
                    "title": "Gautam Gandhar Kevalgyan Mahotsav",
                    "name_hindi": "गौतम गणधर केवलज्ञान महोत्सव",
                    "category": "mahaparv",
                    "badge": "Kevalgyan",
                    "badge_color": "pink",
                    "start_date": d_str,
                    "end_date": d_str,
                    "status": "confirmed",
                    "description": "Attainment of supreme omniscience (Kevalgyana) by Pratham Gandhar Gautam Swami",
                    "meaning": "Attainment of supreme omniscience (Kevalgyana) by Pratham Gandhar Gautam Swami",
                    "observance": "Gautam Swami Pujan, Kevalgyan Aradhana",
                    "sources": ["Jain Traditions"]
                })

        return events


class KartikaShuklaEkamNewYearFestival(FestivalRule):
    """Kartika Shukla Pratipada (1): Navina Vira Nirvana Samvat Prarambh & Gautam Swami Kevalgyan Pujan Engine Logic.

    Target: Kartika Shukla Pratipada (1).
    Vriddhi: Assign strictly to 1st Pratipada.
    Kshaya : Fallback to Kartika Krishna Amavasya (30/15).
    Adhik  : Execute strictly during Adhik Kartika if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        kartika_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["KARTIKA", "KATAK", "KARTIK"]
        ]
        if not kartika_snaps:
            return []

        if any(s["is_adhika"] for s in kartika_snaps):
            kartika_snaps = [s for s in kartika_snaps if s["is_adhika"]]
        else:
            kartika_snaps = [s for s in kartika_snaps if not s["is_adhika"]]

        ekam_days = [
            s for s in kartika_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 1
        ]

        target_snap = None
        if ekam_days:
            target_snap = ekam_days[0]  # Vriddhi -> 1st Pratipada
        else:
            amavasya_days = [
                s for s in kartika_snaps
                if s["paksha"] == "Krishna" and s["tithi_in_paksha"] in [15, 30]
            ]
            if amavasya_days:
                target_snap = amavasya_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"jain_new_year_{year}",
                "occurrence_id": f"jain_new_year_{year}",
                "name": "Navina Vira Nirvana Samvat Prarambh (Jain New Year)",
                "title": "Navina Vira Nirvana Samvat Prarambh (Jain New Year)",
                "name_hindi": "नवीन वीर निर्वाण संवत् प्रारम्भ (जैन नववर्ष)",
                "category": "mahaparv",
                "badge": "New Year",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Commencement of the new Jain era (Vira Nirvana Samvat) and New Year (Nutan Varsh) celebrations",
                "meaning": "Commencement of the new Jain era (Vira Nirvana Samvat) and New Year (Nutan Varsh) celebrations",
                "observance": "Vira Nirvana Samvat Nutan Varsh, Chopda Pujan, Nutan Varsh Abhinandan",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"gautam_swami_kevalgyan_pujan_{year}",
                "occurrence_id": f"gautam_swami_kevalgyan_pujan_{year}",
                "name": "Gautam Swami Kevalgyan Pujan",
                "title": "Gautam Swami Kevalgyan Pujan",
                "name_hindi": "गौतम स्वामी केवलज्ञान पूजन",
                "category": "mahaparv",
                "badge": "Kevalgyan",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Morning celebration and aradhana of supreme omniscience (Kevalgyana) attained by Gautam Gandhar",
                "meaning": "Morning celebration and aradhana of supreme omniscience (Kevalgyana) attained by Gautam Gandhar",
                "observance": "Gautam Swami Pujan, Kevalgyan Aradhana",
                "sources": ["Jain Traditions"]
            }
        ]


class BhaiDoojFestival(FestivalRule):
    """Kartika Shukla Dvitiya (2): Bhai Dooj (Bhaiya Dooj / Yama Dvitiya / Bhratri Dvitiya) Engine Logic.

    Target: Kartika Shukla Dvitiya (2).
    Vriddhi: Assign strictly to 1st Dvitiya.
    Kshaya : Fallback to Kartika Shukla Pratipada (1).
    Adhik  : Execute strictly during Adhik Kartika if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        kartika_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["KARTIKA", "KATAK", "KARTIK"]
        ]
        if not kartika_snaps:
            return []

        if any(s["is_adhika"] for s in kartika_snaps):
            kartika_snaps = [s for s in kartika_snaps if s["is_adhika"]]
        else:
            kartika_snaps = [s for s in kartika_snaps if not s["is_adhika"]]

        dvitiya_days = [
            s for s in kartika_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 2
        ]

        target_snap = None
        if dvitiya_days:
            target_snap = dvitiya_days[0]  # Vriddhi -> 1st Dvitiya
        else:
            ekam_days = [
                s for s in kartika_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 1
            ]
            if ekam_days:
                target_snap = ekam_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"bhai_dooj_{year}",
                "occurrence_id": f"bhai_dooj_{year}",
                "name": "Bhaiya Dooj (Bhratri Dvitiya)",
                "title": "Bhaiya Dooj (Bhratri Dvitiya)",
                "name_hindi": "भैया दूज (भ्रातृ द्वितीया)",
                "category": "mahaparv",
                "badge": "Bhai Dooj",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Kartika Shukla Dvitiya celebration of brother-sister bond (commemorating King Nandivardhana & Sister Sudarshana post-Mahavira Nirvana)",
                "meaning": "Kartika Shukla Dvitiya celebration of brother-sister bond (commemorating King Nandivardhana & Sister Sudarshana post-Mahavira Nirvana)",
                "observance": "Tilak & Raksha Vidhi, Bhratri Pujan, Family Fellowship",
                "sources": ["Jain Traditions"]
            }
        ]


class KartikaShuklaPanchamiFestival(FestivalRule):
    """Kartika Shukla Panchami (5): Labh Panchami / Gyan Panchami / Saubhagya Panchami Engine Logic.

    Target: Kartika Shukla Panchami (5).
    Vriddhi: Assign strictly to 1st Panchami.
    Kshaya : Fallback to Kartika Shukla Chaturthi (4).
    Adhik  : Execute strictly during Adhik Kartika if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        kartika_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["KARTIKA", "KATAK", "KARTIK"]
        ]
        if not kartika_snaps:
            return []

        if any(s["is_adhika"] for s in kartika_snaps):
            kartika_snaps = [s for s in kartika_snaps if s["is_adhika"]]
        else:
            kartika_snaps = [s for s in kartika_snaps if not s["is_adhika"]]

        panchami_days = [
            s for s in kartika_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 5
        ]

        target_snap = None
        if panchami_days:
            target_snap = panchami_days[0]  # Vriddhi -> 1st Panchami
        else:
            chaturthi_days = [
                s for s in kartika_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 4
            ]
            if chaturthi_days:
                target_snap = chaturthi_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"gyan_panchami_{year}",
                "occurrence_id": f"gyan_panchami_{year}",
                "name": "Gyan Panchami (Jnana Panchami)",
                "title": "Gyan Panchami (Jnana Panchami)",
                "name_hindi": "ज्ञान पंचमी (ज्ञान पंचम)",
                "category": "mahaparv_vrat",
                "badge": "Gyan Panchami",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Kartika Shukla Panchami aradhana dedicated to sacred scriptures (Agamas/Shrut Jnana), Shastra Pujan, and destruction of Jnanavaraniya Karma",
                "meaning": "Kartika Shukla Panchami aradhana dedicated to sacred scriptures (Agamas/Shrut Jnana), Shastra Pujan, and destruction of Jnanavaraniya Karma",
                "observance": "Shrut Jnana Aradhana, Shastra Pujan, Fasting & Swadhyay",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"labh_panchami_{year}",
                "occurrence_id": f"labh_panchami_{year}",
                "name": "Labh Panchami (Saubhagya Panchami)",
                "title": "Labh Panchami (Saubhagya Panchami)",
                "name_hindi": "लाभ पंचमी (सौभाग्य पंचमी)",
                "category": "mahaparv",
                "badge": "Labh Panchami",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Auspicious day for reopening of business establishments and ledgers post-Diwali for good fortune and prosperity",
                "meaning": "Auspicious day for reopening of business establishments and ledgers post-Diwali for good fortune and prosperity",
                "observance": "Business Reopening, Shubh-Labh Pujan, Ledger Commencement",
                "sources": ["Jain Traditions"]
            }
        ]


class KartikaNandishwarAshtamiFestival(FestivalRule):
    """Kartika Shukla Ashtami (8): Nandishwar Ashtami (Kartika Ashtahnika Parv Prarambh) Engine Logic.

    Target: Kartika Shukla Ashtami (8) start boundary event, spanning to Kartika Shukla Purnima (15).
    Vriddhi: Assign strictly to 1st Ashtami.
    Kshaya : Fallback to Kartika Shukla Saptami (7).
    Adhik  : Execute strictly during Adhik Kartika if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        kartika_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["KARTIKA", "KATAK", "KARTIK"]
        ]
        if not kartika_snaps:
            return []

        if any(s["is_adhika"] for s in kartika_snaps):
            kartika_snaps = [s for s in kartika_snaps if s["is_adhika"]]
        else:
            kartika_snaps = [s for s in kartika_snaps if not s["is_adhika"]]

        ashtami_days = [
            s for s in kartika_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 8
        ]

        target_snap = None
        if ashtami_days:
            target_snap = ashtami_days[0]  # Vriddhi -> 1st Ashtami
        else:
            saptami_days = [
                s for s in kartika_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 7
            ]
            if saptami_days:
                target_snap = saptami_days[-1]

        if not target_snap:
            return []

        purnima_days = [
            s for s in kartika_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 15
        ]
        end_snap = purnima_days[-1] if purnima_days else kartika_snaps[-1]

        start_date_str = target_snap["date"].isoformat()
        start_mm_dd = target_snap["date"].strftime("%b %d")
        end_mm_dd = end_snap["date"].strftime("%b %d")

        return [
            {
                "id": f"nandishwar_ashtami_kartika_{year}",
                "occurrence_id": f"nandishwar_ashtami_kartika_{year}",
                "name": "Nandishwar Ashtami (Ashtahnika Parv Prarambh)",
                "title": "Nandishwar Ashtami (Ashtahnika Parv Prarambh)",
                "name_hindi": "नंदीश्वर अष्टमी (कार्तिक अष्टाह्निका पर्व प्रारम्भ)",
                "category": "mahaparv_vrat",
                "badge": "Vrat Start",
                "badge_color": "pink",
                "is_span": True,
                "span_label": f"Span: {start_mm_dd} – {end_mm_dd}",
                "boundary_type": "START",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "description": "Commencement of the 8-day Kartika Ashtahnika Mahaparv: Aradhana of the 52 eternal Jinalayas of Nandishwara Dweepa",
                "meaning": "Commencement of the 8-day Kartika Ashtahnika Mahaparv: Aradhana of the 52 eternal Jinalayas of Nandishwara Dweepa",
                "observance": "Nandishwar Vidhana, Siddhachakra Aradhana, Shrut & Jina Pujan",
                "sources": ["Jain Traditions"]
            }
        ]


class PanditJainiJiyalalPunyatithiFestival(FestivalRule):
    """Kartika Shukla Ekadashi (11): Pandit Jaini Jiyalal Ji Chaudhary Punya Divas Engine Logic.

    Target: Kartika Shukla Ekadashi (11).
    Vriddhi: Assign strictly to 1st Ekadashi.
    Kshaya : Fallback to Kartika Shukla Dashami (10).
    Adhik  : Execute strictly during Adhik Kartika if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        kartika_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["KARTIKA", "KATAK", "KARTIK"]
        ]
        if not kartika_snaps:
            return []

        if any(s["is_adhika"] for s in kartika_snaps):
            kartika_snaps = [s for s in kartika_snaps if s["is_adhika"]]
        else:
            kartika_snaps = [s for s in kartika_snaps if not s["is_adhika"]]

        ekadashi_days = [
            s for s in kartika_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 11
        ]

        target_snap = None
        if ekadashi_days:
            target_snap = ekadashi_days[0]  # Vriddhi -> 1st Ekadashi
        else:
            dashami_days = [
                s for s in kartika_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 10
            ]
            if dashami_days:
                target_snap = dashami_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"pandit_jaini_jiyalal_punyatithi_{year}",
                "occurrence_id": f"pandit_jaini_jiyalal_punyatithi_{year}",
                "name": "Pandit Jaini Jiyalal Ji Chaudhary Punya Divas",
                "title": "Pandit Jaini Jiyalal Ji Chaudhary Punya Divas",
                "name_hindi": "पंडित जैनी जियालाल जी चौधरी पुण्य दिवस",
                "category": "punya_tithi",
                "badge": "Punya Tithi",
                "badge_color": "Goldern",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Memorial anniversary commemorating renowned Digambara Jain scholar and educationist Pandit Jaini Jiyalal Ji Chaudhary on Kartika Shukla Ekadashi",
                "meaning": "Memorial anniversary commemorating renowned Digambara Jain scholar and educationist Pandit Jaini Jiyalal Ji Chaudhary on Kartika Shukla Ekadashi",
                "observance": "Gurukul & Vidvat Parishad Memorial Assembly, Swadhyay, Shastra Vandana",
                "sources": ["Jain Traditions"]
            }
        ]


class KartikaPurnimaAshtahnikaPurnaFestival(FestivalRule):
    """Kartika Shukla Purnima (15): Kartika Purnima, Ashtahnika Purna & Dev Deepavali Engine Logic.

    Target: Kartika Shukla Purnima (15).
    Vriddhi: Assign strictly to 2nd Purnima.
    Kshaya : Fallback to Kartika Shukla Chaturdashi (14).
    Adhik  : Execute strictly during Adhik Kartika if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        kartika_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["KARTIKA", "KATAK", "KARTIK"]
        ]
        if not kartika_snaps:
            return []

        if any(s["is_adhika"] for s in kartika_snaps):
            kartika_snaps = [s for s in kartika_snaps if s["is_adhika"]]
        else:
            kartika_snaps = [s for s in kartika_snaps if not s["is_adhika"]]

        purnima_days = [
            s for s in kartika_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 15
        ]

        target_snap = None
        if purnima_days:
            target_snap = purnima_days[-1]  # Vriddhi -> 2nd Purnima
        else:
            chaturdashi_days = [
                s for s in kartika_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 14
            ]
            if chaturdashi_days:
                target_snap = chaturdashi_days[-1]

        if not target_snap:
            return []

        ashtami_days = [
            s for s in kartika_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 8
        ]
        start_snap = ashtami_days[0] if ashtami_days else target_snap

        start_date_str = target_snap["date"].isoformat()
        start_mm_dd = start_snap["date"].strftime("%b %d")
        end_mm_dd = target_snap["date"].strftime("%b %d")

        return [
            {
                "id": f"kartika_ashtahnika_purna_{year}",
                "occurrence_id": f"kartika_ashtahnika_purna_{year}",
                "name": "Kartika Ashtahnika Mahaparv Purna",
                "title": "Kartika Ashtahnika Mahaparv Purna",
                "name_hindi": "कार्तिक अष्टाह्निका महापर्व पूर्ण",
                "category": "mahaparv_vrat",
                "badge": "Vrat End",
                "badge_color": "pink",
                "is_span": True,
                "span_label": f"Span: {start_mm_dd} – {end_mm_dd}",
                "boundary_type": "END",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "description": "Conclusion and Nishthapan of the 8-day Kartika Ashtahnika Parv (Nandishwara Dweepa 52 Jinalaya Aradhana)",
                "meaning": "Conclusion and Nishthapan of the 8-day Kartika Ashtahnika Parv (Nandishwara Dweepa 52 Jinalaya Aradhana)",
                "observance": "Ashtahnika Parv Nishthapan, Nandishwar Grand Pujan, Siddha Bhakti",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"kartika_purnima_dev_deepavali_{year}",
                "occurrence_id": f"kartika_purnima_dev_deepavali_{year}",
                "name": "Kartika Purnima (Dev Deepavali)",
                "title": "Kartika Purnima (Dev Deepavali)",
                "name_hindi": "कार्तिक पूर्णिमा (देव दीपावली)",
                "category": "mahaparv",
                "badge": "Kartika Purnima",
                "badge_color": "pink",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "description": "Culmination of holy Kartika month, Jinalaya Deepotsav, and auspicious Teerth pilgrimage aradhana",
                "meaning": "Culmination of holy Kartika month, Jinalaya Deepotsav, and auspicious Teerth pilgrimage aradhana",
                "observance": "Jinalaya Deepotsav, Shatrunjaya Teerth Yatra, Jin Pujan",
                "sources": ["Jain Traditions"]
            }
        ]


class MargashirshaSheetalnathStotramFestival(FestivalRule):
    """Margashirsha Shukla Navami (9): Bhagwan Sheetalnath Stotram Rachna Divas Engine Logic.

    Target: Margashirsha Shukla Navami (9).
    Vriddhi: Assign strictly to 1st Navami.
    Kshaya : Fallback to Margashirsha Shukla Ashtami (8).
    Adhik  : Execute strictly during Adhik Margashirsha if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        marga_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["MARGASHIRSHA", "MAGSAR", "AGRAHAYANA", "MANSIR", "MARGASHIRSA"]
        ]
        if not marga_snaps:
            return []

        if any(s["is_adhika"] for s in marga_snaps):
            marga_snaps = [s for s in marga_snaps if s["is_adhika"]]
        else:
            marga_snaps = [s for s in marga_snaps if not s["is_adhika"]]

        navami_days = [
            s for s in marga_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 9
        ]

        target_snap = None
        if navami_days:
            target_snap = navami_days[0]  # Vriddhi -> 1st Navami
        else:
            ashtami_days = [
                s for s in marga_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 8
            ]
            if ashtami_days:
                target_snap = ashtami_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"sheetalnath_stotram_rachna_{year}",
                "occurrence_id": f"sheetalnath_stotram_rachna_{year}",
                "name": "Bhagwan Sheetalnath Stotram Rachna Divas",
                "title": "Bhagwan Sheetalnath Stotram Rachna Divas",
                "name_hindi": "भगवान शीतलनाथ स्तोत्रम रचना दिवस",
                "category": "mahaparv",
                "badge": "Stotram Rachna",
                "badge_color": "pink",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Margashirsha Shukla Navami aradhana commemorating the sacred composition of stotras and devotional hymns dedicated to 10th Tirthankara Bhagwan Sheetalnath",
                "meaning": "Margashirsha Shukla Navami aradhana commemorating the sacred composition of stotras and devotional hymns dedicated to 10th Tirthankara Bhagwan Sheetalnath",
                "observance": "Stotra Path, Bhakti-Vandana, Jinavani Swadhyay, Sheetalnath Jin Pujan",
                "sources": ["Jain Traditions"]
            }
        ]


class MaghaLabdhiVidhanFestival(FestivalRule):
    """Magha Krishna Amavasya to Magha Shukla Chaturthi: Labdhi Vidhan Vrat."""
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        jain_snaps = [s for s in snapshots if s["date"].year == year and get_jain_month(s) == "MAGHA"]
        if not jain_snaps: return []
        if any(s["is_adhika"] for s in jain_snaps):
            jain_snaps = [s for s in jain_snaps if s["is_adhika"]]
        else:
            jain_snaps = [s for s in jain_snaps if not s["is_adhika"]]
            
        amavasya_days = [s for s in jain_snaps if s["paksha"] == "Krishna" and s["tithi_in_paksha"] in [15, 30]]
        start_snap = amavasya_days[0] if amavasya_days else None
        if not start_snap:
            k14 = [s for s in jain_snaps if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 14]
            if k14: start_snap = k14[-1]
            
        chaturthi_days = [s for s in jain_snaps if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 4]
        end_snap = chaturthi_days[-1] if chaturthi_days else None
        if not end_snap:
            s3 = [s for s in jain_snaps if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 3]
            if s3: end_snap = s3[-1]
            
        if not start_snap or not end_snap: return []
        
        start_date_str = start_snap["date"].isoformat()
        end_date_str = end_snap["date"].isoformat()
        start_mm_dd = start_snap["date"].strftime("%b %d")
        end_mm_dd = end_snap["date"].strftime("%b %d")
        
        return [
            {
                "id": f"labdhi_vidhan_start_magha_{year}",
                "occurrence_id": f"labdhi_vidhan_start_magha_{year}",
                "name": "Labdhi Vidhan Vrat Prarambh",
                "title": "Labdhi Vidhan Vrat Prarambh",
                "name_hindi": "लब्धि विधान व्रत प्रारम्भ",
                "category": "mahaparv_vrat",
                "badge": "Vrat Start",
                "badge_color": "orange",
                "is_span": True,
                "span_label": f"Span: {start_mm_dd} - {end_mm_dd}",
                "boundary_type": "START",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "description": self.meaning or "Commencement of Labdhi Vidhan Vrat",
                "meaning": self.meaning or "Commencement of Labdhi Vidhan Vrat",
                "observance": self.observance or "Labdhi Vrat Start",
                "sources": self.sources
            },
            {
                "id": f"labdhi_vidhan_purna_magha_{year}",
                "occurrence_id": f"labdhi_vidhan_purna_magha_{year}",
                "name": "Labdhi Vidhan Vrat Purna",
                "title": "Labdhi Vidhan Vrat Purna",
                "name_hindi": "लब्धि विधान व्रत पूर्ण",
                "category": "mahaparv_vrat",
                "badge": "Vrat End",
                "badge_color": "orange",
                "is_span": True,
                "span_label": f"Span: {start_mm_dd} - {end_mm_dd}",
                "boundary_type": "END",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "description": self.meaning or "Conclusion of Labdhi Vidhan Vrat",
                "meaning": self.meaning or "Conclusion of Labdhi Vidhan Vrat",
                "observance": self.observance or "Labdhi Vrat End",
                "sources": self.sources
            }
        ]

class PanditJainiJiyalalJanmaDivasFestival(FestivalRule):
    """Magha Shukla Dvitiya (2): Pandit Jaini Jiyalal Ji Chaudhary Janma Divas Engine Logic.

    Target: Magha Shukla Dvitiya (2).
    Vriddhi: Assign strictly to 1st Dvitiya.
    Kshaya : Fallback to Magha Shukla Pratipada (1).
    Adhik  : Execute strictly during Adhik Magha if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        magha_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["MAGHA", "MAH", "MHA", "MAGH"]
        ]
        if not magha_snaps:
            return []

        if any(s["is_adhika"] for s in magha_snaps):
            magha_snaps = [s for s in magha_snaps if s["is_adhika"]]
        else:
            magha_snaps = [s for s in magha_snaps if not s["is_adhika"]]

        dvitiya_days = [
            s for s in magha_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 2
        ]

        target_snap = None
        if dvitiya_days:
            target_snap = dvitiya_days[0]  # Vriddhi -> 1st Dvitiya
        else:
            pratipada_days = [
                s for s in magha_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 1
            ]
            if pratipada_days:
                target_snap = pratipada_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"pandit_jaini_jiyalal_janma_divas_{year}",
                "occurrence_id": f"pandit_jaini_jiyalal_janma_divas_{year}",
                "name": "Pandit Jaini Jiyalal Ji Chaudhary Janma Divas",
                "title": "Pandit Jaini Jiyalal Ji Chaudhary Janma Divas",
                "name_hindi": "पंडित जैनी जियालाल जी चौधरी जन्म दिवस",
                "category": "jayanti",
                "badge": "Janma Jayanti",
                "badge_color": "purple",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Birth anniversary celebration commemorating renowned Digambara Jain scholar and educationist Pandit Jaini Jiyalal Ji Chaudhary on Magha Shukla Dvitiya",
                "meaning": "Birth anniversary celebration commemorating renowned Digambara Jain scholar and educationist Pandit Jaini Jiyalal Ji Chaudhary on Magha Shukla Dvitiya",
                "observance": "Vidyalaya & Gurukul Assemblies, Swadhyay, Shastra Publishing Seminars",
                "sources": ["Digambara Jain Traditions"]
            }
        ]


class MaghaShuklaPanchamiTriFestival(FestivalRule):
    """Magha Shukla Panchami (5): Acharya Kundakunda Jayanti, Murti Sthapna Divas & Vasant Panchami Engine Logic.

    Target: Magha Shukla Panchami (5).
    Vriddhi: Assign strictly to 1st Panchami.
    Kshaya : Fallback to Magha Shukla Chaturthi (4).
    Adhik  : Execute strictly during Adhik Magha if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        magha_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["MAGHA", "MAH", "MHA", "MAGH"]
        ]
        if not magha_snaps:
            return []

        if any(s["is_adhika"] for s in magha_snaps):
            magha_snaps = [s for s in magha_snaps if s["is_adhika"]]
        else:
            magha_snaps = [s for s in magha_snaps if not s["is_adhika"]]

        panchami_days = [
            s for s in magha_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 5
        ]

        target_snap = None
        if panchami_days:
            target_snap = panchami_days[0]  # Vriddhi -> 1st Panchami
        else:
            chaturthi_days = [
                s for s in magha_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 4
            ]
            if chaturthi_days:
                target_snap = chaturthi_days[-1]

        if not target_snap:
            return []

        date_str = target_snap["date"].isoformat()

        return [
            {
                "id": f"acharya_kundakunda_jayanti_{year}",
                "occurrence_id": f"acharya_kundakunda_jayanti_{year}",
                "name": "Acharya Kundakunda Swami Janma Jayanti",
                "title": "Acharya Kundakunda Swami Janma Jayanti",
                "name_hindi": "आचार्य कुंदकुंद स्वामी जन्म जयंती",
                "category": "jayanti",
                "badge": "Janma Jayanti",
                "badge_color": "purple",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Birth anniversary of Prathamaacharyavarya 108 Acharya Shri Kundakunda Dev, author of foundational Agamic granthas including Samayasara and Pravachanasara",
                "meaning": "Birth anniversary of Prathamaacharyavarya 108 Acharya Shri Kundakunda Dev, author of foundational Agamic granthas including Samayasara and Pravachanasara",
                "observance": "Kundakunda Dev Pujan, Samayasara Swadhyay, Agam Pujan",
                "sources": ["Digambara Jain Traditions"]
            },
            {
                "id": f"jina_murti_sthapna_{year}",
                "occurrence_id": f"jina_murti_sthapna_{year}",
                "name": "Jina Murti Sthapna Divas",
                "title": "Jina Murti Sthapna Divas",
                "name_hindi": "जिन मूर्ति स्थापना दिवस",
                "category": "auspicious",
                "badge": "Murti Sthapna",
                "badge_color": "emerald",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Auspicious day for Jina idol consecration (Pratishtha), Jinalaya Patotsav, and Shubh Murti Sthapna rituals on Vasant Panchami",
                "meaning": "Auspicious day for Jina idol consecration (Pratishtha), Jinalaya Patotsav, and Shubh Murti Sthapna rituals on Vasant Panchami",
                "observance": "Jina Pratishtha, Patotsav Abhisheka, Temple Consecration",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"vasant_panchami_shrut_{year}",
                "occurrence_id": f"vasant_panchami_shrut_{year}",
                "name": "Vasant Panchami (Shrut Vasant)",
                "title": "Vasant Panchami (Shrut Vasant)",
                "name_hindi": "वसन्त पंचमी (श्रुत वसन्त)",
                "category": "shastra",
                "badge": "Jinavani Pujan",
                "badge_color": "indigo",
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": "Magha Shukla Panchami aradhana dedicated to sacred scriptures, Jinavani Pujan, and veneration of Shrut Devi",
                "meaning": "Magha Shukla Panchami aradhana dedicated to sacred scriptures, Jinavani Pujan, and veneration of Shrut Devi",
                "observance": "Jinavani Pujan, Shrut Aradhana, Shastra Vandana",
                "sources": ["Jain Traditions"]
            }
        ]


class PhalgunaPurnimaAshtahnikaPurnaFestival(FestivalRule):
    """Phalguna Shukla Purnima (15): Phalguna Ashtahnika Purna, Holika Dahan & Vasantotsav Engine Logic.

    Target: Phalguna Shukla Purnima (15).
    Vriddhi: Assign strictly to 2nd Purnima.
    Kshaya : Fallback to Phalguna Shukla Chaturdashi (14).
    Adhik  : Execute strictly during Adhik Phalguna if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        phalguna_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["PHALGUNA", "FALGUN", "PHAGAN", "PHALGUN"]
        ]
        if not phalguna_snaps:
            return []

        if any(s["is_adhika"] for s in phalguna_snaps):
            phalguna_snaps = [s for s in phalguna_snaps if s["is_adhika"]]
        else:
            phalguna_snaps = [s for s in phalguna_snaps if not s["is_adhika"]]

        purnima_days = [
            s for s in phalguna_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 15
        ]

        target_snap = None
        if purnima_days:
            target_snap = purnima_days[-1]  # Vriddhi -> 2nd Purnima
        else:
            chaturdashi_days = [
                s for s in phalguna_snaps
                if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 14
            ]
            if chaturdashi_days:
                target_snap = chaturdashi_days[-1]

        if not target_snap:
            return []

        ashtami_days = [
            s for s in phalguna_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 8
        ]
        start_snap = ashtami_days[0] if ashtami_days else target_snap

        start_date_str = target_snap["date"].isoformat()
        start_mm_dd = start_snap["date"].strftime("%b %d")
        end_mm_dd = target_snap["date"].strftime("%b %d")

        return [
            {
                "id": f"phalguna_ashtahnika_purna_{year}",
                "occurrence_id": f"phalguna_ashtahnika_purna_{year}",
                "name": "Phalguna Ashtahnika Mahaparv Purna",
                "title": "Phalguna Ashtahnika Mahaparv Purna",
                "name_hindi": "फाल्गुन अष्टाह्निका महापर्व पूर्ण",
                "category": "mahaparv_vrat",
                "badge": "Vrat End",
                "badge_color": "orange",
                "is_span": True,
                "span_label": f"Span: {start_mm_dd} – {end_mm_dd}",
                "boundary_type": "END",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "description": "Formal conclusion and Nishthapan of the 8-day Phalguna Ashtahnika Parv (Nandishwara Dweepa 52 Jinalaya Aradhana)",
                "meaning": "Formal conclusion and Nishthapan of the 8-day Phalguna Ashtahnika Parv (Nandishwara Dweepa 52 Jinalaya Aradhana)",
                "observance": "Ashtahnika Parv Nishthapan, Nandishwar Grand Pujan, Siddha Bhakti",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"holika_dahan_{year}",
                "occurrence_id": f"holika_dahan_{year}",
                "name": "Holika Dahan (Holi Parv)",
                "title": "Holika Dahan (Holi Parv)",
                "name_hindi": "होलिका दहन (होली पर्व)",
                "category": "utsav",
                "badge": "Holika Dahan",
                "badge_color": "emerald",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "description": "Phalguna Shukla Purnima evening festival symbolizing the victory of devotion and righteousness; bonfire pujan in Pradosha Kaal",
                "meaning": "Phalguna Shukla Purnima evening festival symbolizing the victory of devotion and righteousness; bonfire pujan in Pradosha Kaal",
                "observance": "Bonfire Pujan in Pradosha Kaal, Bhakti Pujan, Utsav Rituals",
                "sources": ["Jain Traditions"]
            },
            {
                "id": f"phalguna_purnima_vasantotsav_{year}",
                "occurrence_id": f"phalguna_purnima_vasantotsav_{year}",
                "name": "Phalguna Purnima (Vasantotsav)",
                "title": "Phalguna Purnima (Vasantotsav)",
                "name_hindi": "फाल्गुन पूर्णिमा (वसन्तौत्सव)",
                "category": "mahaparv",
                "badge": "Sharadotsav",
                "badge_color": "red",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "description": "Culmination of Phalguna month with Jina Abhishek, spring festival aradhana, and full-moon pujan",
                "meaning": "Culmination of Phalguna month with Jina Abhishek, spring festival aradhana, and full-moon pujan",
                "observance": "Jina Abhishek, Full-Moon Pujan, Vasantotsav Aradhana",
                "sources": ["Jain Traditions"]
            }
        ]


class ChaitraAmavasyaKalyanakVarshantFestival(FestivalRule):
    """Chaitra Krishna Amavasya (30): Tirthankara Moksha, Labdhi Vidhan Prarambh & Vikram Samvat Varsha-Ant Engine Logic.

    Start/Kalyanak/Labdhi: 1st Amavasya if Vriddhi, or single Amavasya, or fallback to Krishna 14 if Kshaya.
    Varsha-Ant: 2nd Amavasya if Vriddhi, or single Amavasya, or fallback to Krishna 14 if Kshaya.
    Adhik: Execute strictly during Adhik Chaitra if month repeats, skip Nija.
    """
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]

        chaitra_snaps = [
            s for s in snapshots
            if s["date"].year == year
            and s["hindu_month"].upper() in ["CHAITRA", "CHAIT", "CHET"]
        ]
        if not chaitra_snaps:
            return []

        if any(s["is_adhika"] for s in chaitra_snaps):
            chaitra_snaps = [s for s in chaitra_snaps if s["is_adhika"]]
        else:
            chaitra_snaps = [s for s in chaitra_snaps if not s["is_adhika"]]

        amavasya_days = [
            s for s in chaitra_snaps
            if s["paksha"] == "Krishna" and (s["tithi_in_paksha"] == 15 or s["tithi"] == 30)
        ]

        if amavasya_days:
            first_amavasya = amavasya_days[0]
            last_amavasya = amavasya_days[-1]
        else:
            krishna_14 = [
                s for s in chaitra_snaps
                if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 14
            ]
            if not krishna_14:
                return []
            first_amavasya = krishna_14[-1]
            last_amavasya = krishna_14[-1]

        # Calculate Labdhi Vidhan end date (Chaitra Shukla Chaturthi) for span label
        shukla_4_days = [
            s for s in chaitra_snaps
            if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 4
        ]
        end_snap = shukla_4_days[-1] if shukla_4_days else first_amavasya

        start_date_str = first_amavasya["date"].isoformat()
        end_date_str = last_amavasya["date"].isoformat()

        start_mm_dd = first_amavasya["date"].strftime("%b %d")
        end_mm_dd = end_snap["date"].strftime("%b %d")
        span_label = f"Span: {start_mm_dd} – {end_mm_dd}"

        occurrences = []

        # 1. First Amavasya events
        occurrences.append({
            "id": f"ananthnath_moksha_{year}",
            "occurrence_id": f"ananthnath_moksha_{year}",
            "name": "Bhagwan Ananthnath Ji Moksha Kalyanak",
            "title": "Bhagwan Ananthnath Ji Moksha Kalyanak",
            "name_hindi": "भगवान अनंतनाथ जी मोक्ष कल्याणक",
            "category": "kalyanak",
            "badge": "Moksha Kalyanak",
            "badge_color": "red",
            "start_date": start_date_str,
            "end_date": start_date_str,
            "status": "confirmed",
            "description": "Nirvana / Moksha Kalyanak aradhana of the 14th Tirthankara Bhagwan Ananthnath from Sammed Shikharji",
            "meaning": "Nirvana / Moksha Kalyanak aradhana of the 14th Tirthankara Bhagwan Ananthnath from Sammed Shikharji",
            "observance": "Moksha Kalyanak Ladoo Offering, Shikharji Vandana, Jin Pujan",
            "sources": ["Jain Traditions"]
        })

        occurrences.append({
            "id": f"aranath_moksha_{year}",
            "occurrence_id": f"aranath_moksha_{year}",
            "name": "Bhagwan Aranath Ji Moksha Kalyanak",
            "title": "Bhagwan Aranath Ji Moksha Kalyanak",
            "name_hindi": "भगवान अरनाथ जी मोक्ष कल्याणक",
            "category": "kalyanak",
            "badge": "Moksha Kalyanak",
            "badge_color": "red",
            "start_date": start_date_str,
            "end_date": start_date_str,
            "status": "confirmed",
            "description": "Nirvana / Moksha Kalyanak aradhana of the 18th Tirthankara Bhagwan Aranath from Sammed Shikharji",
            "meaning": "Nirvana / Moksha Kalyanak aradhana of the 18th Tirthankara Bhagwan Aranath from Sammed Shikharji",
            "observance": "Nirvana Ladoo Offering, Shikharji Aradhana, Jin Pujan",
            "sources": ["Jain Traditions"]
        })



        # 2. Concluding/Second Amavasya event: Vikram Samvat Varsha-Ant Divas
        occurrences.append({
            "id": f"vikram_samvat_varshant_{year}",
            "occurrence_id": f"vikram_samvat_varshant_{year}",
            "name": "Vikram Samvat Varsha-Ant Divas",
            "title": "Vikram Samvat Varsha-Ant Divas",
            "name_hindi": "विक्रम संवत वर्षांत दिवस",
            "category": "auspicious",
            "badge": "Year End",
            "badge_color": "emerald",
            "start_date": end_date_str,
            "end_date": end_date_str,
            "status": "confirmed",
            "description": "Concluding day of the outgoing Vikram Samvat lunar year, preceding the dawn of the New Year (Nav Samvatsar)",
            "meaning": "Concluding day of the outgoing Vikram Samvat lunar year, preceding the dawn of the New Year (Nav Samvatsar)",
            "observance": "Varsha-Ant Pratikramana, Year-End Reflection, Shanti Paath",
            "sources": ["Jain/Vedic Traditions"]
        })

        return occurrences


class Namokar35VratFestival(FestivalRule):
    """Namokar Mahamantra 35-Vrat State Machine Engine Logic.

    1.5-Year (18 Lunar Months) 35-Vrat state machine mapping 35 syllables of Namokar Mantra.
    - Steps 1-7: Pada 'Ṇamō Arihantāṇaṁ' (7 Saptami Vrats: Ashadha Shukla 7 to Ashwin Shukla 7)
    - Steps 8-12: Pada 'Ṇamō Siddhāṇaṁ' (5 Panchami Vrats: Kartika Krishna 5 to Pausha Krishna 5)
    - Steps 13-19: Pada 'Ṇamō Āyariyāṇaṁ' (7 Chaturdashi Vrats: Pausha Krishna 14 to Chaitra Krishna 14)
    - Steps 20-26: Pada 'Ṇamō Uvajjhāyāṇaṁ' (7 Chaturdashi Vrats: Chaitra Shukla 14 to Ashadha Shukla 14)
    - Steps 27-35: Pada 'Ṇamō Lōē Savvasāhūṇaṁ' (9 Navami Vrats: Shravana Krishna 9 to Margashirsha Krishna 9)
    """

    STEPS_DEFINITION = [
        # (step_num, month, paksha, tithi, pada, sub_idx, sub_total, fallback_tithi)
        (1, "ASHADHA", "Shukla", 7, "Ṇamō Arihantāṇaṁ", 1, 7, 6),
        (2, "SHRAVANA", "Krishna", 7, "Ṇamō Arihantāṇaṁ", 2, 7, 6),
        (3, "SHRAVANA", "Shukla", 7, "Ṇamō Arihantāṇaṁ", 3, 7, 6),
        (4, "BHADRAPADA", "Krishna", 7, "Ṇamō Arihantāṇaṁ", 4, 7, 6),
        (5, "BHADRAPADA", "Shukla", 7, "Ṇamō Arihantāṇaṁ", 5, 7, 6),
        (6, "ASHWIN", "Krishna", 7, "Ṇamō Arihantāṇaṁ", 6, 7, 6),
        (7, "ASHWIN", "Shukla", 7, "Ṇamō Arihantāṇaṁ", 7, 7, 6),

        (8, "KARTIKA", "Krishna", 5, "Ṇamō Siddhāṇaṁ", 1, 5, 4),
        (9, "KARTIKA", "Shukla", 5, "Ṇamō Siddhāṇaṁ", 2, 5, 4),
        (10, "MARGASHIRSHA", "Krishna", 5, "Ṇamō Siddhāṇaṁ", 3, 5, 4),
        (11, "MARGASHIRSHA", "Shukla", 5, "Ṇamō Siddhāṇaṁ", 4, 5, 4),
        (12, "PAUSHA", "Krishna", 5, "Ṇamō Siddhāṇaṁ", 5, 5, 4),

        (13, "PAUSHA", "Krishna", 14, "Ṇamō Āyariyāṇaṁ", 1, 7, 13),
        (14, "PAUSHA", "Shukla", 14, "Ṇamō Āyariyāṇaṁ", 2, 7, 13),
        (15, "MAGHA", "Krishna", 14, "Ṇamō Āyariyāṇaṁ", 3, 7, 13),
        (16, "MAGHA", "Shukla", 14, "Ṇamō Āyariyāṇaṁ", 4, 7, 13),
        (17, "PHALGUNA", "Krishna", 14, "Ṇamō Āyariyāṇaṁ", 5, 7, 13),
        (18, "PHALGUNA", "Shukla", 14, "Ṇamō Āyariyāṇaṁ", 6, 7, 13),
        (19, "CHAITRA", "Krishna", 14, "Ṇamō Āyariyāṇaṁ", 7, 7, 13),

        (20, "CHAITRA", "Shukla", 14, "Ṇamō Uvajjhāyāṇaṁ", 1, 7, 13),
        (21, "VAISHAKHA", "Krishna", 14, "Ṇamō Uvajjhāyāṇaṁ", 2, 7, 13),
        (22, "VAISHAKHA", "Shukla", 14, "Ṇamō Uvajjhāyāṇaṁ", 3, 7, 13),
        (23, "JYESTHHA", "Krishna", 14, "Ṇamō Uvajjhāyāṇaṁ", 4, 7, 13),
        (24, "JYESTHHA", "Shukla", 14, "Ṇamō Uvajjhāyāṇaṁ", 5, 7, 13),
        (25, "ASHADHA", "Krishna", 14, "Ṇamō Uvajjhāyāṇaṁ", 6, 7, 13),
        (26, "ASHADHA", "Shukla", 14, "Ṇamō Uvajjhāyāṇaṁ", 7, 7, 13),

        (27, "SHRAVANA", "Krishna", 9, "Ṇamō Lōē Savvasāhūṇaṁ", 1, 9, 8),
        (28, "SHRAVANA", "Shukla", 9, "Ṇamō Lōē Savvasāhūṇaṁ", 2, 9, 8),
        (29, "BHADRAPADA", "Krishna", 9, "Ṇamō Lōē Savvasāhūṇaṁ", 3, 9, 8),
        (30, "BHADRAPADA", "Shukla", 9, "Ṇamō Lōē Savvasāhūṇaṁ", 4, 9, 8),
        (31, "ASHWIN", "Krishna", 9, "Ṇamō Lōē Savvasāhūṇaṁ", 5, 9, 8),
        (32, "ASHWIN", "Shukla", 9, "Ṇamō Lōē Savvasāhūṇaṁ", 6, 9, 8),
        (33, "KARTIKA", "Krishna", 9, "Ṇamō Lōē Savvasāhūṇaṁ", 7, 9, 8),
        (34, "KARTIKA", "Shukla", 9, "Ṇamō Lōē Savvasāhūṇaṁ", 8, 9, 8),
        (35, "MARGASHIRSHA", "Krishna", 9, "Ṇamō Lōē Savvasāhūṇaṁ", 9, 9, 8),
    ]

    MONTH_ALIASES = {
        "ASHADHA": ["ASHADHA", "ASAR", "ASADH"],
        "SHRAVANA": ["SHRAVANA", "SAVAN", "SHRAVAN"],
        "BHADRAPADA": ["BHADRAPADA", "BHADO", "BHADRA"],
        "ASHWIN": ["ASHWIN", "ASHVINA", "ASO", "ASOJ"],
        "KARTIKA": ["KARTIKA", "KATAK", "KARTIK"],
        "MARGASHIRSHA": ["MARGASHIRSHA", "MAGSAR", "AGRAHAYANA", "MANSIR", "MARGASHIRSA"],
        "PAUSHA": ["PAUSHA", "POSH", "PAUSH"],
        "MAGHA": ["MAGHA", "MAH", "MHA", "MAGH"],
        "PHALGUNA": ["PHALGUNA", "FALGUN", "PHAGAN", "PHALGUN"],
        "CHAITRA": ["CHAITRA", "CHAIT", "CHET"],
        "VAISHAKHA": ["VAISHAKHA", "BAISAKH", "VAISHAKH"],
        "JYESTHHA": ["JYESTHHA", "JETH", "JYESHTHA"]
    }

    @staticmethod
    def _ordinal(n: int) -> str:
        if 11 <= (n % 100) <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        occurrences = []

        year_snaps = [s for s in snapshots if s["date"].year == year]
        if not year_snaps:
            return []

        for step_num, month_key, paksha, tithi, pada, sub_idx, sub_total, fallback_tithi in self.STEPS_DEFINITION:
            aliases = self.MONTH_ALIASES.get(month_key, [month_key])
            m_snaps = [
                s for s in year_snaps
                if s["hindu_month"].upper() in aliases
            ]
            if not m_snaps:
                continue

            if any(s["is_adhika"] for s in m_snaps):
                m_snaps = [s for s in m_snaps if s["is_adhika"]]
            else:
                m_snaps = [s for s in m_snaps if not s["is_adhika"]]

            target_days = [
                s for s in m_snaps
                if s["paksha"] == paksha and s["tithi_in_paksha"] == tithi
            ]

            target_snap = None
            if target_days:
                target_snap = target_days[0]  # Vriddhi -> 1st instance
            else:
                fallback_days = [
                    s for s in m_snaps
                    if s["paksha"] == paksha and s["tithi_in_paksha"] == fallback_tithi
                ]
                if fallback_days:
                    target_snap = fallback_days[-1]  # Kshaya -> preceding day

            if not target_snap:
                continue

            date_str = target_snap["date"].isoformat()
            tithi_name = "Saptami" if tithi == 7 else ("Panchami" if tithi == 5 else ("Chaturdashi" if tithi == 14 else "Navami"))

            if step_num == 1:
                title = "Namokar Mahamantra Vrat (Prarambh - 1/35)"
                b_type = "START"
                badge = "Namokar Vrat #1"
                desc = f"Commencement of the 1.5-year 35-Namokar Vrat chain; First fasting observance (Pada: {pada} - {tithi_name} Vrat {sub_idx}/{sub_total})"
            elif step_num == 35:
                title = "Namokar Mahamantra Vrat (Udyapan / Purna - 35/35)"
                b_type = "END"
                badge = "Namokar Vrat Purna"
                desc = "Culmination, final Navami fasting observance, and Udyapan of the 1.5-year 35-Namokar Mahamantra Vrat chain"
            else:
                title = f"Namokar Mahamantra Vrat ({step_num}/35)"
                b_type = "INTERMEDIATE"
                badge = f"Namokar Vrat #{step_num}"
                ord_str = self._ordinal(step_num)
                desc = f"{ord_str} fasting observance of the Namokar Vrat chain (Pada: {pada} - {tithi_name} Vrat {sub_idx}/{sub_total})"

            occurrences.append({
                "id": f"namokar_vrat_step_{step_num}_{year}",
                "occurrence_id": f"namokar_vrat_step_{step_num}_{year}",
                "name": title,
                "title": title,
                "name_hindi": f"णमोकार महामंत्र व्रत ({step_num}/35)",
                "category": "mahaparv_vrat",
                "badge": badge,
                "badge_color": "orange",
                "is_span": True,
                "boundary_type": b_type,
                "mantra_pada": pada,
                "step_index": step_num,
                "total_steps": 35,
                "start_date": date_str,
                "end_date": date_str,
                "status": "confirmed",
                "description": desc,
                "meaning": desc,
                "observance": f"Namokar Vrat observance for Pada '{pada}', fasting & 108 Mala Jaap.",
                "sources": ["Jain Traditions"]
            })

        return occurrences






































class ChaitraLabdhiVidhanFestival(FestivalRule):
    """Chaitra Krishna Amavasya to Chaitra Shukla Chaturthi: Labdhi Vidhan Vrat."""
    def resolve(self, snapshots: List[Dict[str, Any]], profile: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        year = context["year"]
        jain_snaps = [s for s in snapshots if s["date"].year == year and get_jain_month(s) == "CHAITRA"]
        if not jain_snaps: return []
        if any(s["is_adhika"] for s in jain_snaps):
            jain_snaps = [s for s in jain_snaps if s["is_adhika"]]
        else:
            jain_snaps = [s for s in jain_snaps if not s["is_adhika"]]
            
        amavasya_days = [s for s in jain_snaps if s["paksha"] == "Krishna" and s["tithi_in_paksha"] in [15, 30]]
        start_snap = amavasya_days[0] if amavasya_days else None
        if not start_snap:
            k14 = [s for s in jain_snaps if s["paksha"] == "Krishna" and s["tithi_in_paksha"] == 14]
            if k14: start_snap = k14[-1]
            
        chaturthi_days = [s for s in jain_snaps if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 4]
        end_snap = chaturthi_days[-1] if chaturthi_days else None
        if not end_snap:
            s3 = [s for s in jain_snaps if s["paksha"] == "Shukla" and s["tithi_in_paksha"] == 3]
            if s3: end_snap = s3[-1]
            
        if not start_snap or not end_snap: return []
        
        start_date_str = start_snap["date"].isoformat()
        end_date_str = end_snap["date"].isoformat()
        start_mm_dd = start_snap["date"].strftime("%b %d")
        end_mm_dd = end_snap["date"].strftime("%b %d")
        
        return [
            {
                "id": f"labdhi_vidhan_start_chaitra_{year}",
                "occurrence_id": f"labdhi_vidhan_start_chaitra_{year}",
                "name": "Labdhi Vidhan Vrat Prarambh",
                "title": "Labdhi Vidhan Vrat Prarambh",
                "name_hindi": "लब्धि विधान व्रत प्रारम्भ",
                "category": "mahaparv_vrat",
                "badge": "Vrat Start",
                "badge_color": "orange",
                "is_span": True,
                "span_label": f"Span: {start_mm_dd} - {end_mm_dd}",
                "boundary_type": "START",
                "start_date": start_date_str,
                "end_date": start_date_str,
                "status": "confirmed",
                "description": self.meaning or "Commencement of Labdhi Vidhan Vrat",
                "meaning": self.meaning or "Commencement of Labdhi Vidhan Vrat",
                "observance": self.observance or "Labdhi Vrat Start",
                "sources": self.sources
            },
            {
                "id": f"labdhi_vidhan_purna_chaitra_{year}",
                "occurrence_id": f"labdhi_vidhan_purna_chaitra_{year}",
                "name": "Labdhi Vidhan Vrat Purna",
                "title": "Labdhi Vidhan Vrat Purna",
                "name_hindi": "लब्धि विधान व्रत पूर्ण",
                "category": "mahaparv_vrat",
                "badge": "Vrat End",
                "badge_color": "orange",
                "is_span": True,
                "span_label": f"Span: {start_mm_dd} - {end_mm_dd}",
                "boundary_type": "END",
                "start_date": end_date_str,
                "end_date": end_date_str,
                "status": "confirmed",
                "description": self.meaning or "Conclusion of Labdhi Vidhan Vrat",
                "meaning": self.meaning or "Conclusion of Labdhi Vidhan Vrat",
                "observance": self.observance or "Labdhi Vrat End",
                "sources": self.sources
            }
        ]
