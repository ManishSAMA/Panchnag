# jain_festival_rules.py - Data-driven and OOP rule registry for Jain festivals.

from datetime import timedelta
from typing import List, Dict, Any
from datetime import date

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
                resolved_day = None
                if candidates:
                    if len(candidates) > 1 and self.vriddhi_rule == "second_day":
                        resolved_day = candidates[1]["date"]
                    else:
                        resolved_day = candidates[0]["date"]
                else:
                    # Kshaya
                    next_days = [s for s in matches if s["tithi_in_paksha"] > self.tithi]
                    if next_days:
                        resolved_day = next_days[0]["date"]
                        
                if resolved_day:
                    occurrences.append(self._create_occurrence(resolved_day, resolved_day, self.tithi, self.jain_month, self.paksha, profile))
            else:
                # Recurring monthly
                from itertools import groupby
                keyed = sorted(matches, key=lambda s: (s["hindu_month"], s["date"]))
                for _month_name, group_iter in groupby(keyed, key=lambda s: s["hindu_month"]):
                    group = list(group_iter)
                    candidates = [s for s in group if s["tithi_in_paksha"] == self.tithi]
                    resolved_day = None
                    if candidates:
                        if len(candidates) > 1 and self.vriddhi_rule == "second_day":
                            resolved_day = candidates[1]["date"]
                        else:
                            resolved_day = candidates[0]["date"]
                    else:
                        # Kshaya
                        next_days = [s for s in group if s["tithi_in_paksha"] > self.tithi]
                        if next_days:
                            resolved_day = next_days[0]["date"]
                            
                    if resolved_day:
                        occurrences.append(self._create_occurrence(resolved_day, resolved_day, self.tithi, "Every Month", self.paksha, profile))
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

