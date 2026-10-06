"""Execute all 6 notebooks using nbconvert programmatic API."""
import sys, os, subprocess, time

NOTEBOOKS = [
    'notebooks/01_classical_eda.ipynb',
    'notebooks/02_quantum_representation.ipynb',
    'notebooks/03_quantum_similarity.ipynb',
    'notebooks/04_comparative_analysis.ipynb',
    'notebooks/05_q_interestingness.ipynb',
    'notebooks/06_validation.ipynb',
]

results = {}
for nb_path in NOTEBOOKS:
    print(f"\n{'='*60}")
    print(f"EXECUTING: {nb_path}")
    print(f"{'='*60}")
    t0 = time.time()
    try:
        import nbformat
        from nbconvert.preprocessors import ExecutePreprocessor
        with open(nb_path, encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=3600, kernel_name='python3')
        ep.preprocess(nb, {'metadata': {'path': '.'}})
        with open(nb_path, 'w', encoding='utf-8') as f:
            nbformat.write(nb, f)
        elapsed = time.time() - t0
        results[nb_path] = ('SUCCESS', elapsed)
        print(f"SUCCESS: {nb_path} ({elapsed:.1f}s)")
    except Exception as e:
        elapsed = time.time() - t0
        results[nb_path] = ('FAILED', elapsed, str(e))
        print(f"FAILED: {nb_path} ({elapsed:.1f}s)")
        print(f"ERROR: {e}")

print("\n\n" + "="*60)
print("EXECUTION SUMMARY")
print("="*60)
for path, res in results.items():
    status = res[0]
    t = res[1]
    print(f"  {os.path.basename(path)}: {status} ({t:.1f}s)")
    if status == 'FAILED':
        print(f"    Error: {res[2][:200]}")
