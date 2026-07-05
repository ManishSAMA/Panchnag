package com.example.jainpanchang.domain

import java.time.LocalDate

class Panchang(private val astronomy: Astronomy) {

    val TITHI_NAMES = listOf(
        "Shukla Pratipada", "Shukla Dwitiya", "Shukla Tritiya",
        "Shukla Chaturthi", "Shukla Panchami", "Shukla Shashthi",
        "Shukla Saptami", "Shukla Ashtami", "Shukla Navami",
        "Shukla Dashami", "Shukla Ekadashi", "Shukla Dwadashi",
        "Shukla Trayodashi", "Shukla Chaturdashi", "Purnima",
        "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya",
        "Krishna Chaturthi", "Krishna Panchami", "Krishna Shashthi",
        "Krishna Saptami", "Krishna Ashtami", "Krishna Navami",
        "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi",
        "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya"
    )

    val NAKSHATRA_NAMES = listOf(
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    )

    val YOGA_NAMES = listOf(
        "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
        "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
        "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
        "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
        "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
        "Indra", "Vaidhriti"
    )

    val VARA_NAMES = listOf(
        "Ravivara (Sunday)", "Somavara (Monday)",
        "Mangalavara (Tuesday)", "Budhavara (Wednesday)",
        "Guruvara (Thursday)", "Shukravara (Friday)",
        "Shanivara (Saturday)"
    )

    private val RAHU_KAAL_SLOT = mapOf(
        0 to 8, 1 to 2, 2 to 7, 3 to 5,
        4 to 6, 5 to 4, 6 to 3
    )

    val HINDU_MONTH_NAMES = listOf(
        "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha",
        "Shravana", "Bhadrapada", "Ashwin", "Kartika",
        "Agrahayana", "Pausha", "Magha", "Phalguna"
    )

    val HINDU_MONTH_COMMON_NAMES = mapOf(
        "Chaitra" to "Chaitra",
        "Vaishakha" to "Vaishakh",
        "Jyeshtha" to "Jeth",
        "Ashadha" to "Ashadh",
        "Shravana" to "Shravan",
        "Bhadrapada" to "Bhadarvo",
        "Ashwin" to "Aaso",
        "Kartika" to "Kartak",
        "Agrahayana" to "Maagsar",
        "Pausha" to "Posh",
        "Magha" to "Maha",
        "Phalguna" to "Faagan"
    )

    fun getHinduMonthFromSunLon(sunLon: Double): Pair<String, String> {
        val idx = (sunLon / 30.0).toInt() % 12
        val sanskrit = HINDU_MONTH_NAMES[idx]
        return Pair(sanskrit, HINDU_MONTH_COMMON_NAMES[sanskrit] ?: sanskrit)
    }

    private fun moonSunElongation(jd: Double, ayanamsa: String = "Lahiri"): Double {
        val moon = astronomy.getPlanetaryLongitude(jd, "Moon", ayanamsa)
        val sun = astronomy.getPlanetaryLongitude(jd, "Sun", ayanamsa)
        return (moon - sun + 360.0) % 360.0
    }

    fun findNewMoonBefore(jd: Double, ayanamsa: String = "Lahiri"): Double {
        val e = moonSunElongation(jd, ayanamsa)
        val centre = jd - e / 13.2
        val lo = centre - 3.0
        var prevE = moonSunElongation(lo, ayanamsa)
        for (i in 0..13) {
            val curr = lo + (i + 1) * 0.5
            val currE = moonSunElongation(curr, ayanamsa)
            if (prevE > 270.0 && currE < 90.0) {
                var a = lo + i * 0.5
                var b = curr
                for (j in 0..49) {
                    val mid = (a + b) / 2
                    if (moonSunElongation(mid, ayanamsa) > 180.0) {
                        a = mid
                    } else {
                        b = mid
                    }
                }
                return b
            }
            prevE = currE
        }
        throw IllegalArgumentException("No new moon found before JD $jd")
    }

    fun findNewMoonAfter(jd: Double, ayanamsa: String = "Lahiri"): Double {
        val e = moonSunElongation(jd, ayanamsa)
        val centre = jd + (360.0 - e) / 13.2
        val lo = centre - 3.0
        var prevE = moonSunElongation(lo, ayanamsa)
        for (i in 0..13) {
            val curr = lo + (i + 1) * 0.5
            val currE = moonSunElongation(curr, ayanamsa)
            if (prevE > 270.0 && currE < 90.0) {
                var a = lo + i * 0.5
                var b = curr
                for (j in 0..49) {
                    val mid = (a + b) / 2
                    if (moonSunElongation(mid, ayanamsa) > 180.0) {
                        a = mid
                    } else {
                        b = mid
                    }
                }
                if (b > jd) return b
            }
            prevE = currE
        }
        throw IllegalArgumentException("No new moon found after JD $jd")
    }

    fun findSankrantisInRange(startJd: Double, endJd: Double, ayanamsa: String = "Lahiri"): List<Int> {
        val results = mutableListOf<Int>()
        val step = 0.5
        var t = startJd
        var prevSign = (astronomy.getPlanetaryLongitude(t, "Sun", ayanamsa) / 30.0).toInt() % 12
        t += step
        while (t <= endJd + step) {
            val currSign = (astronomy.getPlanetaryLongitude(t, "Sun", ayanamsa) / 30.0).toInt() % 12
            if (currSign != prevSign) {
                var a = t - step
                var b = t
                for (i in 0..49) {
                    val mid = (a + b) / 2
                    if ((astronomy.getPlanetaryLongitude(mid, "Sun", ayanamsa) / 30.0).toInt() % 12 == prevSign) {
                        a = mid
                    } else {
                        b = mid
                    }
                }
                if (b > startJd && b <= endJd) {
                    results.add(currSign)
                }
                prevSign = currSign
            }
            t += step
        }
        return results
    }

    fun getTithi(sunLon: Double, moonLon: Double): Int {
        val diff = (moonLon - sunLon + 360.0) % 360.0
        val tithiIdx = (diff / 12.0).toInt()
        return tithiIdx + 1
    }

    fun getNakshatra(moonLon: Double): Int {
        val nakshatraLength = 360.0 / 27.0
        val nakshatraIdx = (moonLon / nakshatraLength).toInt()
        return (nakshatraIdx % 27) + 1
    }

    fun getNakshatraPada(moonLon: Double): Int {
        val padaLength = (360.0 / 27.0) / 4.0
        val padaIdx = (moonLon / padaLength).toInt()
        return (padaIdx % 4) + 1
    }

    fun getYoga(sunLon: Double, moonLon: Double): Int {
        val total = (sunLon + moonLon) % 360.0
        val yogaLength = 360.0 / 27.0
        val yogaIdx = (total / yogaLength).toInt()
        return (yogaIdx % 27) + 1
    }

    fun getVara(julianDate: Double): Int {
        val jdInt = Math.floor(julianDate + 0.5).toLong()
        return ((jdInt + 1) % 7).toInt()
    }

    fun getVaraFromDate(localDate: LocalDate): Int {
        return (localDate.dayOfWeek.value) % 7 // Monday is 1 -> 1, Sunday is 7 -> 0
    }
}
