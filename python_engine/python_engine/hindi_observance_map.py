# -*- coding: utf-8 -*-
"""Curated Hindi renderings for festival `observance` strings and residual names.

The registry carries `name_hindi` for most festivals but has no `observance_hindi`
field at all, so the Aradhana column of any Hindi export falls back to English.
This module supplies a reviewed, per-string translation rather than word-level
substitution, which mangles Jain terminology (e.g. "Austerity Kalyanak" is
दीक्षा कल्याणक, not a literal rendering of "austerity").

Prakrit mantra padas (Ṇamō Arihantāṇaṁ and the rest) are deliberately kept in
their transliterated form inside the Hindi text -- they are recited as-is.

TRANSLATION STATUS: machine-drafted, NOT yet reviewed by a Jain scholar or
native Hindi reviewer. Terms most worth a second look are marked "# review:".
"""

OBSERVANCE_HI = {
    # --- Kalyanak / general worship -------------------------------------------
    "Special prayers, pujas, and temple visits.": "विशेष प्रार्थना, पूजा एवं मंदिर दर्शन।",
    "Special prayers and reading of scriptures": "विशेष प्रार्थना एवं शास्त्र वाचन",
    "Special prayers, Swadhyay, and scripture recitation.": "विशेष प्रार्थना, स्वाध्याय एवं शास्त्र पाठ।",
    "Special prayers and conclusion of monsoon stay": "विशेष प्रार्थना एवं चातुर्मास समापन",
    "Scripture recitation and Agam Puja": "शास्त्र पाठ एवं आगम पूजा",
    "Scripture reverence and Swadhyay": "शास्त्र विनय एवं स्वाध्याय",
    "Worship, community gathering": "पूजा एवं सामूहिक आयोजन",
    "Fasting and worship": "उपवास एवं पूजा",
    "Puja, Fasting, Temple visits": "पूजा, उपवास एवं मंदिर दर्शन",
    "Rath Yatra, Puja, Fasting": "रथ यात्रा, पूजा एवं उपवास",
    "Jina Darshan before morning meals": "प्रातः भोजन से पूर्व जिन दर्शन",

    # --- Pratikraman / Samvatsari ---------------------------------------------
    "Pakshik Pratikraman": "पाक्षिक प्रतिक्रमण",
    "Chaumasi Pratikraman": "चौमासी प्रतिक्रमण",
    "Samvatsari Pratikramana, Fasting, Kshamavani": "सांवत्सरिक प्रतिक्रमण, उपवास एवं क्षमावाणी",
    "Kshamapana & Upvas": "क्षमापना एवं उपवास",
    "Varsha-Ant Pratikramana, Year-End Reflection, Shanti Paath":
        "वर्षांत प्रतिक्रमण, वर्ष-समीक्षा एवं शांति पाठ",

    # --- Fasting forms ---------------------------------------------------------
    "Fasting and Bhaktambar Stotra Aradhana": "उपवास एवं भक्तामर स्तोत्र आराधना",
    "Fasting and Pushpa offering": "उपवास एवं पुष्प अर्पण",
    "Fasting and Ratnatraya Aradhana": "उपवास एवं रत्नत्रय आराधना",
    "Fasting and Shodashkaran Aradhana": "उपवास एवं षोडशकारण आराधना",
    "Fasting and ten virtues Aradhana": "उपवास एवं दस धर्म आराधना",
    "Fasting and Sapta Rishi Puja": "उपवास एवं सप्त ऋषि पूजा",
    "Fasting and Sapta Paramsthan Aradhana": "उपवास एवं सप्त परमस्थान आराधना",
    "Fasting and Akshaya Nidhi Aradhana": "उपवास एवं अक्षय निधि आराधना",
    "Fasting and Rakshabandhan Mahaparv celebration": "उपवास एवं रक्षाबंधन महापर्व",
    "Fasting and Labdhi Vidhan Aradhana": "उपवास एवं लब्धि विधान आराधना",
    "Fasting and Teen Chaubisi Tirthankara Aradhana": "उपवास एवं तीन चौबीसी तीर्थंकर आराधना",
    "Fasting and Abhaya Aradhana": "उपवास एवं अभय आराधना",
    "Fasting and Shalya-Tyaga Aradhana": "उपवास एवं शल्य-त्याग आराधना",
    "Fasting and Sankat Haran Aradhana": "उपवास एवं संकट हरण आराधना",
    "Fasting and Samyak Shraddha Aradhana": "उपवास एवं सम्यक श्रद्धा आराधना",
    "Fasting, Anant Sutra Aradhana": "उपवास एवं अनंत सूत्र आराधना",
    "Fasting, Ratnatraya Aradhana, Swadhyay": "उपवास, रत्नत्रय आराधना एवं स्वाध्याय",
    "Fasting, Swadhyay, and Dhoop Dashami Aradhana": "उपवास, स्वाध्याय एवं धूप दशमी आराधना",
    "Fast on Chaturdashi tithis": "चतुर्दशी तिथियों पर उपवास",
    "Fast starts at sunrise, single saltless meal in afternoon.":
        "उपवास सूर्योदय से आरंभ; दोपहर में एक बार नमक रहित आहार।",
    "Sunday fasts": "रविवार के उपवास",
    "Fistful grain donation/restriction fasting": "मुट्ठी अन्न दान एवं संयम उपवास",  # review
    "Austere penance and Tala Dhar Tap fasting": "कठोर तप एवं ताला धर तप उपवास",  # review
    "Monsoon penance and Nirjara aradhana": "वर्षाकालीन तप एवं निर्जरा आराधना",
    "Solah Karan Bhavna contemplation and fasting": "सोलह कारण भावना चिंतन एवं उपवास",
    "Sugarcane juice parana & Ahar Dan": "इक्षुरस पारणा एवं आहार दान",
    "Fasting and worship of Bhagwan Vasupujya; traditionally observed by women for family well-being.":
        "भगवान वासुपूज्य की उपवास एवं पूजा; परंपरागत रूप से महिलाओं द्वारा परिवार के कल्याण हेतु।",

    # --- Namokar 35-vrat chain (Prakrit padas kept as recited) -----------------
    "Namokar Vrat observance for Pada 'Ṇamō Arihantāṇaṁ', fasting & 108 Mala Jaap.":
        "‘णमो अरिहंताणं’ पद हेतु णमोकार व्रत आराधना; उपवास एवं 108 माला जाप।",
    "Namokar Vrat observance for Pada 'Ṇamō Siddhāṇaṁ', fasting & 108 Mala Jaap.":
        "‘णमो सिद्धाणं’ पद हेतु णमोकार व्रत आराधना; उपवास एवं 108 माला जाप।",
    "Namokar Vrat observance for Pada 'Ṇamō Āyariyāṇaṁ', fasting & 108 Mala Jaap.":
        "‘णमो आयरियाणं’ पद हेतु णमोकार व्रत आराधना; उपवास एवं 108 माला जाप।",
    "Namokar Vrat observance for Pada 'Ṇamō Uvajjhāyāṇaṁ', fasting & 108 Mala Jaap.":
        "‘णमो उवज्झायाणं’ पद हेतु णमोकार व्रत आराधना; उपवास एवं 108 माला जाप।",
    "Namokar Vrat observance for Pada 'Ṇamō Lōē Savvasāhūṇaṁ', fasting & 108 Mala Jaap.":
        "‘णमो लोए सव्वसाहूणं’ पद हेतु णमोकार व्रत आराधना; उपवास एवं 108 माला जाप।",

    # --- Oli / Ashtahnika / Nandishwar ----------------------------------------
    "Ayambil Fasting, Navapad Pujan & Tap": "आयंबिल तप, नवपद पूजन एवं तप",
    "Navapad Oli Nishthapan, Purnima Aradhana": "नवपद ओली निष्ठापन एवं पूर्णिमा आराधना",
    "Nandishwar Dvipa Puja & Fasting": "नंदीश्वर द्वीप पूजा एवं उपवास",
    "Ashtahnika Parv Nishthapan, Nandishwar Grand Pujan, Siddha Bhakti":
        "अष्टाह्निका पर्व निष्ठापन, नंदीश्वर महापूजन एवं सिद्ध भक्ति",
    "Nandishwar Vidhana, Siddhachakra Aradhana, Shrut & Jina Pujan":
        "नंदीश्वर विधान, सिद्धचक्र आराधना एवं श्रुत-जिन पूजन",

    # --- Labdhi / Ratnatraya / Sankat Haran ------------------------------------
    "Labdhi Vrat Aradhana": "लब्धि व्रत आराधना",
    "Labdhi Vrat Aradhana, Siddha Bhakti, Purna Ahuti": "लब्धि व्रत आराधना, सिद्ध भक्ति एवं पूर्ण आहुति",
    "Ratnatraya Vrat Conclusion, Purna Ahuti": "रत्नत्रय व्रत समापन एवं पूर्ण आहुति",
    "Conclusion of Sankat Haran Vrat": "संकट हरण व्रत का समापन",
    "Conclusion of Shraddha Vrat": "श्रद्धा व्रत का समापन",
    "Das Lakshan Purna, Anantnath Bhagwan Moksha Kalyanak Pujan":
        "दस लक्षण पूर्ण एवं अनंतनाथ भगवान मोक्ष कल्याणक पूजन",

    # --- Swadhyay / Shrut ------------------------------------------------------
    "Kalpasutra Swadhyay and Tap-Aradhana": "कल्पसूत्र स्वाध्याय एवं तप आराधना",
    "Jinvani Puja and Swadhyay": "जिनवाणी पूजा एवं स्वाध्याय",
    "Jinvani Puja, Swadhyay": "जिनवाणी पूजा एवं स्वाध्याय",
    "Jinavani Pujan, Shrut Aradhana, Shastra Vandana": "जिनवाणी पूजन, श्रुत आराधना एवं शास्त्र वंदना",
    "Shrut Jnana Aradhana, Shastra Pujan, Fasting & Swadhyay":
        "श्रुत ज्ञान आराधना, शास्त्र पूजन, उपवास एवं स्वाध्याय",
    "Samyak Jnana Aradhana, Shastra Pujan, Jin Agam Vachana":
        "सम्यक ज्ञान आराधना, शास्त्र पूजन एवं जिन आगम वाचन",
    "Kundakunda Dev Pujan, Samayasara Swadhyay, Agam Pujan":
        "कुंदकुंद देव पूजन, समयसार स्वाध्याय एवं आगम पूजन",
    "Stotra Path, Bhakti-Vandana, Jinavani Swadhyay, Sheetalnath Jin Pujan":
        "स्तोत्र पाठ, भक्ति-वंदना, जिनवाणी स्वाध्याय एवं शीतलनाथ जिन पूजन",
    "Uttama Mardava Swadhyay and Maan-Chheen Dhyana": "उत्तम मार्दव स्वाध्याय एवं मान-क्षीण ध्यान",  # review
    "Chaturmas Sthirata and Svadhyay Span": "चातुर्मास स्थिरता एवं स्वाध्याय काल",
    "Samadhi Aradhana, Swadhyay, and Viniyojita Tap": "समाधि आराधना, स्वाध्याय एवं विनियोजित तप",
    "Swadhyay, Muni Vandan, and Rishi Panchami Aradhana": "स्वाध्याय, मुनि वंदन एवं ऋषि पंचमी आराधना",

    # --- Diwali cluster --------------------------------------------------------
    "Dhyan and Samayik, Ratnatraya / Atma-Dhan Aradhana, Padam Prabhu Bhagwan Kalyanak Pujan, Deepotsav Initiation":
        "ध्यान एवं सामायिक, रत्नत्रय / आत्म-धन आराधना, श्री पद्मप्रभ भगवान कल्याणक पूजन एवं दीपोत्सव आरंभ",
    "Laddoo offering & Swadhyay": "लाडू अर्पण एवं स्वाध्याय",
    "Lighting of lamps, offering of Nirvan Ladoo.": "दीप प्रज्वलन एवं निर्वाण लाडू अर्पण।",
    "Nirvana Laddu Offering, Moksha Kalyan Pujan, Deepotsav":
        "निर्वाण लाडू अर्पण, मोक्ष कल्याण पूजन एवं दीपोत्सव",
    "Varsha Yog Nishthapan Vidhi, Chaturmas Parana": "वर्षा योग निष्ठापन विधि एवं चातुर्मास पारणा",
    "Vira Nirvana Samvat Nutan Varsh, Chopda Pujan, Nutan Varsh Abhinandan":
        "वीर निर्वाण संवत् नूतन वर्ष, चोपड़ा पूजन एवं नूतन वर्ष अभिनंदन",
    "Gautam Swami Pujan, Kevalgyan Aradhana": "गौतम स्वामी पूजन एवं केवलज्ञान आराधना",
    "Business Reopening, Shubh-Labh Pujan, Ledger Commencement":
        "व्यापार पुनरारंभ, शुभ-लाभ पूजन एवं बही-खाता आरंभ",
    "Jinalaya Deepotsav, Shatrunjaya Teerth Yatra, Jin Pujan":
        "जिनालय दीपोत्सव, शत्रुंजय तीर्थ यात्रा एवं जिन पूजन",
    "Dhoop Aradhana in Jinalayas, Jin Pujan, Swadhyay":
        "जिनालयों में धूप आराधना, जिन पूजन एवं स्वाध्याय",

    # --- Rakshabandhan / Bhaiya Dooj / misc -----------------------------------
    "Special Mahaparv celebration, Munis Protection remembrance":
        "विशेष महापर्व आयोजन एवं मुनि रक्षा स्मरण",
    "Special Pujan of Muni Vishnukumar and Acharya Akampanacharya":
        "मुनि विष्णुकुमार एवं आचार्य अकम्पनाचार्य का विशेष पूजन",
    "Sorana Pujan and Raksha Sutra Bandhan": "सोरण पूजन एवं रक्षा सूत्र बंधन",  # review: "Sorana"
    "Tilak & Raksha Vidhi, Bhratri Pujan, Family Fellowship":
        "तिलक एवं रक्षा विधि, भ्रातृ पूजन एवं पारिवारिक मिलन",
    "Mangal Kalash worship and spiritual purification": "मंगल कलश पूजन एवं आत्म शुद्धि",
    "Meru Sthapana, Akrtrim Chaityalaya Pujan": "मेरु स्थापना एवं अकृत्रिम चैत्यालय पूजन",
    "Jina Pratishtha, Patotsav Abhisheka, Temple Consecration":
        "जिन प्रतिष्ठा, पाटोत्सव अभिषेक एवं मंदिर प्रतिष्ठा",
    "Jina Abhishek, Full-Moon Pujan, Vasantotsav Aradhana":
        "जिन अभिषेक, पूर्णिमा पूजन एवं वसंतोत्सव आराधना",
    "Bonfire Pujan in Pradosha Kaal, Bhakti Pujan, Utsav Rituals":
        "प्रदोष काल में होलिका पूजन, भक्ति पूजन एवं उत्सव विधि",
    "Ahimsa, Abhayadan, Gaushala Seva, Karuna Bhavna":
        "अहिंसा, अभयदान, गौशाला सेवा एवं करुणा भावना",
    "Chandrodaya Fasting, Moon Worship": "चंद्रोदय उपवास एवं चंद्र पूजन",
    "Pradosha Evening Fasting, Star Sighting": "प्रदोष कालीन उपवास एवं तारा दर्शन",
    "Pradosha Evening Vrat, Star Sighting": "प्रदोष कालीन व्रत एवं तारा दर्शन",
}