FESTIVAL_REGISTRY = [
    {
        "id": "mahavir_janma_kalyanak",
        "name": "Mahavir Janma Kalyanak",
        "name_hindi": "महावीर जन्म कल्याणक",
        "category": "kalyanak",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Chaitra",
        "paksha": "Shukla",
        "tithi": 13,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "The birthday of Lord Mahavir, the 24th Tirthankara",
        "observance": "Pujas, reading the Kalpa Sutra, and fasts. Non-Murtipujaks focus on meditation.",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "samvatsari_tapagachchha",
        "name": "Samvatsari (Tapagachchha)",
        "name_hindi": "संवत्सरी (तपगच्छ)",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha"
        ],
        "jain_month": "Bhadrapada",
        "paksha": "Shukla",
        "tithi": 4,
        "vriddhi_rule": "second_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "The final day of Paryushan, the day of universal forgiveness",
        "observance": "Performance of Samvatsari Pratikramana, seek forgiveness with 'Micchami Dukkadam'",
        "sources": [
            "https://www.jainfoundation.in/JAINLIBRARY/books/Historical_Perspective_of_Samvatsari_Day_and_Jain_Calendar_200022_data.pdf"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "samvatsari_sthanakvasi",
        "name": "Samvatsari (Sthanakvasi)",
        "name_hindi": "संवत्सरी (स्थानकवासी)",
        "category": "festival",
        "profiles": [
            "shwetambar_sthanakvasi"
        ],
        "jain_month": "Bhadrapada",
        "paksha": "Shukla",
        "tithi": 5,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "The final day of Paryushan for Sthanakvasis, the day of universal forgiveness",
        "observance": "Meditation, chanting, Pratikramana, and 'Micchami Dukkadam'",
        "sources": [
            "https://www.jainfoundation.in/JAINLIBRARY/books/Historical_Perspective_of_Samvatsari_Day_and_Jain_Calendar_200022_data.pdf"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "samvatsari_terapanthi",
        "name": "Samvatsari (Terapanthi)",
        "name_hindi": "संवत्सरी (तेरापंथी)",
        "category": "festival",
        "profiles": [
            "shwetambar_terapanthi"
        ],
        "jain_month": "Bhadrapada",
        "paksha": "Shukla",
        "tithi": 5,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "The final day of Paryushan for Terapanthis, the day of universal forgiveness",
        "observance": "Strictly non-ritualistic meditation, fasts, and Samvatsari Pratikramana",
        "sources": [
            "https://www.jainfoundation.in/JAINLIBRARY/books/Historical_Perspective_of_Samvatsari_Day_and_Jain_Calendar_200022_data.pdf"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "paryushan_start_tapagachchha",
        "name": "Paryushan Start (Tapagachchha)",
        "name_hindi": "पर्युषण प्रारंभ (तपगच्छ)",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha"
        ],
        "jain_month": "Bhadrapada",
        "paksha": "Krishna",
        "tithi": 12,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Start of the 8-day Paryushan festival of self-purification",
        "observance": "Daily reading of the Kalpa Sutra, listening to discourses, and fasting",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "Relative",
        "relative_to": "samvatsari_tapagachchha",
        "offset_days": -7
    },
    {
        "id": "paryushan_start_sthanakvasi",
        "name": "Paryushan Start (Sthanakvasi)",
        "name_hindi": "पर्युषण प्रारंभ (स्थानकवासी)",
        "category": "festival",
        "profiles": [
            "shwetambar_sthanakvasi"
        ],
        "jain_month": "Bhadrapada",
        "paksha": "Krishna",
        "tithi": 13,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Start of the 8-day Paryushan festival",
        "observance": "Spiritual discourses, meditation, fasting, and reading of scriptures",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "Relative",
        "relative_to": "samvatsari_sthanakvasi",
        "offset_days": -7
    },
    {
        "id": "paryushan_start_terapanthi",
        "name": "Paryushan Start (Terapanthi)",
        "name_hindi": "पर्युषण प्रारंभ (तेरापंथी)",
        "category": "festival",
        "profiles": [
            "shwetambar_terapanthi"
        ],
        "jain_month": "Bhadrapada",
        "paksha": "Krishna",
        "tithi": 13,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Start of the 8-day Paryushan festival",
        "observance": "Scriptural contemplation, fasting, and strict vows",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "Relative",
        "relative_to": "samvatsari_terapanthi",
        "offset_days": -7
    },
    {
        "id": "ayambil_oli_chaitra",
        "name": "Chaitra Ayambil Oli",
        "name_hindi": "चैत्री आयंबिल ओली",
        "category": "fast",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Chaitra",
        "paksha": "Shukla",
        "tithi": "7-15",
        "vriddhi_rule": "all_days",
        "kshaya_rule": "adjust_9_days",
        "adhika_rule": "nija_only",
        "meaning": "A 9-day festival of Ayambil fasts honoring the Navpad",
        "observance": "Eating only once a day of boiled grains/cereals without spice, oil, ghee, milk, or curd",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/ayambil-oli/"
        ],
        "rule_type": "MultiDay",
        "duration_days": 9
    },
    {
        "id": "ayambil_oli_ashvin",
        "name": "Ashvin Ayambil Oli",
        "name_hindi": "आसोज आयंबिल ओली",
        "category": "fast",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Ashwin",
        "paksha": "Shukla",
        "tithi": "7-15",
        "vriddhi_rule": "all_days",
        "kshaya_rule": "adjust_9_days",
        "adhika_rule": "nija_only",
        "meaning": "A 9-day festival of Ayambil fasts honoring the Navpad",
        "observance": "Fasting on boiled grains, performing pujas (Murtipujak) or meditation",
        "sources": [
            "https://www.msjs.org.au/resources/library/knowledge-base/festivals/navpadji-oli/"
        ],
        "rule_type": "MultiDay",
        "duration_days": 9
    },
    {
        "id": "diwali",
        "name": "Diwali (Shri Mahavir Swami Ji - Moksha Kalyanak)",
        "name_hindi": "दिवाली",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Kartika",
        "paksha": "Krishna",
        "tithi": 15,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Lord Mahavir's Nirvana (Moksha) Kalyanak",
        "observance": "Lighting lamps, fasting, chanting prayers",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "jain_new_year",
        "name": "Jain New Year",
        "name_hindi": "नूतन वर्ष (वीर निर्वाण संवत)",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Kartika",
        "paksha": "Shukla",
        "tithi": 1,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Gautam Swami's Kevalgyan Kalyanak, start of VNS year",
        "observance": "Visiting temples, greeting with 'Saal Mubarak', listening to Gautam Swami's Ras",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "jnan_panchami",
        "name": "Jnan Panchami",
        "name_hindi": "ज्ञान पंचमी",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Kartika",
        "paksha": "Shukla",
        "tithi": 5,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Day of worshipping knowledge and scriptures",
        "observance": "Fasting, cleaning and worshipping religious books, performing Jnan Puja",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "dev_diwali",
        "name": "Dev Diwali",
        "name_hindi": "देव दिवाली",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Kartika",
        "paksha": "Shukla",
        "tithi": 15,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Culmination of Kartiki Chaturmas, reopening of Shatrunjay hills",
        "observance": "Illuminating temples, organizing grand pujas, and resuming pilgrimage",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "maun_ekadashi",
        "name": "Maun Agyaras",
        "name_hindi": "मौन ग्यारस",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Margashirsha",
        "paksha": "Shukla",
        "tithi": 11,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Day honoring five Kalyanakas of various Tirthankaras",
        "observance": "Maintaining complete silence (Maun), performing 150 logassa, fasting",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "parshvanath_jayanti",
        "name": "Paush Dashami",
        "name_hindi": "पोष दशमी",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Pausha",
        "paksha": "Krishna",
        "tithi": 10,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Birthday Kalyanak of Lord Parshvanath (23rd Tirthankara)",
        "observance": "Fasting, performing Paush Dashami Pujas, chanting Parshvanath prayers",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "meru_trayodashi",
        "name": "Meru Trayodashi",
        "name_hindi": "मेरु त्रयोदशी",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Magha",
        "paksha": "Krishna",
        "tithi": 13,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Lord Rishabhdev's (Adinath) Nirvana Kalyanak",
        "observance": "Worship of Mount Shatrunjay, specialized pujas and fasts",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "chaumasi_chaudas_ashadha",
        "name": "Ashadha Chaumasi Chaudas",
        "name_hindi": "आषाढी चौमासी चौदश",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Ashadha",
        "paksha": "Shukla",
        "tithi": 14,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Start of the holy Chaturmas period",
        "observance": "Fasting, starting Chaturmas vows, and performing special Pratikramana",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "chaumasi_chaudas_kartika",
        "name": "Kartika Chaumasi Chaudas",
        "name_hindi": "कार्तिकी चौमासी चौदश",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Kartika",
        "paksha": "Shukla",
        "tithi": 14,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "End of the main Chaturmas period",
        "observance": "Performing grand Chaumasi Pratikramana, concluding monsoon vows",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "chaumasi_chaudas_phalguna",
        "name": "Phalguna Chaumasi Chaudas",
        "name_hindi": "फाल्गुनी चौमासी चौदश",
        "category": "festival",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": "Phalguna",
        "paksha": "Shukla",
        "tithi": 14,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Third Chaumasi Chaudas of the year",
        "observance": "Spiritual cleansing, fasting, and performing Chaumasi Pratikramana",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "pakhi_chaudas_shukla",
        "name": "Pakhi Chaudas (Shukla)",
        "name_hindi": "पाखी चौदश (शुक्ल)",
        "category": "parva",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": None,
        "paksha": "Shukla",
        "tithi": 14,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Bi-weekly day of spiritual purification and fasting",
        "observance": "Performance of Pakshik Pratikramana and observing dietary restrictions",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "pakhi_chaudas_krishna",
        "name": "Pakhi Chaudas (Krishna)",
        "name_hindi": "पाखी चौदश (कृष्ण)",
        "category": "parva",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": None,
        "paksha": "Krishna",
        "tithi": 14,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Bi-weekly day of spiritual purification and fasting",
        "observance": "Performance of Pakshik Pratikramana and observing dietary restrictions",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "parva_tithi_ashtami_shukla",
        "name": "Parva Tithi (Shukla Ashtami)",
        "name_hindi": "पर्व तिथि (शुक्ल अष्टमी)",
        "category": "parva",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": None,
        "paksha": "Shukla",
        "tithi": 8,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Fortnightly holy day for fasting and penance",
        "observance": "Observing abstinences, avoiding green vegetables, performing Samayik",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "parva_tithi_ashtami_krishna",
        "name": "Parva Tithi (Krishna Ashtami)",
        "name_hindi": "पर्व तिथि (कृष्ण अष्टमी)",
        "category": "parva",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": None,
        "paksha": "Krishna",
        "tithi": 8,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Fortnightly holy day for fasting and penance",
        "observance": "Avoiding green/root vegetables, engaging in scripture study",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "parva_tithi_purnima",
        "name": "Parva Tithi (Purnima)",
        "name_hindi": "पर्व तिथि (पूर्णिमा)",
        "category": "parva",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": None,
        "paksha": "Shukla",
        "tithi": 15,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Monthly full moon spiritual day",
        "observance": "Temple visits, special prayers, and charitable donations",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "parva_tithi_amavasya",
        "name": "Parva Tithi (Amavasya)",
        "name_hindi": "पर्व तिथि (अमावस्या)",
        "category": "parva",
        "profiles": [
            "shwetambar_murtipujak_tapagachchha",
            "shwetambar_sthanakvasi",
            "shwetambar_terapanthi"
        ],
        "jain_month": None,
        "paksha": "Krishna",
        "tithi": 15,
        "vriddhi_rule": "first_day",
        "kshaya_rule": "next_day",
        "adhika_rule": "nija_only",
        "meaning": "Monthly new moon spiritual day",
        "observance": "Inner contemplation, fasting, and offering prayers",
        "sources": [
            "https://jainpedia.org/themes/practices/festivals/"
        ],
        "rule_type": "SingleTithi"
    },
    {
        "id": "veer_shasan_jayanti",
        "name": "Veer Shasan Jayanti",
        "category": "festival",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Shravana",
        "paksha": "Krishna",
        "tithi": 1,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "munisuvratnath_garbh",
        "name": "Shri Munisuvratnath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Shravana",
        "paksha": "Krishna",
        "tithi": 2,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "kunthunath_garbh",
        "name": "Shri Kunthunath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Shravana",
        "paksha": "Krishna",
        "tithi": 10,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sumatinath_garbh",
        "name": "Shri Sumatinath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Shravana",
        "paksha": "Shukla",
        "tithi": 2,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "neminath_janma_tap",
        "name": "Shri Neminath Ji - Janma & Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Shravana",
        "paksha": "Shukla",
        "tithi": 6,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "parshvanath_moksha",
        "name": "Shri Parshvanath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Shravana",
        "paksha": "Shukla",
        "tithi": 7,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "shreyansnath_moksha",
        "name": "Shri Shreyansnath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Shravana",
        "paksha": "Shukla",
        "tithi": 15,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "vasupujya_kevalgyan",
        "name": "Shri Vasupujya Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Bhadrapada",
        "paksha": "Krishna",
        "tithi": 2,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "shantinath_garbh",
        "name": "Shri Shantinath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Bhadrapada",
        "paksha": "Krishna",
        "tithi": 7,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "suparshvanath_garbh",
        "name": "Shri Suparshvanath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Bhadrapada",
        "paksha": "Shukla",
        "tithi": 6,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "vasupujya_moksha",
        "name": "Shri Vasupujya Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Bhadrapada",
        "paksha": "Shukla",
        "tithi": 14,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "naminath_garbh",
        "name": "Shri Naminath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Ashvin",
        "paksha": "Krishna",
        "tithi": 2,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "neminath_kevalgyan",
        "name": "Shri Neminath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Ashvin",
        "paksha": "Shukla",
        "tithi": 1,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "pushpadant_moksha",
        "name": "Shri Pushpadant Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Ashvin",
        "paksha": "Shukla",
        "tithi": 8,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sheetalnath_moksha",
        "name": "Shri Sheetalnath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Ashvin",
        "paksha": "Shukla",
        "tithi": 8,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "anantnath_garbh",
        "name": "Shri Anantnath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Kartika",
        "paksha": "Krishna",
        "tithi": 1,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sambhavnath_kevalgyan",
        "name": "Shri Sambhavnath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Kartika",
        "paksha": "Krishna",
        "tithi": 4,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "veer_nirvana_prapti",
        "name": "Veer Nirvana Prapti",
        "category": "festival",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Kartika",
        "paksha": "Shukla",
        "tithi": 1,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "gautam_swami_gyan",
        "name": "Shri Gautam Swami Gyan",
        "category": "festival",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Kartika",
        "paksha": "Shukla",
        "tithi": 1,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "pushpadant_kevalgyan_kartika",
        "name": "Shri Pushpadant Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Kartika",
        "paksha": "Shukla",
        "tithi": 2,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "neminath_garbh",
        "name": "Shri Neminath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Kartika",
        "paksha": "Shukla",
        "tithi": 6,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "arahnath_kevalgyan",
        "name": "Shri Arahnath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Kartika",
        "paksha": "Shukla",
        "tithi": 12,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "padmaprabhu_janma_tap",
        "name": "Shri Padmaprabhu Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Kartika",
        "paksha": "Shukla",
        "tithi": 13,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sambhavnath_janma",
        "name": "Shri Sambhavnath Ji - Janma Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Kartika",
        "paksha": "Shukla",
        "tithi": 15,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "mahavir_swami_tap",
        "name": "Shri Mahavir Swami Ji - Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Margashirsha",
        "paksha": "Krishna",
        "tithi": 10,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "pushpadant_janma_tap",
        "name": "Shri Pushpadant Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Margashirsha",
        "paksha": "Shukla",
        "tithi": 1,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "mallinath_janma_tap",
        "name": "Shri Mallinath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Margashirsha",
        "paksha": "Shukla",
        "tithi": 11,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "neminath_kevalgyan_margashirsha",
        "name": "Shri Neminath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Margashirsha",
        "paksha": "Shukla",
        "tithi": 11,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "arahnath_janma_tap",
        "name": "Shri Arahnath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Margashirsha",
        "paksha": "Shukla",
        "tithi": 14,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sambhavnath_tap",
        "name": "Shri Sambhavnath Ji - Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Margashirsha",
        "paksha": "Shukla",
        "tithi": 15,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "mallinath_kevalgyan",
        "name": "Shri Mallinath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Pausha",
        "paksha": "Krishna",
        "tithi": 2,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "chandraprabhu_janma_tap",
        "name": "Shri Chandraprabhu Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Pausha",
        "paksha": "Krishna",
        "tithi": 11,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "parshvanath_janma_tap",
        "name": "Shri Parshvanath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Pausha",
        "paksha": "Krishna",
        "tithi": 11,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sheetalnath_kevalgyan",
        "name": "Shri Sheetalnath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Pausha",
        "paksha": "Krishna",
        "tithi": 14,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "ajitnath_kevalgyan",
        "name": "Shri Ajitnath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Pausha",
        "paksha": "Shukla",
        "tithi": 4,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "shantinath_kevalgyan",
        "name": "Shri Shantinath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Pausha",
        "paksha": "Shukla",
        "tithi": 10,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "abhinandannath_kevalgyan",
        "name": "Shri Abhinandannath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Pausha",
        "paksha": "Shukla",
        "tithi": 14,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "dharmanath_kevalgyan",
        "name": "Shri Dharmanath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Pausha",
        "paksha": "Shukla",
        "tithi": 15,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "padmaprabhu_garbh",
        "name": "Shri Padmaprabhu Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Magha",
        "paksha": "Krishna",
        "tithi": 6,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sheetalnath_janma_tap",
        "name": "Shri Sheetalnath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Magha",
        "paksha": "Krishna",
        "tithi": 12,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "adinath_moksha",
        "name": "Shri Adinath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Magha",
        "paksha": "Krishna",
        "tithi": 14,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "shreyansnath_kevalgyan",
        "name": "Shri Shreyansnath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Magha",
        "paksha": "Krishna",
        "tithi": 15,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "vimalnath_janma_tap",
        "name": "Shri Vimalnath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Magha",
        "paksha": "Shukla",
        "tithi": 4,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "vimalnath_kevalgyan",
        "name": "Shri Vimalnath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Magha",
        "paksha": "Shukla",
        "tithi": 6,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "ajitnath_janma_tap",
        "name": "Shri Ajitnath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Magha",
        "paksha": "Shukla",
        "tithi": 10,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "abhinandannath_janma_tap",
        "name": "Shri Abhinandannath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Magha",
        "paksha": "Shukla",
        "tithi": 12,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "dharmanath_janma_tap",
        "name": "Shri Dharmanath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Magha",
        "paksha": "Shukla",
        "tithi": 13,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "padmaprabhu_moksha",
        "name": "Shri Padmaprabhu Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Krishna",
        "tithi": 4,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "suparshvanath_kevalgyan",
        "name": "Shri Suparshvanath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Krishna",
        "tithi": 6,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "chandraprabhu_kevalgyan",
        "name": "Shri Chandraprabhu Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Krishna",
        "tithi": 7,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "suparshvanath_moksha",
        "name": "Shri Suparshvanath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Krishna",
        "tithi": 7,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "pushpadant_garbh",
        "name": "Shri Pushpadant Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Krishna",
        "tithi": 9,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "adinath_kevalgyan",
        "name": "Shri Adinath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Krishna",
        "tithi": 11,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "shreyansnath_janma_tap",
        "name": "Shri Shreyansnath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Krishna",
        "tithi": 11,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "munisuvratnath_moksha",
        "name": "Shri Munisuvratnath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Krishna",
        "tithi": 12,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "vasupujya_janma_tap",
        "name": "Shri Vasupujya Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Krishna",
        "tithi": 14,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "arahnath_garbh",
        "name": "Shri Arahnath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Shukla",
        "tithi": 3,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "mallinath_moksha",
        "name": "Shri Mallinath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Shukla",
        "tithi": 5,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "chandraprabhu_moksha",
        "name": "Shri Chandraprabhu Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Shukla",
        "tithi": 7,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sambhavnath_garbh",
        "name": "Shri Sambhavnath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Phalguna",
        "paksha": "Shukla",
        "tithi": 8,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "anantnath_moksha",
        "name": "Shri Anantnath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Krishna",
        "tithi": 4,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "parshvanath_kevalgyan",
        "name": "Shri Parshvanath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Krishna",
        "tithi": 4,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "chandraprabhu_garbh",
        "name": "Shri Chandraprabhu Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Krishna",
        "tithi": 5,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sheetalnath_garbh",
        "name": "Shri Sheetalnath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Krishna",
        "tithi": 8,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "adinath_janma_tap",
        "name": "Shri Adinath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Krishna",
        "tithi": 9,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "anantnath_kevalgyan",
        "name": "Shri Anantnath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Krishna",
        "tithi": 15,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "mallinath_garbh",
        "name": "Shri Mallinath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Shukla",
        "tithi": 1,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "kunthunath_kevalgyan",
        "name": "Shri Kunthunath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Shukla",
        "tithi": 3,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "ajitnath_moksha",
        "name": "Shri Ajitnath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Shukla",
        "tithi": 5,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sambhavnath_moksha",
        "name": "Shri Sambhavnath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Shukla",
        "tithi": 6,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sumatinath_janma_tap_kevalgyan_moksha",
        "name": "Shri Sumatinath Ji - Janma, Tap, Kevalgyan, Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Shukla",
        "tithi": 11,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "arahnath_moksha",
        "name": "Shri Arahnath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Shukla",
        "tithi": 11,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "padmaprabhu_kevalgyan",
        "name": "Shri Padmaprabhu Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Chaitra",
        "paksha": "Shukla",
        "tithi": 15,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "parshvanath_garbh",
        "name": "Shri Parshvanath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Vaishakha",
        "paksha": "Krishna",
        "tithi": 2,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "munisuvratnath_kevalgyan",
        "name": "Shri Munisuvratnath Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Vaishakha",
        "paksha": "Krishna",
        "tithi": 9,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "munisuvratnath_janma_tap",
        "name": "Shri Munisuvratnath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Vaishakha",
        "paksha": "Krishna",
        "tithi": 10,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "naminath_moksha",
        "name": "Shri Naminath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Vaishakha",
        "paksha": "Krishna",
        "tithi": 14,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "kunthunath_janma_tap_moksha",
        "name": "Shri Kunthunath Ji - Janma, Tap, Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Vaishakha",
        "paksha": "Shukla",
        "tithi": 1,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "abhinandannath_garbh_moksha",
        "name": "Shri Abhinandannath Ji - Garbh, Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Vaishakha",
        "paksha": "Shukla",
        "tithi": 6,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "dharmanath_garbh",
        "name": "Shri Dharmanath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Vaishakha",
        "paksha": "Shukla",
        "tithi": 8,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "mahavir_swami_kevalgyan",
        "name": "Shri Mahavir Swami Ji - Kevalgyan Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Vaishakha",
        "paksha": "Shukla",
        "tithi": 10,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "shreyansnath_garbh",
        "name": "Shri Shreyansnath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Jyeshtha",
        "paksha": "Krishna",
        "tithi": 8,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "vimalnath_garbh",
        "name": "Shri Vimalnath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Jyeshtha",
        "paksha": "Krishna",
        "tithi": 10,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "anantnath_janma_tap",
        "name": "Shri Anantnath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Jyeshtha",
        "paksha": "Krishna",
        "tithi": 12,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "sheetalnath_janma_tap_moksha",
        "name": "Shri Sheetalnath Ji - Janma, Tap, Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Jyeshtha",
        "paksha": "Krishna",
        "tithi": 14,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "shantinath_janma_tap_moksha",
        "name": "Shri Shantinath Ji - Janma, Tap, Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Jyeshtha",
        "paksha": "Krishna",
        "tithi": 14,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "ajitnath_garbh",
        "name": "Shri Ajitnath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Jyeshtha",
        "paksha": "Krishna",
        "tithi": 15,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "dharmanath_moksha",
        "name": "Shri Dharmanath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Jyeshtha",
        "paksha": "Shukla",
        "tithi": 4,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "suparshvanath_janma_tap",
        "name": "Shri Suparshvanath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Jyeshtha",
        "paksha": "Shukla",
        "tithi": 12,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "munisuvratnath_garbh_ashadha",
        "name": "Shri Munisuvratnath Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Ashadha",
        "paksha": "Krishna",
        "tithi": 2,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "vasupujya_garbh",
        "name": "Shri Vasupujya Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Ashadha",
        "paksha": "Krishna",
        "tithi": 6,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "vimalnath_moksha",
        "name": "Shri Vimalnath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Ashadha",
        "paksha": "Krishna",
        "tithi": 6,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "naminath_janma_tap",
        "name": "Shri Naminath Ji - Janma, Tap Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Ashadha",
        "paksha": "Krishna",
        "tithi": 10,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "mahavir_swami_garbh",
        "name": "Shri Mahavir Swami Ji - Garbh Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Ashadha",
        "paksha": "Shukla",
        "tithi": 6,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    },
    {
        "id": "neminath_moksha",
        "name": "Shri Neminath Ji - Moksha Kalyanak",
        "category": "kalyanak",
        "profiles": [
            "all"
        ],
        "rule_type": "SingleTithi",
        "jain_month": "Ashadha",
        "paksha": "Shukla",
        "tithi": 8,
        "name_hindi": "",
        "meaning": "",
        "observance": "",
        "sources": [],
        "vriddhi_rule": None,
        "kshaya_rule": None,
        "adhika_rule": None
    }
]
