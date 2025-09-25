# Station Search Algorithm: Mathematical Specification

This document provides a comprehensive mathematical explanation of how the station search algorithm works, including the scoring mechanisms, indexing strategies, and search flow.

## Table of Contents

1. [Mathematical Definitions](#mathematical-definitions)
2. [Data Model & Indexing](#data-model--indexing)
3. [Search Algorithm](#search-algorithm)
4. [Scoring Functions](#scoring-functions)
5. [Performance Analysis](#performance-analysis)
6. [Examples & Edge Cases](#examples--edge-cases)

## Mathematical Definitions

### Basic Notation

Let **S** = {s₁, s₂, ..., sₙ} be the set of all stations where n = |S|

Each station sᵢ ∈ S is defined as a tuple:
```
sᵢ = (title, codes, location, search_text)
```

Where:
- **title** ∈ Σ* : Station name (string over alphabet Σ)
- **codes** = {yandex_code, esr_code, ...} : Set of identification codes  
- **location** = (settlement, region, country) : Hierarchical location tuple
- **search_text** ∈ Σ* : Concatenated searchable text

### Query Processing

For a user query **q** ∈ Σ*, we define:
```
Q = normalize(q) = trim(lowercase(q))
```

The search process returns a ranked list:
```
R(Q) = [(s₁, r₁), (s₂, r₂), ..., (sₖ, rₖ)]
```

Where:
- sᵢ ∈ S are matching stations
- rᵢ ∈ ℝ⁺ are relevance scores
- r₁ ≥ r₂ ≥ ... ≥ rₖ (sorted by relevance)

## Data Model & Indexing

### Text Index Construction

Each station's search text is constructed as:
```
search_text(sᵢ) = title ⊕ settlement ⊕ region ⊕ country ⊕ direction
```

Where ⊕ is string concatenation with space separation.

### MongoDB Text Index

MongoDB creates an inverted index **I** where:
```
I: Σ* → P(S)
I(word) = {s ∈ S | word ∈ tokenize(search_text(s))}
```

The tokenization function splits text into words:
```
tokenize(text) = {w₁, w₂, ..., wₘ} where wᵢ ∈ Σ*
```

### Index Storage Complexity

**Space Complexity**: O(|V| × n̄)
- |V| = vocabulary size (unique words across all stations)
- n̄ = average number of stations per word

**Time Complexity** for index construction: O(n × m̄)
- n = number of stations
- m̄ = average words per station

## Search Algorithm

### Primary Search: MongoDB Text Search

Given query Q, the primary search algorithm:

1. **Tokenize Query**:
   ```
   tokens(Q) = {t₁, t₂, ..., tₖ}
   ```

2. **Compute Candidate Set**:
   ```
   C = ⋃ᵢ₌₁ᵏ I(tᵢ)
   ```

3. **Calculate Text Scores**:
   For each s ∈ C, MongoDB computes:
   ```
   score_text(s, Q) = Σᵢ₌₁ᵏ tf_idf(tᵢ, s)
   ```

   Where tf_idf is Term Frequency × Inverse Document Frequency:
   ```
   tf_idf(t, s) = tf(t, s) × log(n / df(t))
   ```
   
   - tf(t, s) = frequency of term t in station s
   - df(t) = number of stations containing term t
   - n = total number of stations

### Secondary Search: Fuzzy Matching

If |results| = 0 from primary search, activate fuzzy matching:

1. **Pattern Compilation**:
   ```
   P = compile_regex(escape(Q), IGNORECASE)
   ```

2. **Pattern Matching**:
   ```
   F = {s ∈ S | P.matches(title(s))}
   ```

3. **Fuzzy Score Assignment**:
   ```
   score_fuzzy(s, Q) = 0.5 ∀s ∈ F
   ```

### Combined Algorithm

```python
def search(Q: str, limit: int) -> List[Tuple[Station, float]]:
    results = []
    
    # Phase 1: MongoDB Text Search
    C = mongodb_text_search(Q)
    for s in C:
        score = mongodb_text_score(s, Q)
        results.append((s, score))
    
    # Phase 2: Fuzzy Fallback (if needed)
    if len(results) == 0:
        F = fuzzy_search(Q)
        for s in F:
            results.append((s, 0.5))
    
    # Phase 3: Sort and Limit
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]
```

## Scoring Functions

### MongoDB Text Score

MongoDB's text search score is computed as:
```
score_mongodb(s, Q) = Σₜ∈Q∩tokens(s) weight(t) × tf(t, s) × idf(t)
```

Where:
- **weight(t)**: Term weight (title terms weighted higher)
- **tf(t, s)**: Term frequency in station s
- **idf(t)**: Inverse document frequency

### Enhanced Relevance Scoring

We apply additional relevance boosts:

1. **Exact Title Match**:
   ```
   boost_exact(s, Q) = 3.0 if normalize(title(s)) = Q else 1.0
   ```

2. **Title Contains Query**:
   ```
   boost_title(s, Q) = 2.0 if Q ⊆ normalize(title(s)) else 1.0
   ```

3. **Final Score**:
   ```
   score_final(s, Q) = score_mongodb(s, Q) × max(boost_exact(s, Q), boost_title(s, Q))
   ```

### Score Distribution

The final scores follow this hierarchy:
- **3.0+**: Exact title matches
- **2.0-2.9**: Partial title matches with high text score
- **1.0-1.9**: Location/context matches
- **0.5**: Fuzzy matches

## Performance Analysis

### Time Complexity

1. **MongoDB Text Search**: O(k × log n + m)
   - k = query terms
   - m = result set size
   - Uses B-tree index for O(log n) term lookup

2. **Fuzzy Search**: O(n × |title_avg|)
   - Linear scan through all stations
   - Regex matching on titles

3. **Total Worst Case**: O(n × |title_avg|)
   - When text search returns no results

### Space Complexity

1. **Index Storage**: O(|V| × n̄)
   - Vocabulary size × average postings per term

2. **Query Processing**: O(limit)
   - Only stores top results

### Optimization Strategies

1. **Early Termination**:
   ```
   if len(results) ≥ limit and score < threshold:
       break
   ```

2. **Index Selectivity**:
   ```
   selectivity(t) = df(t) / n
   ```
   Process terms in order of increasing selectivity.

3. **Cache Frequent Queries**:
   ```
   cache_key = hash(normalize(query))
   ```

## Examples & Edge Cases

### Example 1: High-Precision Search

**Query**: "Domodedovo Airport"
**Processing**:
1. tokens = ["domodedovo", "airport"]
2. Both terms have high selectivity
3. Exact match in title → score = 3.0

**Results**:
```
[("Domodedovo Airport", 3.0), ("Vnukovo Airport", 1.2)]
```

### Example 2: Location-Based Search

**Query**: "moscow"
**Processing**:
1. tokens = ["moscow"]
2. Matches in title, settlement, region fields
3. Various boost levels applied

**Score Breakdown**:
- "Moscow Terminal" (title match) → 2.0
- "Domodedovo Airport" (settlement match) → 1.0
- Other Moscow stations → 1.0

### Example 3: Fuzzy Fallback

**Query**: "moskva" (Russian variant)
**Processing**:
1. Text search returns 0 results
2. Fuzzy search activated
3. No regex matches found
4. Return empty result set

### Edge Cases

1. **Empty Query**:
   ```
   if |Q| = 0: return []
   ```

2. **Very Short Query**:
   ```
   if |Q| < 2: return "Query too short"
   ```

3. **Special Characters**:
   ```
   Q = regex_escape(Q)  # Prevent injection
   ```

4. **Unicode Normalization**:
   ```
   Q = unicode_normalize(Q)  # Handle accents, etc.
   ```

## Mathematical Properties

### Monotonicity
For queries Q₁ ⊆ Q₂:
```
|results(Q₂)| ≤ |results(Q₁)|
```
(More specific queries return fewer results)

### Symmetry
The search is not symmetric:
```
search("Airport Moscow") ≠ search("Moscow Airport")
```
Due to term ordering in MongoDB text search.

### Idempotency
Multiple identical searches return identical results:
```
search(Q) = search(Q) ∀Q
```

### Completeness
Every station with non-empty title is findable:
```
∀s ∈ S where title(s) ≠ ∅, ∃Q such that s ∈ results(Q)
```

## Conclusion

The search algorithm combines:
1. **High-precision text search** via MongoDB indexing
2. **Graceful degradation** through fuzzy matching
3. **Relevance-based scoring** with domain-specific boosts
4. **Linear performance** characteristics suitable for real-time use

The mathematical foundation ensures predictable, scalable behavior while maintaining user-friendly search capabilities across the transportation network.