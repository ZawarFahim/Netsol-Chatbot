def run_evaluation(query: str, response: str, context: str = None) -> float:
    if not response or len(response.strip()) == 0:
        return 0.0
    
    score = 0.5
    query_words = set(w.strip("?,.:!\"'()[]") for w in query.lower().split() if len(w) > 2)
    resp_words = set(w.strip("?,.:!\"'()[]") for w in response.lower().split() if len(w) > 2)
    
    if query_words:
        overlap = len(query_words.intersection(resp_words))
        score += min(0.3, overlap * 0.05)
        
    if context:
        context_words = set(w.strip("?,.:!\"'()[]") for w in context.lower().split() if len(w) > 2)
        if context_words:
            ctx_overlap = len(context_words.intersection(resp_words))
            score += min(0.2, ctx_overlap * 0.02)
            
    return min(1.0, score)
