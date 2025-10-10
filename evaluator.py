
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