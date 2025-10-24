import numpy as np
import nltk
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from bert_score import score as bert_score


class ChatbotEvaluator:
    """Evaluator for text-based chatbot responses (semantic and linguistic quality)."""
    def __init__(self):
        self.rouge = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'], use_stemmer=True
        )
        self.smooth_fn = SmoothingFunction().method1

    # ---------------------------
    # ROUGE evaluation (per-sample)
    # ---------------------------
    def evaluate_rouge(self, references, candidates):
        results = {'rouge1': [], 'rouge2': [], 'rougeL': []}
        sample_scores = []
        for ref, cand in zip(references, candidates):
            scores = self.rouge.score(ref, cand)
            sample_scores.append({
                'rouge1': scores['rouge1'].fmeasure,
                'rouge2': scores['rouge2'].fmeasure,
                'rougeL': scores['rougeL'].fmeasure
            })
            for key in results:
                results[key].append(scores[key].fmeasure)

        avg_scores = {k: sum(v) / len(v) for k, v in results.items()}
        return avg_scores, sample_scores

    # ---------------------------
    # BLEU evaluation (per-sample)
    # ---------------------------
    def evaluate_bleu(self, references, candidates):
        scores = []
        for ref, cand in zip(references, candidates):
            ref_tokens = [ref.split()]
            cand_tokens = cand.split()
            bleu = sentence_bleu(
                ref_tokens,
                cand_tokens,
                smoothing_function=self.smooth_fn
            )
            scores.append(bleu)
        avg_bleu = sum(scores) / len(scores)
        return avg_bleu, scores

    # ---------------------------
    # BERTScore evaluation (per-sample)
    # ---------------------------
    def evaluate_bertscore(self, references, candidates, lang="en"):
        P, R, F1 = bert_score(candidates, references, lang=lang)
        sample_scores = [{'precision': float(p), 'recall': float(r), 'f1': float(f)}
                         for p, r, f in zip(P, R, F1)]
        avg_scores = {
            'precision': float(P.mean()),
            'recall': float(R.mean()),
            'f1': float(F1.mean())
        }
        return avg_scores, sample_scores

    # ---------------------------
    # Combined evaluation (per-sample + overall)
    # ---------------------------
    def evaluate_combined(self, references, candidates, weights=(0.1, 0.4, 0.5)):
        rouge_avg, rouge_samples = self.evaluate_rouge(references, candidates)
        bleu_avg, bleu_samples = self.evaluate_bleu(references, candidates)
        bert_avg, bert_samples = self.evaluate_bertscore(references, candidates)

        w_bleu, w_rouge, w_bert = weights
        per_sample_results = []

        for i in range(len(references)):
            rouge_mean = np.mean(list(rouge_samples[i].values()))
            bleu_norm = bleu_samples[i]
            bert_f1 = bert_samples[i]['f1']
            bert_norm = (bert_f1 - 0.8) / (1.0 - 0.8)  # normalize roughly 0.8–1.0

            composite = (
                w_bleu * bleu_norm +
                w_rouge * rouge_mean +
                w_bert * bert_norm
            )

            per_sample_results.append({
                'reference': references[i],
                'candidate': candidates[i],
                'bleu': bleu_samples[i],
                **rouge_samples[i],
                **bert_samples[i],
                'composite_score': float(np.clip(composite, 0, 1))
            })

        overall_composite = np.mean([s['composite_score'] for s in per_sample_results])
        overall = {
            'bleu': bleu_avg,
            'rouge': rouge_avg,
            'bertscore': bert_avg,
            'composite_score': overall_composite
        }

        return {'overall': overall, 'per_sample': per_sample_results}


# ===============================================================
# Numeric Evaluator for computation-based chatbot responses
# ===============================================================
class NumericEvaluator:
    """Evaluator for numeric outputs (e.g., calculations or factual values)."""
    def __init__(self, tolerance_ratio=0.01):
        self.tolerance_ratio = tolerance_ratio  # default 1% tolerance

    def evaluate(self, references, candidates):
        references = np.array(references, dtype=float)
        candidates = np.array(candidates, dtype=float)

        abs_diff = np.abs(candidates - references)
        rel_diff = abs_diff / np.maximum(np.abs(references), 1e-8)
        tolerance = self.tolerance_ratio * np.abs(references)
        correct = abs_diff <= tolerance

        accuracy = np.mean(correct)
        mae = np.mean(abs_diff)
        mape = np.mean(rel_diff) * 100

        per_sample = []
        for i in range(len(references)):
            per_sample.append({
                'reference': references[i],
                'candidate': candidates[i],
                'abs_error': abs_diff[i],
                'rel_error_%': rel_diff[i] * 100,
                'is_correct': bool(correct[i])
            })

        results = {
            'accuracy_within_tolerance': accuracy,
            'mean_absolute_error': mae,
            'mean_absolute_percentage_error': mape
        }
        return {'overall': results, 'per_sample': per_sample}


# ===============================================================
# Unified Evaluator
# ===============================================================
class UnifiedEvaluator:
    """
    Automatically decides whether to run text or numeric evaluation.
    - For strings: uses ChatbotEvaluator (BLEU, ROUGE, BERTScore)
    - For numbers: uses NumericEvaluator (accuracy, MAE, MAPE)
    """

    def __init__(self, tolerance_ratio=0.01):
        self.text_eval = ChatbotEvaluator()
        self.numeric_eval = NumericEvaluator(tolerance_ratio=tolerance_ratio)

    def evaluate(self, references, candidates):
        # Detect if this is numeric or textual
        is_numeric = all(self._is_number(x) and self._is_number(y)
                         for x, y in zip(references, candidates))

        if is_numeric:
            return {'type': 'numeric', **self.numeric_eval.evaluate(references, candidates)}
        else:
            return {'type': 'text', **self.text_eval.evaluate_combined(references, candidates)}

    @staticmethod
    def _is_number(x):
        try:
            float(x)
            return True
        except ValueError:
            return False


# ===============================================================
# Example usage
# ===============================================================
if __name__ == "__main__":
    # --- Example 1: Text-based ---
    text_refs = [
        "The capital of France is Paris.",
        "Water boils at 100 degrees Celsius."
    ]
    text_cands = [
        "Paris is the capital city of France.",
        "Water reaches boiling point at one hundred degrees Celsius."
    ]

    # --- Example 2: Numeric-based ---
    numeric_refs = [2500, 3200, 4100]
    numeric_cands = [2490, 3198, 4300]

    evaluator = UnifiedEvaluator(tolerance_ratio=0.02)

    print("=== Text Evaluation ===")
    print(evaluator.evaluate(text_refs, text_cands))

    print("\n=== Numeric Evaluation ===")
    print(evaluator.evaluate(numeric_refs, numeric_cands))
