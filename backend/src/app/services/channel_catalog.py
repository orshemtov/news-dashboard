"""Curated catalog of Telegram news channels for suggestion engine.

Each entry has a username, display name, description (used for embedding),
language, and category tags. Descriptions should be rich enough for the
embedding model to compute meaningful similarity against user article vectors.

All usernames have been verified to be real, active Telegram channels.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CatalogChannel:
    username: str
    name: str
    description: str
    language: str  # primary language: he, ar, en, ru, ...
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Catalog — verified real Telegram channels covering Middle-East security,
# geopolitics, Israeli news, Arab world, international affairs, and more.
# ---------------------------------------------------------------------------

CHANNEL_CATALOG: list[CatalogChannel] = [
    # ── Israeli Security & Military ────────────────────────────────────
    CatalogChannel(
        username="abualiexpress",
        name="Abu Ali Express",
        description="Real-time security and military updates from Israel and the Middle East. Covers IDF operations, rocket alerts, border incidents, and breaking security developments.",
        language="he",
        tags=["security", "military", "israel", "breaking"],
    ),
    CatalogChannel(
        username="salehdesk1",
        name="Saleh Desk",
        description="Security and military news desk covering Israel, Gaza, Lebanon, and regional conflicts. Intelligence and field reports.",
        language="he",
        tags=["security", "military", "intelligence"],
    ),
    CatalogChannel(
        username="red_alert_israel",
        name="Red Alert Israel",
        description="Automated rocket alert notifications for Israel. Real-time missile and drone warnings, Iron Dome interceptions, and shelter alerts by region.",
        language="he",
        tags=["alerts", "rockets", "security", "realtime"],
    ),
    CatalogChannel(
        username="SouthFirstResponders",
        name="South First Responders",
        description="First responder updates from southern Israel. Emergency incidents, rescue operations, and community alerts from the Gaza border region.",
        language="he",
        tags=["emergency", "first-responders", "south-israel"],
    ),
    # ── Israeli Politics & General News ────────────────────────────────
    CatalogChannel(
        username="amitsegal",
        name="Amit Segal",
        description="Leading Israeli political journalist. Breaking political news, coalition dynamics, Knesset developments, and government policy analysis in Hebrew.",
        language="he",
        tags=["politics", "israel", "commentary"],
    ),
    CatalogChannel(
        username="rotter_HaMadlif",
        name="Rotter HaMadlif",
        description="Breaking news leaks and early reports from Israel. Unfiltered news updates covering politics, security, crime, and society.",
        language="he",
        tags=["breaking", "leaks", "israel"],
    ),
    CatalogChannel(
        username="yinonews",
        name="Yinon News",
        description="Israeli news and current affairs. Covers politics, economy, social issues, and investigative journalism in Hebrew.",
        language="he",
        tags=["news", "politics", "society"],
    ),
    CatalogChannel(
        username="kann11",
        name="Kann News",
        description="Israel's public broadcasting corporation news channel. Official updates covering politics, economy, defense, and cultural affairs.",
        language="he",
        tags=["news", "broadcast", "official"],
    ),
    CatalogChannel(
        username="calcalistnews",
        name="Calcalist",
        description="Israel's leading business and financial news. Stock market updates, startup ecosystem, tech industry, real estate, and economic policy analysis.",
        language="he",
        tags=["business", "finance", "tech", "economy"],
    ),
    CatalogChannel(
        username="WallaNews",
        name="Walla News",
        description="Walla! News portal. Broad Israeli news coverage including breaking news, politics, sports, entertainment, and lifestyle.",
        language="he",
        tags=["news", "portal", "comprehensive"],
    ),
    CatalogChannel(
        username="N12News",
        name="N12 News",
        description="Channel 12 Israeli news network. Breaking news, political analysis, investigative reports, and major national stories.",
        language="he",
        tags=["news", "broadcast", "breaking"],
    ),
    CatalogChannel(
        username="News13",
        name="Channel 13 News",
        description="Reshet 13 Israeli television news. Political coverage, defense reporting, economic analysis, and investigative journalism.",
        language="he",
        tags=["news", "broadcast", "politics"],
    ),
    # ── Arab World & Regional ──────────────────────────────────────────
    CatalogChannel(
        username="arabworld301news",
        name="301 Arab World",
        description="Arab world news and analysis in Hebrew. Covers political developments, conflicts, and social changes across the Arab Middle East and North Africa.",
        language="he",
        tags=["arab-world", "mena", "analysis"],
    ),
    CatalogChannel(
        username="AlArabiya",
        name="Al Arabiya",
        description="Al Arabiya news network. Pan-Arab and international news, business reports, and cultural coverage in Arabic.",
        language="ar",
        tags=["news", "pan-arab", "business"],
    ),
    CatalogChannel(
        username="BBCArabic",
        name="BBC Arabic",
        description="BBC Arabic service. International news, analysis, and features covering the Middle East, Africa, and world events in Arabic.",
        language="ar",
        tags=["news", "international", "bbc"],
    ),
    CatalogChannel(
        username="AlMayadeenNews",
        name="Al Mayadeen",
        description="Lebanese pan-Arab news network. Coverage of regional conflicts, Palestinian affairs, resistance movements, and Middle East geopolitics in Arabic.",
        language="ar",
        tags=["arab-world", "politics", "conflict"],
    ),
    CatalogChannel(
        username="skynewsarabia",
        name="Sky News Arabia",
        description="Sky News Arabia channel. Breaking news from the Arab world, Gulf states, international politics, economy, and sports.",
        language="ar",
        tags=["news", "arab-world", "breaking"],
    ),
    # ── Iran ───────────────────────────────────────────────────────────
    CatalogChannel(
        username="iranintltv",
        name="Iran International",
        description="Iran International TV news. Coverage of Iranian politics, protests, IRGC activities, nuclear program, and sanctions impact.",
        language="en",
        tags=["iran", "politics", "nuclear", "sanctions"],
    ),
    # ── OSINT & Intelligence ───────────────────────────────────────────
    CatalogChannel(
        username="GeoConfirmed",
        name="GeoConfirmed",
        description="Geolocation verification of conflict events. Visual evidence analysis, mapping combat footage, and verifying military claims worldwide.",
        language="en",
        tags=["osint", "geolocation", "verification"],
    ),
    CatalogChannel(
        username="intelslava",
        name="Intel Slava Z",
        description="Military OSINT and conflict intelligence. Real-time updates on war zones, troop movements, and geopolitical developments.",
        language="en",
        tags=["osint", "military", "conflict"],
    ),
    # ── Geopolitics & International Affairs ────────────────────────────
    CatalogChannel(
        username="MyGPLANET",
        name="GPLANET",
        description="Geopolitical news and analysis. Global power dynamics, diplomatic developments, trade wars, international security, and foreign policy analysis.",
        language="en",
        tags=["geopolitics", "diplomacy", "international"],
    ),
    CatalogChannel(
        username="ukrainewar",
        name="Ukraine War",
        description="Ukraine war real-time updates. Frontline movements, drone strikes, Western aid deliveries, casualty reports, and battlefield developments.",
        language="en",
        tags=["ukraine", "war", "frontline", "realtime"],
    ),
    # ── International Wire Services ────────────────────────────────────
    CatalogChannel(
        username="BBCWorld",
        name="BBC World",
        description="BBC World Service. Global news, analysis, and features covering international affairs, science, culture, and business in English.",
        language="en",
        tags=["news", "international", "bbc", "world"],
    ),
    CatalogChannel(
        username="reuters_world",
        name="Reuters World",
        description="Reuters global news wire. Breaking international news, financial markets, political developments, and enterprise reporting worldwide.",
        language="en",
        tags=["news", "wire", "international", "finance"],
    ),
    CatalogChannel(
        username="AFP_en",
        name="AFP English",
        description="Agence France-Presse English service. International news, photo journalism, fact-checking, and investigative reports from global bureaus.",
        language="en",
        tags=["news", "wire", "international", "fact-check"],
    ),
    # ── Russian-language (Israel & region) ─────────────────────────────
    CatalogChannel(
        username="meduzaio",
        name="Meduza",
        description="Independent Russian journalism. Kremlin politics, war coverage, civil liberties, and analysis of Russian state propaganda.",
        language="ru",
        tags=["russia", "independent", "politics"],
    ),
    # ── Technology & Cyber ─────────────────────────────────────────────
    CatalogChannel(
        username="therecord_media",
        name="The Record",
        description="Cybersecurity news by Recorded Future. Data breaches, ransomware attacks, nation-state hacking, and cyber policy developments.",
        language="en",
        tags=["cybersecurity", "breaches", "hacking"],
    ),
    # ── Humanitarian ───────────────────────────────────────────────────
    CatalogChannel(
        username="MSFupdates",
        name="MSF / Doctors Without Borders",
        description="Medecins Sans Frontieres updates. Medical humanitarian aid in war zones, disease outbreaks, refugee health, and emergency response missions.",
        language="en",
        tags=["humanitarian", "medical", "msf", "health"],
    ),
]


def get_catalog_excluding(existing_usernames: set[str]) -> list[CatalogChannel]:
    """Return catalog channels that are not already in the user's sources."""
    existing_lower = {u.lower() for u in existing_usernames}
    return [ch for ch in CHANNEL_CATALOG if ch.username.lower() not in existing_lower]
