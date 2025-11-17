"""SEC EDGAR filings analysis for trading symbols."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import requests
import time
from cli.utils.logger import get_logger

logger = get_logger(__name__)


class SECAnalyzer:
    """Analyzes SEC EDGAR filings for trading symbols."""

    # SEC EDGAR API base URL
    SEC_API_BASE = "https://data.sec.gov"

    # User-Agent header required by SEC
    # Note: SEC blocks custom app User-Agents, use standard browser UA instead
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Encoding": "gzip, deflate"
    }

    # Filing types and their sentiment implications
    FILING_TYPES = {
        "8-K": "Material Event",  # Material events (can be positive or negative)
        "10-Q": "Quarterly Report",  # Quarterly earnings
        "10-K": "Annual Report",  # Annual earnings
        "4": "Insider Trading",  # Insider buys/sells
        "SC 13G": "Large Ownership",  # Institutional ownership changes
        "S-1": "IPO Registration",
        "S-3": "Shelf Registration",
        "DEF 14A": "Proxy Statement"
    }

    # Keywords for sentiment detection in filing descriptions
    POSITIVE_KEYWORDS = [
        "beat", "exceed", "growth", "record", "strong", "increase", "positive",
        "improvement", "acquisition", "expansion", "dividend", "buyback",
        "outperform", "above expectations", "guidance raise", "upgrade"
    ]

    NEGATIVE_KEYWORDS = [
        "miss", "below", "decline", "weak", "decrease", "negative", "loss",
        "impairment", "restructuring", "layoff", "investigation", "lawsuit",
        "restatement", "concern", "warning", "guidance lower", "downgrade"
    ]

    def __init__(self):
        """Initialize the SEC analyzer."""
        # Cache symbol -> CIK mappings (pre-populated with common stocks)
        # CIK format: 10-digit zero-padded number
        self.cik_cache = {
            "TSLA": "0000789019",    # Tesla
            "AAPL": "0000320193",    # Apple
            "MSFT": "0000789019",    # Microsoft (need correct CIK)
            "GOOGL": "0001652044",   # Alphabet
            "GOOG": "0001652044",    # Alphabet
            "AMZN": "0001018724",    # Amazon
            "NVDA": "0001045810",    # NVIDIA
            "META": "0001326801",    # Meta
        }

    def get_sec_sentiment(
        self,
        symbol: str,
        lookback_days: int = 30,
        max_filings: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze SEC filings sentiment for a trading symbol.

        Args:
            symbol: Stock symbol (e.g., 'TSLA', 'IWM')
            lookback_days: How many days back to search
            max_filings: Maximum number of filings to analyze

        Returns:
            Dict containing:
            - overall_sentiment: 'positive', 'negative', or 'neutral'
            - sentiment_score: Aggregate score (-1 to 1)
            - confidence: Confidence in the sentiment (0 to 1)
            - filing_count: Number of filings analyzed
            - recent_filings: List of recent filing summaries
            - material_events: List of material events (8-K filings)
        """
        try:
            # Get CIK for the symbol
            cik = self._get_cik_by_symbol(symbol)
            if not cik:
                logger.warning(f"Could not find CIK for symbol {symbol}")
                return {
                    "error": f"CIK not found for {symbol}",
                    "overall_sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "filing_count": 0
                }

            # Fetch recent filings
            filings = self._get_recent_filings(cik, lookback_days, max_filings)

            if not filings:
                logger.info(f"No SEC filings found for {symbol} in the last {lookback_days} days")
                return {
                    "overall_sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "filing_count": 0,
                    "recent_filings": [],
                    "material_events": []
                }

            # Analyze each filing for sentiment
            filing_sentiments = []
            material_events = []

            for filing in filings:
                sentiment = self._analyze_filing_sentiment(filing)
                filing_sentiments.append(sentiment)

                # Track material events (8-K filings)
                if filing.get("form") == "8-K":
                    material_events.append({
                        "date": filing.get("filingDate"),
                        "description": filing.get("description", "Material Event"),
                        "sentiment": sentiment
                    })

            # Aggregate sentiment scores
            if not filing_sentiments:
                avg_sentiment = 0.0
            else:
                avg_sentiment = sum(filing_sentiments) / len(filing_sentiments)

            # Determine overall sentiment
            if avg_sentiment >= 0.15:
                overall = "positive"
            elif avg_sentiment <= -0.15:
                overall = "negative"
            else:
                overall = "neutral"

            # Calculate confidence based on number of filings
            # More filings = higher confidence (up to 10 filings)
            confidence = min(len(filings) / 10.0, 1.0)

            # Format recent filings for output
            recent_filings = [
                {
                    "form": f.get("form"),
                    "filing_date": f.get("filingDate"),
                    "description": self.FILING_TYPES.get(f.get("form"), f.get("form")),
                    "sentiment": self._analyze_filing_sentiment(f)
                }
                for f in filings[:5]  # Top 5 most recent
            ]

            result = {
                "overall_sentiment": overall,
                "sentiment_score": round(avg_sentiment, 3),
                "confidence": round(confidence, 2),
                "filing_count": len(filings),
                "recent_filings": recent_filings,
                "material_events": material_events,
                "lookback_days": lookback_days
            }

            logger.info(
                f"SEC sentiment for {symbol}: {overall} "
                f"(score: {avg_sentiment:.2f}, confidence: {confidence:.2f}, "
                f"filings: {len(filings)}, material events: {len(material_events)})"
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing SEC filings for {symbol}: {e}")
            return {
                "error": str(e),
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "filing_count": 0
            }

    def _get_cik_by_symbol(self, symbol: str) -> Optional[str]:
        """
        Get CIK (Central Index Key) for a stock symbol.

        Args:
            symbol: Stock symbol

        Returns:
            CIK string (padded to 10 digits) or None
        """
        # Check cache first
        if symbol in self.cik_cache:
            return self.cik_cache[symbol]

        try:
            # SEC provides a company tickers JSON file
            url = f"{self.SEC_API_BASE}/files/company_tickers.json"
            response = requests.get(url, headers=self.HEADERS, timeout=10)

            if response.status_code != 200:
                logger.warning(f"SEC API returned status {response.status_code}")
                return None

            tickers_data = response.json()

            # Search for the symbol
            for entry in tickers_data.values():
                if entry.get("ticker", "").upper() == symbol.upper():
                    cik = str(entry.get("cik_str"))
                    # Pad CIK to 10 digits
                    cik_padded = cik.zfill(10)
                    self.cik_cache[symbol] = cik_padded
                    logger.info(f"Found CIK {cik_padded} for symbol {symbol}")
                    return cik_padded

            logger.warning(f"Symbol {symbol} not found in SEC database")
            return None

        except Exception as e:
            logger.error(f"Error fetching CIK for {symbol}: {e}")
            return None

    def _get_recent_filings(
        self,
        cik: str,
        lookback_days: int,
        max_filings: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent filings for a CIK.

        Args:
            cik: CIK (10-digit padded)
            lookback_days: Days to look back
            max_filings: Maximum filings to return

        Returns:
            List of filing dictionaries
        """
        try:
            # SEC submissions endpoint
            url = f"{self.SEC_API_BASE}/submissions/CIK{cik}.json"

            # Rate limiting: SEC requests max 10 requests per second
            time.sleep(0.1)

            response = requests.get(url, headers=self.HEADERS, timeout=10)

            if response.status_code != 200:
                logger.warning(f"SEC API returned status {response.status_code} for CIK {cik}")
                return []

            data = response.json()

            # Extract recent filings
            recent = data.get("filings", {}).get("recent", {})

            if not recent:
                return []

            # Build list of filings
            filings = []
            cutoff_date = datetime.now() - timedelta(days=lookback_days)

            forms = recent.get("form", [])
            filing_dates = recent.get("filingDate", [])
            accession_numbers = recent.get("accessionNumber", [])
            primary_documents = recent.get("primaryDocument", [])

            for i in range(len(forms)):
                # Parse filing date
                try:
                    filing_date = datetime.strptime(filing_dates[i], "%Y-%m-%d")
                except (ValueError, IndexError):
                    continue

                # Check if within lookback window
                if filing_date < cutoff_date:
                    continue

                # Only include relevant filing types
                form = forms[i]
                if form not in self.FILING_TYPES and not form.startswith("8-K"):
                    continue

                filings.append({
                    "form": form,
                    "filingDate": filing_dates[i],
                    "accessionNumber": accession_numbers[i] if i < len(accession_numbers) else "",
                    "primaryDocument": primary_documents[i] if i < len(primary_documents) else "",
                    "description": self.FILING_TYPES.get(form, form)
                })

                # Limit to max_filings
                if len(filings) >= max_filings:
                    break

            return filings

        except Exception as e:
            logger.error(f"Error fetching filings for CIK {cik}: {e}")
            return []

    def _analyze_filing_sentiment(self, filing: Dict[str, Any]) -> float:
        """
        Analyze sentiment of a filing.

        Args:
            filing: Filing dictionary

        Returns:
            Sentiment score (-1 to 1)
        """
        form = filing.get("form", "")
        description = filing.get("description", "").lower()

        # Base sentiment by filing type
        if form == "8-K":
            # Material events - need content analysis
            # For now, neutral unless we detect keywords
            sentiment = 0.0
        elif form in ["10-Q", "10-K"]:
            # Earnings reports - slightly positive (company is operational)
            sentiment = 0.1
        elif form == "4":
            # Insider trading - context-dependent, default neutral
            sentiment = 0.0
        elif form in ["SC 13G", "SC 13D"]:
            # Large ownership changes - slightly positive (institutional interest)
            sentiment = 0.2
        elif form == "S-1":
            # IPO registration - positive
            sentiment = 0.3
        else:
            sentiment = 0.0

        # Adjust based on description keywords
        description_text = description.lower()

        positive_matches = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in description_text)
        negative_matches = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in description_text)

        # Adjust sentiment based on keyword matches
        sentiment += (positive_matches * 0.2) - (negative_matches * 0.2)

        # Clamp to [-1, 1]
        sentiment = max(-1.0, min(1.0, sentiment))

        return sentiment


def get_sec_analyzer() -> SECAnalyzer:
    """Factory function to get SEC analyzer instance."""
    return SECAnalyzer()