# Festival names translate_fest() leaves partly in Latin.
NAME_HI = {
    "☀️ Ravi Vrat": "☀️ रवि व्रत",
    "Karma Nirjara Vrat (Ashadha)": "कर्म निर्जरा व्रत (आषाढ़)",
    "Karma Nirjara Vrat (Shravana)": "कर्म निर्जरा व्रत (श्रावण)",
    "Karma Nirjara Vrat (Bhadrapada)": "कर्म निर्जरा व्रत (भाद्रपद)",
    "Karma Nirjara Vrat (Ashwin)": "कर्म निर्जरा व्रत (आश्विन)",
    "श्री महावीर Swami भगवान Moksha Kalyanak (The Nirvana/Liberation of Lord महावीर, celebrated as Jain Diwali).":
        "श्री महावीर स्वामी भगवान मोक्ष कल्याणक (जैन दीपावली)",
    "श्री Pushpadant (Suvidhinath) भगवान गर्भ कल्याणक":
        "श्री पुष्पदंत (सुविधिनाथ) भगवान गर्भ कल्याणक",
}

# "[Tithi]" disambiguation prefixes carried by some Kalyanak titles.
TITHI_PREFIX_HI = {
    "Pratipada": "प्रथमा", "Ekam": "एकम", "Dwitiya": "द्वितीया", "Tritiya": "तृतीया",
    "Chaturthi": "चतुर्थी", "Panchami": "पंचमी", "Shasthi": "षष्ठी", "Shashthi": "षष्ठी",
    "Saptami": "सप्तमी", "Ashtami": "अष्टमी", "Navami": "नवमी", "Dashami": "दशमी",
    "Ekadashi": "एकादशी", "Dwadashi": "द्वादशी", "Trayodashi": "त्रयोदशी",
    "Chaturdashi": "चतुर्दशी", "Purnima": "पूर्णिमा", "Amavasya": "अमावस्या",
}

