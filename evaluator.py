import numpy as np
import pandas as pd
import nltk
import json
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from bert_score import score as bert_score


# ===============================================================
# Text Evaluator
# ===============================================================
class ChatbotEvaluator:
    """Evaluator for text-based chatbot responses (semantic and linguistic quality)."""
    def __init__(self):
        self.rouge = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'], use_stemmer=True
        )
        self.smooth_fn = SmoothingFunction().method1

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
            bert_norm = (bert_f1 - 0.8) / (1.0 - 0.8)  # normalize 0.8–1.0

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
# Numeric Evaluator
# ===============================================================
class NumericEvaluator:
    """Evaluator for numeric outputs (e.g., calculations or factual values)."""
    def __init__(self, tolerance_ratio=0.01):
        self.tolerance_ratio = tolerance_ratio

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
# Unified Evaluator (now supports mixed types)
# ===============================================================
class UnifiedEvaluator:
    """Evaluates each pair automatically as text or numeric."""

    def __init__(self, tolerance_ratio=0.01):
        self.text_eval = ChatbotEvaluator()
        self.numeric_eval = NumericEvaluator(tolerance_ratio=tolerance_ratio)

    def evaluate_row(self, ref, cand):
        if self._is_number(ref) and self._is_number(cand):
            result = self.numeric_eval.evaluate([ref], [cand])
            return {'type': 'numeric', **result['per_sample'][0]}
        else:
            result = self.text_eval.evaluate_combined([ref], [cand])
            s = result['per_sample'][0]
            return {'type': 'text', **s}

    @staticmethod
    def _is_number(x):
        try:
            float(x)
            return True
        except ValueError:
            return False


# ===============================================================
# Example usage — mixed evaluation
# ===============================================================
if __name__ == "__main__":
    # Load your CSV
    df = pd.read_csv("qa_pair_model_test_results_v5.1.csv", encoding="latin-1")

    required_cols = {"template_ans", "model_ans", "difficulty"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {required_cols}")

    evaluator = UnifiedEvaluator(tolerance_ratio=0.02)

    print("=== Evaluating responses row by row ===")
    all_results = []
    for _, row in df.iterrows():
        res = evaluator.evaluate_row(row["template_ans"], row["model_ans"])
        res["difficulty"] = row["difficulty"]
        all_results.append(res)

    per_sample_df = pd.DataFrame(all_results)

    # --- Aggregate scores by difficulty (text-only metrics) ---
    text_metrics = ['composite_score', 'bleu', 'rouge1', 'rouge2', 'rougeL',
                    'precision', 'recall', 'f1']
    numeric_metrics = ['abs_error', 'rel_error_%', 'is_correct']

    # Aggregation handling (only apply relevant metrics per type)
    agg_by_difficulty = (
        per_sample_df.groupby("difficulty")
        .apply(lambda g: g[text_metrics + numeric_metrics].mean(numeric_only=True))
        .reset_index()
    )

    # --- Save results ---
    per_sample_df.to_csv("evaluation_per_sample.csv", index=False)
    agg_by_difficulty.to_csv("evaluation_by_difficulty.csv", index=False)

    with open("evaluation_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print("✅ Evaluation completed. Results saved to:")
    print(" - evaluation_per_sample.csv")
    print(" - evaluation_by_difficulty.csv")
    print(" - evaluation_results.json")
