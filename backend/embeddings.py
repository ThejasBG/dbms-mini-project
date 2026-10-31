import hashlib, re
import numpy as np
_model = None
_attempted = False
DIM = 384

def embed(text):
    global _model, _attempted
    if not _attempted:
        _attempted = True
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            print("Embedding model unavailable; using hashed-token fallback.")
    if _model is not None:
        return _model.encode(text, normalize_embeddings=True).astype(np.float32).tolist()
    v = np.zeros(DIM, dtype=np.float32)
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        h = hashlib.blake2b(token.encode(), digest_size=8).digest()
        v[int.from_bytes(h[:4], "big") % DIM] += 1 if h[4] % 2 else -1
    n = np.linalg.norm(v)
    if n: v /= n
    return v.tolist()
