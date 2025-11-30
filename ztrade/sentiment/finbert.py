"""FinBERT sentiment analyzer for financial text.

This module provides a wrapper around the ProsusAI/finbert model for
financial sentiment analysis. FinBERT is a BERT-based model fine-tuned
on financial text, providing better accuracy than VADER for financial content.

References:
- Model: https://huggingface.co/ProsusAI/finbert
- Paper: https://arxiv.org/abs/1908.10063
"""

from typing import Dict, Any, List, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from ztrade.core.logger import get_logger

logger = get_logger(__name__)


class FinBERTAnalyzer:
    """
    FinBERT sentiment analyzer for financial text.

    Uses the ProsusAI/finbert model to analyze sentiment in financial news,
    social media posts, and SEC filings. Returns scores compatible with
    VADER-style output for easy drop-in replacement.
    """

    # Model checkpoint
    MODEL_NAME = "ProsusAI/finbert"

    # Labels from FinBERT model
    LABELS = ["positive", "negative", "neutral"]

    # Maximum sequence length (FinBERT is based on BERT)
    MAX_LENGTH = 512

    def __init__(self, device: Optional[str] = None):
        """
        Initialize FinBERT analyzer.

        Args:
            device: Device to run model on ('cpu', 'cuda', 'mps', or None for auto)
        """
        self.device = self._get_device(device)
        self.tokenizer = None
        self.model = None
        self._load_model()

    def _get_device(self, device: Optional[str] = None) -> str:
        """
        Determine device to use for inference.

        Args:
            device: Requested device or None for auto-detection

        Returns:
            Device string ('cpu', 'cuda', or 'mps')
        """
        if device:
            return device

        # Auto-detect best available device
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _load_model(self):
        """Load FinBERT model and tokenizer."""
        try:
            logger.info(f"Loading FinBERT model ({self.MODEL_NAME}) on {self.device}...")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)

            # Load model
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.MODEL_NAME
            )

            # Move model to device
            self.model.to(self.device)

            # Set to evaluation mode
            self.model.eval()

            logger.info(f"FinBERT model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {e}")
            raise

    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of financial text.

        Args:
            text: Input text to analyze

        Returns:
            Dict containing:
            - compound: Overall sentiment score (-1 to 1)
            - pos: Positive probability (0 to 1)
            - neg: Negative probability (0 to 1)
            - neu: Neutral probability (0 to 1)
        """
        if not text or not text.strip():
            return {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}

        try:
            # Tokenize input
            # Truncate to MAX_LENGTH to avoid errors
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=self.MAX_LENGTH,
                padding=True
            )

            # Move inputs to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Run inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits

            # Get probabilities using softmax
            probs = torch.nn.functional.softmax(logits, dim=-1)
            probs = probs.cpu().numpy()[0]

            # Extract probabilities (model outputs: positive, negative, neutral)
            pos_prob = float(probs[0])
            neg_prob = float(probs[1])
            neu_prob = float(probs[2])

            # Calculate compound score (-1 to 1)
            # Similar to VADER: positive minus negative
            compound = pos_prob - neg_prob

            return {
                "compound": round(compound, 4),
                "pos": round(pos_prob, 4),
                "neg": round(neg_prob, 4),
                "neu": round(neu_prob, 4)
            }

        except Exception as e:
            logger.error(f"Error analyzing text with FinBERT: {e}")
            # Return neutral on error
            return {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}

    def analyze_batch(self, texts: List[str], batch_size: int = 8) -> List[Dict[str, float]]:
        """
        Analyze sentiment for multiple texts in batches.

        More efficient than calling analyze() multiple times for large datasets.

        Args:
            texts: List of texts to analyze
            batch_size: Number of texts to process per batch

        Returns:
            List of sentiment dicts (same format as analyze())
        """
        results = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Filter out empty texts
            valid_indices = [j for j, t in enumerate(batch) if t and t.strip()]
            valid_texts = [batch[j] for j in valid_indices]

            if not valid_texts:
                # All texts in batch are empty
                results.extend([
                    {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}
                    for _ in batch
                ])
                continue

            try:
                # Tokenize batch
                inputs = self.tokenizer(
                    valid_texts,
                    return_tensors="pt",
                    truncation=True,
                    max_length=self.MAX_LENGTH,
                    padding=True
                )

                # Move to device
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Run inference
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits = outputs.logits

                # Get probabilities
                probs = torch.nn.functional.softmax(logits, dim=-1)
                probs = probs.cpu().numpy()

                # Process each result
                batch_results = []
                for prob in probs:
                    pos_prob = float(prob[0])
                    neg_prob = float(prob[1])
                    neu_prob = float(prob[2])
                    compound = pos_prob - neg_prob

                    batch_results.append({
                        "compound": round(compound, 4),
                        "pos": round(pos_prob, 4),
                        "neg": round(neg_prob, 4),
                        "neu": round(neu_prob, 4)
                    })

                # Merge results back (handling empty texts)
                result_idx = 0
                for j in range(len(batch)):
                    if j in valid_indices:
                        results.append(batch_results[result_idx])
                        result_idx += 1
                    else:
                        results.append({"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0})

            except Exception as e:
                logger.error(f"Error in batch analysis: {e}")
                # Return neutral for failed batch
                results.extend([
                    {"compound": 0.0, "pos": 0.0, "neg": 0.0, "neu": 1.0}
                    for _ in batch
                ])

        return results

    def polarity_scores(self, text: str) -> Dict[str, float]:
        """
        VADER-compatible method name for drop-in replacement.

        Args:
            text: Input text

        Returns:
            Sentiment scores (same format as analyze())
        """
        return self.analyze(text)


# Global singleton instance
_finbert_analyzer = None


def get_finbert_analyzer(device: Optional[str] = None) -> FinBERTAnalyzer:
    """
    Get or create global FinBERT analyzer instance.

    Using a singleton pattern to avoid loading the model multiple times.

    Args:
        device: Device to use (only used on first initialization)

    Returns:
        FinBERTAnalyzer instance
    """
    global _finbert_analyzer

    if _finbert_analyzer is None:
        _finbert_analyzer = FinBERTAnalyzer(device=device)

    return _finbert_analyzer


def compare_with_vader(text: str) -> Dict[str, Any]:
    """
    Compare FinBERT and VADER sentiment for analysis.

    Useful for debugging and understanding differences between models.

    Args:
        text: Text to analyze

    Returns:
        Dict with both FinBERT and VADER results
    """
    results = {
        "text": text[:100] + "..." if len(text) > 100 else text,
        "finbert": None,
        "vader": None,
        "agreement": False
    }

    # Get FinBERT sentiment
    try:
        finbert = get_finbert_analyzer()
        results["finbert"] = finbert.analyze(text)
    except Exception as e:
        logger.error(f"FinBERT analysis failed: {e}")

    # Get VADER sentiment
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        vader = SentimentIntensityAnalyzer()
        results["vader"] = vader.polarity_scores(text)
    except Exception as e:
        logger.error(f"VADER analysis failed: {e}")

    # Check agreement
    if results["finbert"] and results["vader"]:
        finbert_sentiment = "positive" if results["finbert"]["compound"] >= 0.05 else \
                           "negative" if results["finbert"]["compound"] <= -0.05 else "neutral"
        vader_sentiment = "positive" if results["vader"]["compound"] >= 0.05 else \
                         "negative" if results["vader"]["compound"] <= -0.05 else "neutral"

        results["agreement"] = finbert_sentiment == vader_sentiment
        results["finbert_label"] = finbert_sentiment
        results["vader_label"] = vader_sentiment

    return results
