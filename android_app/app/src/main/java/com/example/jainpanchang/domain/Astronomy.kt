package com.example.jainpanchang.domain

import de.thmac.swisseph.SweConst
import de.thmac.swisseph.SwissEph
import de.thmac.swisseph.SweDate
import de.thmac.swisseph.DblObj
import java.time.LocalDate
import java.time.ZoneId
import java.time.ZonedDateTime

class Astronomy {
    private val swe = SwissEph()

    init {
        // Points to internal ephemeris Moshier by default
        swe.swe_set_ephe_path("")
    }

    val AYANAMSA_SYSTEMS = mapOf(
        "Lahiri" to SweConst.SE_SIDM_LAHIRI,
        "Raman" to SweConst.SE_SIDM_RAMAN,
        "Krishnamurti" to SweConst.SE_SIDM_KRISHNAMURTI
    )

    val RASHI_NAMES = listOf(
        "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)",
        "Karka (Cancer)", "Simha (Leo)", "Kanya (Virgo)",
        "Tula (Libra)", "Vrishchika (Scorpio)", "Dhanu (Sagittarius)",
        "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)"
    )

    val SUN_RASHI_NAMES = listOf(
        "Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya",
        "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen"
    )

    val PLANETS = mapOf(
        "Sun" to SweConst.SE_SUN,
        "Moon" to SweConst.SE_MOON,
        "Mars" to SweConst.SE_MARS,
        "Mercury" to SweConst.SE_MERCURY,
        "Jupiter" to SweConst.SE_JUPITER,
        "Venus" to SweConst.SE_VENUS,
        "Saturn" to SweConst.SE_SATURN,
        "Rahu" to SweConst.SE_TRUE_NODE
    )

    fun getJulianDate(year: Int, month: Int, day: Int, hourUtc: Double): Double {
        val sd = SweDate(year, month, day, hourUtc, true) // true for Gregorian
        return sd.getJulDay()
    }

    fun localTimeToJd(year: Int, month: Int, day: Int, localHour: Double, tzOffset: Double = 5.5): Double {
        var hourUtc = localHour - tzOffset
        var deltaDays = 0
        if (hourUtc < 0) {
            hourUtc += 24.0
            deltaDays = -1
        } else if (hourUtc >= 24.0) {
            hourUtc -= 24.0
            deltaDays = 1
        }
        val sd = SweDate(year, month, day, hourUtc, true)
        return sd.getJulDay() + deltaDays
    }

    fun zonedDatetimeToJd(localDt: ZonedDateTime): Double {
        val utcDt = localDt.withZoneSameInstant(ZoneId.of("UTC"))
        val hourUtc = utcDt.hour + utcDt.minute / 60.0 + utcDt.second / 3600.0 + utcDt.nano / 3_600_000_000_000.0
        val sd = SweDate(utcDt.year, utcDt.monthValue, utcDt.dayOfMonth, hourUtc, true)
        return sd.getJulDay()
    }

    fun localDateAnchorJd(localDate: LocalDate, tzName: String, hour: Int = 0): Double {
        val localDt = localDate.atTime(hour, 0).atZone(ZoneId.of(tzName))
        return zonedDatetimeToJd(localDt)
    }

    fun getAyanamsa(julianDate: Double, ayanamsaName: String = "Lahiri"): Double {
        val sidMode = AYANAMSA_SYSTEMS[ayanamsaName] ?: SweConst.SE_SIDM_LAHIRI
        swe.swe_set_sid_mode(sidMode, 0.0, 0.0)
        return swe.swe_get_ayanamsa_ut(julianDate)
    }

    private fun setSiderealMode(ayanamsaName: String) {
        val sidMode = AYANAMSA_SYSTEMS[ayanamsaName] ?: SweConst.SE_SIDM_LAHIRI
        swe.swe_set_sid_mode(sidMode, 0.0, 0.0)
    }

    fun getPlanetaryLongitude(julianDate: Double, planetName: String, ayanamsaName: String = "Lahiri"): Double {
        if (planetName == "Ketu") {
            val rahuLon = getPlanetaryLongitude(julianDate, "Rahu", ayanamsaName)
            return (rahuLon + 180.0) % 360.0
        }
        val planetId = PLANETS[planetName] ?: return 0.0
        setSiderealMode(ayanamsaName)
        
        val flags = SweConst.SEFLG_SWIEPH or SweConst.SEFLG_SIDEREAL or SweConst.SEFLG_SPEED
        val res = DoubleArray(6)
        val err = StringBuffer()
        swe.swe_calc_ut(julianDate, planetId, flags, res, err)
        return res[0] % 360.0
    }

    fun getAllPlanetPositions(julianDate: Double, ayanamsaName: String = "Lahiri"): Map<String, Double> {
        val result = mutableMapOf<String, Double>()
        setSiderealMode(ayanamsaName)
        val flags = SweConst.SEFLG_SWIEPH or SweConst.SEFLG_SIDEREAL or SweConst.SEFLG_SPEED

        for ((name, pid) in PLANETS) {
            val res = DoubleArray(6)
            val err = StringBuffer()
            swe.swe_calc_ut(julianDate, pid, flags, res, err)
            result[name] = res[0] % 360.0
        }
        result["Ketu"] = ((result["Rahu"] ?: 0.0) + 180.0) % 360.0
        return result
    }

