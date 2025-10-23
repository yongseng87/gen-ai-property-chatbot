
import numpy as np
import nltk
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from bert_score import score as bert_score

class ChatbotEvaluator:
    def __init__(self):
        # Initialize ROUGE scorer
        self.rouge = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'], use_stemmer=True
        )
        self.smooth_fn = SmoothingFunction().method1

    def evaluate_rouge(self, references, candidates):
        results = {'rouge1': [], 'rouge2': [], 'rougeL': []}
        for ref, cand in zip(references, candidates):
            scores = self.rouge.score(ref, cand)
            for key in results:
                results[key].append(scores[key].fmeasure)
        return {k: sum(v) / len(v) for k, v in results.items()}

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
        return sum(scores) / len(scores)

    def evaluate_bertscore(self, references, candidates, lang="en"):
        P, R, F1 = bert_score(candidates, references, lang=lang)
        return {
            'precision': float(P.mean()),
            'recall': float(R.mean()),
            'f1': float(F1.mean())
        }

    def evaluate_all(self, references, candidates):
        return {
            'rouge': self.evaluate_rouge(references, candidates),
            'bleu': self.evaluate_bleu(references, candidates),
            'bertscore': self.evaluate_bertscore(references, candidates),
        }
    def evaluate_combined(self, references, candidates, weights=(0.1, 0.4, 0.5)):

        all_scores = self.evaluate_all(references, candidates)

        bleu = all_scores['bleu']
        rouge_vals = all_scores['rouge']
        rouge_mean = np.mean(list(rouge_vals.values()))
        bert_f1 = all_scores['bertscore']['f1']

        # normalize roughly to 0–1 scale
        bleu_norm = bleu
        rouge_norm = rouge_mean
        bert_norm = (bert_f1 - 0.8) / (1.0 - 0.8)  # normalize around 0.8–1.0 typical range

        # weighted combination
        w_bleu, w_rouge, w_bert = weights
        composite = (
            w_bleu * bleu_norm +
            w_rouge * rouge_norm +
            w_bert * bert_norm
        )

        all_scores['composite_score'] = float(np.clip(composite, 0, 1))
        return all_scores


# Example usage:
if __name__ == "__main__":
    references = [
        "The capital of France is Paris.",
        "Water boils at 100 degrees Celsius."
    ]
    candidates = [
        "Paris is the capital city of France.",
        "Water reaches its boiling point at one hundred degrees Celsius."
    ]

    evaluator = ChatbotEvaluator()
    results = evaluator.evaluate_combined(references, candidates)
    print(results)