# Category labels. janam_kalyanak / garbha_kalyanak are one-off variants of the
# plain "kalyanak" category used by two registry entries.
CATEGORY_HI = {
    "kalyanak": "कल्याणक", "janam_kalyanak": "जन्म कल्याणक", "garbha_kalyanak": "गर्भ कल्याणक",
    "festival": "पर्व", "fast": "उपवास", "parva": "पर्व", "mahaparv": "महापर्व",
    "parva_vrat": "पर्व व्रत", "monthly_vrat": "मासिक व्रत", "jayanti": "जयंती",
    "vrat": "व्रत", "poojan": "पूजन", "parv_vidhi": "पर्व विधि",
    "mahaparv_vrat": "महापर्व व्रत", "punyatithi": "पुण्यतिथि", "punya_tithi": "पुण्यतिथि",
    "tap_vrat": "तप व्रत", "auspicious": "शुभ", "shastra": "शास्त्र", "utsav": "उत्सव",
}

# The Rohini vrat is nakshatra-based, not tithi-based: it carries a nakshatra name
# in the paksha column and a "Nakshatra:" marker where a Jain month would be.
JAIN_MONTH_HI = {"Nakshatra:": "नक्षत्र:"}
PAKSHA_HI = {"Shukla": "शुक्ल", "Krishna": "कृष्ण", "Rohini": "रोहिणी"}
