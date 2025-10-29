import numpy as np
import pandas as pd
import nltk
import json
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
    Automatically decides whether to run text or numeric evaluation on a per-sample basis.
    - For strings that parse as numbers: uses NumericEvaluator (accuracy, MAE, MAPE)
    - Otherwise: uses ChatbotEvaluator (BLEU, ROUGE, BERTScore)
    """

    def __init__(self, tolerance_ratio=0.01):
        self.text_eval = ChatbotEvaluator()
        self.numeric_eval = NumericEvaluator(tolerance_ratio=tolerance_ratio)

    def evaluate(self, references, candidates):
        # ensure lists
        refs = list(references)
        cands = list(candidates)
        if len(refs) != len(cands):
            raise ValueError("references and candidates must have the same length")

        per_sample_results = []
        # Collect indices for numeric and text to evaluate in batches where convenient
        numeric_indices = []
        text_indices = []
        for i, (r, c) in enumerate(zip(refs, cands)):
            if self._is_number(r) and self._is_number(c):
                numeric_indices.append(i)
            else:
                text_indices.append(i)

        # Evaluate numeric samples (if any) in a batch using NumericEvaluator
        if numeric_indices:
            numeric_refs = [self._to_number(refs[i]) for i in numeric_indices]
            numeric_cands = [self._to_number(cands[i]) for i in numeric_indices]
            numeric_results = self.numeric_eval.evaluate(numeric_refs, numeric_cands)
            # numeric_results['per_sample'] is a list aligned to numeric_indices order
            for idx, sample in zip(numeric_indices, numeric_results['per_sample']):
                out = {
                    'index': idx,
                    'evaluator': 'numeric',
                    **sample
                }
                per_sample_results.append(out)

        # Evaluate text samples (if any) using ChatbotEvaluator.evaluate_combined
        if text_indices:
            text_refs = [refs[i] for i in text_indices]
            text_cands = [cands[i] for i in text_indices]
            text_results = self.text_eval.evaluate_combined(text_refs, text_cands)
            # text_results['per_sample'] aligned to text_indices order
            for idx, sample in zip(text_indices, text_results['per_sample']):
                out = {
                    'index': idx,
                    'evaluator': 'text',
                    **sample
                }
                per_sample_results.append(out)

        # Sort per_sample_results by original index
        per_sample_results = sorted(per_sample_results, key=lambda x: x['index'])

        # Build overall summary
        overall = {}
        types_present = set(r['evaluator'] for r in per_sample_results)
        if types_present == {'numeric'}:
            overall_type = 'numeric'
            # We already computed numeric_results above if numeric_indices
            overall = numeric_results['overall']
        elif types_present == {'text'}:
            overall_type = 'text'
            overall = text_results['overall']
        else:
            overall_type = 'mixed'
            # Combine/aggregate overall metrics sensibly:
            # - For simplicity: compute numeric overall and text overall separately and present both
            overall = {}
            if numeric_indices:
                overall['numeric'] = numeric_results['overall']
            if text_indices:
                overall['text'] = text_results['overall']

        return {
            'type': overall_type,
            'overall': overall,
            'per_sample': per_sample_results
        }

    @staticmethod
    def _is_number(x):
        """
        Return True if x looks like a number. Accepts numeric types or strings with
        commas, currency symbols ($,€,£), percent signs, parentheses for negatives, etc.
        """
        if x is None:
            return False
        # If already numeric type
        if isinstance(x, (int, float, np.number)):
            return True
        if not isinstance(x, str):
            return False
        s = x.strip()
        if s == "":
            return False
        # handle parentheses negative like (1234)
        if s.startswith("(") and s.endswith(")"):
            s = "-" + s[1:-1]
        # remove common currency symbols and percent signs and whitespace
        for ch in ["$", "£", "€", ",", "%", " "]:
            s = s.replace(ch, "")
        # remove plus signs
        if s.startswith("+"):
            s = s[1:]
        # final check
        try:
            float(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def _to_number(x):
        """
        Convert an accepted numeric-like string to float. Assumes _is_number returned True.
        """
        if isinstance(x, (int, float, np.number)):
            return float(x)
        s = str(x).strip()
        if s.startswith("(") and s.endswith(")"):
            s = "-" + s[1:-1]
        for ch in ["$", "£", "€", ",", "%", " "]:
            s = s.replace(ch, "")
        if s == "":
            return 0.0
        try:
            return float(s)
        except ValueError:
            # fallback, though ideally should not happen if _is_number passed
            return float('nan')


# ===============================================================
# Example usage
# ===============================================================
if __name__ == "__main__":
    # --- Example 1: Text-based ---

    # Load the CSV file
    df = pd.read_csv("qa_pair_model_test_results_v3.csv", encoding="latin-1")

    # Ensure required columns exist
    required_cols = {"template_ans", "model_ans", "difficulty"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {required_cols}")

    # Extract the lists
    text_refs = df["template_ans"].tolist()
    text_cands = df["model_ans"].tolist()

    evaluator = UnifiedEvaluator(tolerance_ratio=0.02)

    print("=== Text Evaluation ===")
    print(evaluator.evaluate(text_refs, text_cands))

    #print("\n=== Numeric Evaluation ===")
    #print(evaluator.evaluate(numeric_refs, numeric_cands))

results = evaluator.evaluate(text_refs, text_cands)

# Convert the per-sample data to a DataFrame
per_sample_df = pd.DataFrame(results["per_sample"])

# Merge difficulty back into per-sample evaluation
per_sample_df["difficulty"] = df["difficulty"]

# --- Aggregate scores by difficulty ---
metrics = ['composite_score', 'bleu', 'rouge1', 'rouge2', 'rougeL', 'precision', 'recall', 'f1']

# --- Aggregate by difficulty and evaluator type ---
# --- Aggregate by difficulty and evaluator type ---
# Separate handling for numeric vs text

agg_text = (
    per_sample_df[per_sample_df["evaluator"] == "text"]
    .groupby("difficulty", dropna=False)
    .mean(numeric_only=True)
    .reset_index()
)
agg_text["evaluator"] = "text"

agg_numeric_summary = []
numeric_df = per_sample_df[per_sample_df["evaluator"] == "numeric"]

if not numeric_df.empty:
    grouped = numeric_df.groupby("difficulty", dropna=False)
    for diff, group in grouped:
        total = len(group)
        correct = int(group["is_correct"].sum())
        accuracy = correct / total if total > 0 else 0
        agg_numeric_summary.append({
            "difficulty": diff,
            "evaluator": "numeric",
            "num_questions": total,
            "num_correct": correct,
            "accuracy_within_tolerance": accuracy,
            "mean_absolute_error": group["abs_error"].mean(),
            "mean_absolute_percentage_error": group["rel_error_%"].mean()
        })

agg_numeric = pd.DataFrame(agg_numeric_summary)

# Combine both types for unified output
agg_by_difficulty_type = pd.concat([agg_text, agg_numeric], ignore_index=True)


total_composite_score = per_sample_df["composite_score"].mean()

# --- Save everything to JSON ---
per_sample_records = per_sample_df.to_dict(orient="records")
agg_records = agg_by_difficulty_type.to_dict(orient="records")

with open("evaluation_results.json", "w") as f:
    json.dump(results, f, indent=2)

with open("evaluation_per_sample.json", "w") as f:
    json.dump(per_sample_records, f, indent=2)

with open("evaluation_by_difficulty_and_type.json", "w") as f:
    json.dump(agg_records, f, indent=2)
