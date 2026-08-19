"""
Module Name: source_registry.py
Repo Path: src/data/source_registry.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Canonical Registry of all 47 Authorized Public Web & RSS Data Sources.
- Coverage:
  1. Economic & Macro Calendars (BLS, BEA, Census, UMich, ConfBoard, TradingEconomics)
  2. Global Central Banks & Liquidity (Fed H.4.1, NY Fed, KC Fed, ECB, BOJ, BOE, PBoC, etc.)
  3. Sovereign Debt & Yields (TreasuryDirect, FiscalData, Real Yield TIPS)
  4. Corporate Earnings & Filings (SEC EDGAR, Nasdaq, Yahoo, Mag-7 IR)
  5. Derivatives & Microstructure (CBOE, OCC, OpEx calendars)
  6. Commodities & Industry (OPEC, ISM, SEMI billings)
  7. Geopolitics, Sovereign Ratings & Press (ISW, CSIS, S&P, Moody's, Fitch, Reuters, FT, FDIC)
"""

# Import Enum for discrete source categories
from enum import Enum

# Import typing primitives for strict type safety
from typing import List, Dict, Optional, Any

# Import Pydantic v2 core components for schema contracts
from pydantic import BaseModel, Field, ConfigDict, HttpUrl


# Enum defining the 7 institutional source categories
class SourceCategory(str, Enum):
    # Category 1: Economic calendars and growth releases
    MACRO_CALENDAR = "MACRO_CALENDAR"
    # Category 2: Central bank policy, speeches, and balance sheets
    CENTRAL_BANKING = "CENTRAL_BANKING"
    # Category 3: Sovereign debt auctions, TGA, and yield curve plumbing
    TREASURY_AND_YIELDS = "TREASURY_AND_YIELDS"
    # Category 4: Corporate earnings, Mag-7 IR, and SEC filings
    CORPORATE_AND_EARNINGS = "CORPORATE_AND_EARNINGS"
    # Category 5: Options exchanges, OpEx, and volatility schedules
    DERIVATIVES_AND_OPEX = "DERIVATIVES_AND_OPEX"
    # Category 6: Industrial manufacturing, semiconductor equipment, and energy
    SECTOR_AND_COMMODITY = "SECTOR_AND_COMMODITY"
    # Category 7: Geopolitical risk, defense think tanks, ratings agencies, and news wires
    GEOPOLITICS_AND_NEWS = "GEOPOLITICS_AND_NEWS"


# Schema representing an individual registered public data endpoint
class SourceEndpoint(BaseModel):
    # Enforce immutable configuration for audit safety
    model_config = ConfigDict(frozen=True)

    # Unique endpoint identifier key
    name: str = Field(..., description="Unique source identifier key")
    # Public target URL string
    url: str = Field(..., description="Public endpoint URL")
    # Institutional source category classification
    category: SourceCategory = Field(..., description="Assigned institutional category")
    # Brief description of macro data provided
    description: str = Field(default="", description="Scope of macro intelligence provided")
    # Flag indicating whether source provides an RSS feed or standard HTML
    is_rss: bool = Field(default=False, description="True if source provides an RSS/XML feed")