    fun decimalToDms(decimalDegrees: Double): Triple<Int, Int, Double> {
        val d = decimalDegrees.toInt()
        val mDec = (decimalDegrees - d) * 60.0
        val m = mDec.toInt()
        val s = (mDec - m) * 60.0
        return Triple(d, m, s)
    }

    fun formatDms(decimalDegrees: Double): String {
        val (d, m, s) = decimalToDms(decimalDegrees)
        return String.format("%3d° %02d' %05.2f\"", d, m, s)
    }

    fun getRashiName(decimalDegrees: Double): String {
        val idx = (decimalDegrees / 30.0).toInt() % 12
        return RASHI_NAMES[idx]
    }

    fun getSunRashi(jdSunrise: Double): String {
        val flags = SweConst.SEFLG_SWIEPH or SweConst.SEFLG_SPEED
        val res = DoubleArray(6)
        val err = StringBuffer()
        swe.swe_calc_ut(jdSunrise, SweConst.SE_SUN, flags, res, err)
        val tropicalLon = res[0]
        swe.swe_set_sid_mode(SweConst.SE_SIDM_LAHIRI, 0.0, 0.0)
        val ayanamsa = swe.swe_get_ayanamsa_ut(jdSunrise)
        val siderealLon = (tropicalLon - ayanamsa + 360.0) % 360.0
        val idx = (siderealLon / 30.0).toInt() % 12
        return SUN_RASHI_NAMES[idx]
    }

    private fun riseSet(julianDate: Double, body: Int, lat: Double, lon: Double, isRise: Boolean): Double {
        val geopos = doubleArrayOf(lon, lat, 0.0)
        val rsmi = if (isRise) SweConst.SE_CALC_RISE else SweConst.SE_CALC_SET
        
        val tret = DblObj()
        val err = StringBuffer()
        
        try {
            val ret = swe.swe_rise_trans(
                julianDate,
                body,
                StringBuffer(""),
                SweConst.SEFLG_SWIEPH,
                rsmi,
                geopos,
                1013.25,
                15.0,
                tret,
                err
            )
            if (ret == 0 && tret.`val` > 0) {
                return tret.`val`
            }
        } catch (e: Exception) {}
        
        return 0.0
    }

    fun getSunrise(julianDate: Double, lat: Double, lon: Double): Double {
        return riseSet(julianDate, SweConst.SE_SUN, lat, lon, true)
    }

    fun getSunset(julianDate: Double, lat: Double, lon: Double): Double {
        return riseSet(julianDate, SweConst.SE_SUN, lat, lon, false)
    }

    fun getMoonrise(julianDate: Double, lat: Double, lon: Double): Double {
        return riseSet(julianDate, SweConst.SE_MOON, lat, lon, true)
    }

    fun getMoonset(julianDate: Double, lat: Double, lon: Double): Double {
        return riseSet(julianDate, SweConst.SE_MOON, lat, lon, false)
    }

    fun jdToLocalTimeString(jd: Double, tzOffset: Double = 5.5): String {
        if (jd == 0.0) return "--:--:--"
        try {
            val s = SweDate(jd)
            var hLocal = s.hour + tzOffset
            hLocal %= 24.0
            if (hLocal < 0) hLocal += 24.0
            val hh = hLocal.toInt()
            val mmFloat = (hLocal - hh) * 60.0
            val mm = mmFloat.toInt()
            val ss = ((mmFloat - mm) * 60.0).toInt()
            return String.format("%02d:%02d:%02d", hh, mm, ss)
        } catch (e: Exception) {
            return "--:--:--"
        }
    }

    fun buildEclipseDateSets(startJd: Double, endJd: Double, lat: Double, lon: Double): Pair<Set<String>, Set<String>> {
        val geopos = doubleArrayOf(lon, lat, 0.0)
        val solarDates = mutableSetOf<String>()
        val lunarDates = mutableSetOf<String>()

        var jd = startJd
        val tret = DoubleArray(10)
        val attr = DoubleArray(20)
        val err = StringBuffer()

        while (jd < endJd) {
            try {
                val ret = swe.swe_sol_eclipse_when_loc(jd, SweConst.SEFLG_SWIEPH, geopos, tret, attr, 0, err)
                if (ret > 0 && tret[0] > 0) {
                    val s = SweDate(tret[0])
                    solarDates.add(String.format("%04d-%02d-%02d", s.year, s.month, s.day))
                    jd = tret[0] + 20.0
                } else {
                    jd += 150.0
                }
            } catch (e: Exception) {
                jd += 150.0
            }
        }

        jd = startJd
        while (jd < endJd) {
            try {
                val ret = swe.swe_lun_eclipse_when_loc(jd, SweConst.SEFLG_SWIEPH, geopos, tret, attr, 0, err)
                if (ret > 0 && tret[0] > 0) {
                    val s = SweDate(tret[0])
                    lunarDates.add(String.format("%04d-%02d-%02d", s.year, s.month, s.day))
                    jd = tret[0] + 20.0
                } else {
                    jd += 25.0
                }
            } catch (e: Exception) {
                jd += 25.0
            }
        }

        return Pair(solarDates, lunarDates)
    }
}