# Canonical dictionary defining all 47 authorized public data sources
RAW_47_SOURCES: List[Dict[str, Any]] = [
    # --- Category 1: Macro & Economic Calendars ---
    {"name": "TradingEconomics", "url": "https://api.tradingeconomics.com/calendar?country=united%20states&c=guest:guest", "category": SourceCategory.MACRO_CALENDAR, "description": "Global economic calendar feed (Free Guest Tier)", "is_rss": False},
    {"name": "BLS_releases", "url": "https://www.bls.gov/schedule/news_release/", "category": SourceCategory.MACRO_CALENDAR, "description": "Bureau of Labor Statistics CPI, PPI, and Employment release schedules", "is_rss": False},
    {"name": "BEA_releases", "url": "https://www.bea.gov/news", "category": SourceCategory.MACRO_CALENDAR, "description": "Bureau of Economic Analysis news releases", "is_rss": False},
    {"name": "BEA_PCE_GDP_pages", "url": "https://www.bea.gov/data", "category": SourceCategory.MACRO_CALENDAR, "description": "BEA official GDP and Core PCE Deflator release tables", "is_rss": False},
    {"name": "US_Census_releases", "url": "https://www.census.gov/newsroom/press-kits.html", "category": SourceCategory.MACRO_CALENDAR, "description": "US Census Bureau Retail Sales and Housing Starts press releases", "is_rss": False},
    {"name": "UMich_Consumer_Sentiment", "url": "https://data.sca.isr.umich.edu/", "category": SourceCategory.MACRO_CALENDAR, "description": "University of Michigan Surveys of Consumers sentiment and inflation expectations", "is_rss": False},
    {"name": "ConferenceBoard_Consumer_Confidence", "url": "https://www.conference-board.org/topics/consumer-confidence", "category": SourceCategory.MACRO_CALENDAR, "description": "Conference Board Consumer Confidence Index reports", "is_rss": False},
    {"name": "Investing_econ", "url": "https://www.investing.com/economic-calendar/", "category": SourceCategory.MACRO_CALENDAR, "description": "Consensus vs actual economic indicator calendar", "is_rss": False},
    {"name": "ForexFactory", "url": "https://www.forexfactory.com/calendar.php", "category": SourceCategory.MACRO_CALENDAR, "description": "High-impact global macroeconomic calendar prints", "is_rss": False},

    # --- Category 2: Central Banking & Liquidity Plumbing ---
    {"name": "Fed_H4.1", "url": "https://www.federalreserve.gov/releases/h41/", "category": SourceCategory.CENTRAL_BANKING, "description": "Federal Reserve Balance Sheet (WALCL, Total Assets, Reserves)", "is_rss": False},
    {"name": "Fed_events", "url": "https://www.federalreserve.gov/newsevents.htm", "category": SourceCategory.CENTRAL_BANKING, "description": "Federal Reserve official public speeches and calendar", "is_rss": False},
    {"name": "Fed_Board_Press_Releases", "url": "https://www.federalreserve.gov/newsevents/pressreleases.htm", "category": SourceCategory.CENTRAL_BANKING, "description": "Federal Reserve Board emergency policy and regulatory press releases", "is_rss": False},
    {"name": "KC_Fed_JacksonHole", "url": "https://www.kansascityfed.org/research/jackson-hole/", "category": SourceCategory.CENTRAL_BANKING, "description": "Kansas City Fed Jackson Hole Economic Symposium schedules", "is_rss": False},
    {"name": "KC_Fed_research", "url": "https://www.kansascityfed.org/", "category": SourceCategory.CENTRAL_BANKING, "description": "Kansas City Fed regional manufacturing and policy research", "is_rss": False},
    {"name": "NYFed_ops", "url": "https://www.newyorkfed.org/markets/operations", "category": SourceCategory.CENTRAL_BANKING, "description": "NY Fed Open Market Operations and primary dealer absorption", "is_rss": False},
    {"name": "NYFed_Reverse_Repo_Operations", "url": "https://www.newyorkfed.org/markets/desk-operations/reverse-repo", "category": SourceCategory.CENTRAL_BANKING, "description": "Overnight Reverse Repo (ON RRP) facility usage and counterparty count", "is_rss": False},
    {"name": "ECB_events", "url": "https://www.ecb.europa.eu/press/key/date/html/index.en.html", "category": SourceCategory.CENTRAL_BANKING, "description": "European Central Bank monetary policy decisions and press conferences", "is_rss": False},
    {"name": "BOE_news", "url": "https://www.bankofengland.co.uk/news", "category": SourceCategory.CENTRAL_BANKING, "description": "Bank of England MPC rate decisions and monetary policy reports", "is_rss": False},
    {"name": "BOJ_announcements", "url": "https://www.boj.or.jp/en/announcements/", "category": SourceCategory.CENTRAL_BANKING, "description": "Bank of Japan policy announcements and yield curve control statements", "is_rss": False},
    {"name": "SNB_news", "url": "https://www.snb.ch/en/mmr/reference", "category": SourceCategory.CENTRAL_BANKING, "description": "Swiss National Bank monetary policy assessments", "is_rss": False},
    {"name": "RBA_media", "url": "https://www.rba.gov.au/media-releases/", "category": SourceCategory.CENTRAL_BANKING, "description": "Reserve Bank of Australia interest rate decision releases", "is_rss": False},
    {"name": "BOC_news", "url": "https://www.bankofcanada.ca/news/", "category": SourceCategory.CENTRAL_BANKING, "description": "Bank of Canada policy decisions and monetary policy reports", "is_rss": False},
    {"name": "PBoC_news", "url": "http://www.pbc.gov.cn/english/130721/index.html", "category": SourceCategory.CENTRAL_BANKING, "description": "People's Bank of China monetary policy and liquidity announcements", "is_rss": False},

    # --- Category 3: Sovereign Debt, Auctions & Yields ---
    {"name": "US_Treasury_auctions", "url": "https://home.treasury.gov/policy-issues/financing-the-government/auctions", "category": SourceCategory.TREASURY_AND_YIELDS, "description": "U.S. Treasury auction announcements and offering sizes", "is_rss": False},
    {"name": "Treasury_Real_Yield_Curve", "url": "https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics", "category": SourceCategory.TREASURY_AND_YIELDS, "description": "U.S. Treasury real yield curve (TIPS) and daily interest rates", "is_rss": False},
    {"name": "TreasuryDirect_auctions", "url": "https://www.treasurydirect.gov/instit/annceresult/annceresult.htm", "category": SourceCategory.TREASURY_AND_YIELDS, "description": "TreasuryDirect auction announcement results and settlement schedules", "is_rss": False},

    # --- Category 4: Corporate Earnings & SEC Filings ---
    {"name": "Nasdaq_earnings", "url": "https://www.nasdaq.com/market-activity/earnings", "category": SourceCategory.CORPORATE_AND_EARNINGS, "description": "Nasdaq composite corporate earnings release calendar", "is_rss": False},
    {"name": "Yahoo_earnings", "url": "https://finance.yahoo.com/calendar/earnings", "category": SourceCategory.CORPORATE_AND_EARNINGS, "description": "Yahoo Finance corporate earnings calendar and consensus EPS", "is_rss": False},
    {"name": "SEC_EDGAR_search", "url": "https://www.sec.gov/edgar/search/", "category": SourceCategory.CORPORATE_AND_EARNINGS, "description": "SEC EDGAR company search (10-K, 10-Q, 8-K Item 1.05)", "is_rss": False},
    {"name": "Apple_IR_Events", "url": "https://investor.apple.com/investor-relations/default.aspx", "category": SourceCategory.CORPORATE_AND_EARNINGS, "description": "Apple Inc. (AAPL) Investor Relations and earnings webcasts", "is_rss": False},
    {"name": "Microsoft_IR_Events", "url": "https://www.microsoft.com/en-us/investor", "category": SourceCategory.CORPORATE_AND_EARNINGS, "description": "Microsoft Corporation (MSFT) Investor Relations and events", "is_rss": False},
    {"name": "Nvidia_IR_Events", "url": "https://investor.nvidia.com/", "category": SourceCategory.CORPORATE_AND_EARNINGS, "description": "NVIDIA Corporation (NVDA) Investor Relations announcements", "is_rss": False},

    # --- Category 5: Derivatives, OpEx & Microstructure ---
    {"name": "CBOE_calendar", "url": "https://www.cboe.com/us/options/", "category": SourceCategory.DERIVATIVES_AND_OPEX, "description": "Cboe Options Exchange trading schedules and volatility indices", "is_rss": False},
    {"name": "Cboe_Options_Schedule", "url": "https://www.cboe.com/en/about/hours/us-options/", "category": SourceCategory.DERIVATIVES_AND_OPEX, "description": "Cboe holiday and operational expiration hours", "is_rss": False},
    {"name": "OCC_Expiration_Calendar", "url": "https://www.optionseducation.org/referencelibrary/expiration-calendar", "category": SourceCategory.DERIVATIVES_AND_OPEX, "description": "Options Clearing Corporation (OCC) Monthly and Quarterly OpEx calendar", "is_rss": False},

    # --- Category 6: Sector Catalysts & Commodity Plumbing ---
    {"name": "OPEC", "url": "https://www.opec.org/opec_web/en/", "category": SourceCategory.SECTOR_AND_COMMODITY, "description": "OPEC+ JMMC meetings, press releases, and production quota reviews", "is_rss": False},
    {"name": "ISM_releases", "url": "https://www.ismworld.org/supply-management-news-and-reports/", "category": SourceCategory.SECTOR_AND_COMMODITY, "description": "Institute for Supply Management Manufacturing and Services PMI reports", "is_rss": False},
    {"name": "SEMI_Market_Data_Billings", "url": "https://www.semi.org/en/news-resources/market-data/billings-report", "category": SourceCategory.SECTOR_AND_COMMODITY, "description": "SEMI Global Semiconductor Equipment Billings reports", "is_rss": False},
    {"name": "SEMI_events", "url": "https://www.semi.org/en/events", "category": SourceCategory.SECTOR_AND_COMMODITY, "description": "Semiconductor industry global executive conferences", "is_rss": False},

    # --- Category 7: Geopolitics, Sovereign Ratings & Press ---
    {"name": "FDIC_Press_Releases", "url": "https://www.fdic.gov/news/press-releases", "category": SourceCategory.GEOPOLITICS_AND_NEWS, "description": "FDIC bank closure, receivership, and regulatory announcements (Unscheduled Shock Detection)", "is_rss": True},
    {"name": "Reuters_RSS_index", "url": "https://www.reuters.com/tools/rss", "category": SourceCategory.GEOPOLITICS_AND_NEWS, "description": "Reuters breaking business, macro, and international wire feeds", "is_rss": True},
    {"name": "FT_RSS_index", "url": "https://www.ft.com/rss", "category": SourceCategory.GEOPOLITICS_AND_NEWS, "description": "Financial Times global macro, central banking, and capital markets RSS", "is_rss": True},
    {"name": "S&P_press", "url": "https://www.spglobal.com/ratings/en/sector/sovereign-ratings", "category": SourceCategory.GEOPOLITICS_AND_NEWS, "description": "S&P Global Sovereign Credit Rating actions and credit-watch placements", "is_rss": False},
    {"name": "Moody_press", "url": "https://www.moodys.com/researchandratings", "category": SourceCategory.GEOPOLITICS_AND_NEWS, "description": "Moody's sovereign and banking credit research announcements", "is_rss": False},
    {"name": "Fitch_press", "url": "https://www.fitchratings.com/site/home", "category": SourceCategory.GEOPOLITICS_AND_NEWS, "description": "Fitch Ratings sovereign downgrade and debt rating updates", "is_rss": False},
    {"name": "ISW_Newsroom", "url": "https://understandingwar.org/newsroom", "category": SourceCategory.GEOPOLITICS_AND_NEWS, "description": "Institute for the Study of War kinetic conflict and maritime chokepoint analysis", "is_rss": False},
    {"name": "CSIS_Press_Releases", "url": "https://www.csis.org/about/media/press-releases", "category": SourceCategory.GEOPOLITICS_AND_NEWS, "description": "Center for Strategic and International Studies trade, sanctions, and defense analysis", "is_rss": False},
]


# Function to get all registered SourceEndpoint models
def get_all_registered_sources() -> List[SourceEndpoint]:
    """
    Returns the complete list of all 47 validated SourceEndpoint models.
    """
    # Instantiate Pydantic models from raw dictionary definitions
    return [SourceEndpoint(**item) for item in RAW_47_SOURCES]


# Function to query sources by specific institutional category
def get_endpoints_by_category(category: SourceCategory) -> List[SourceEndpoint]:
    """
    Filters registered endpoints matching a specific SourceCategory.
    """
    all_sources = get_all_registered_sources()
    # Filter sources by matching category
    return [s for s in all_sources if s.category == category]
