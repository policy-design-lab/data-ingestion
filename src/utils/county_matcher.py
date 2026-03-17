# python
"""
Generalized county/state normalization and matching.

Capabilities:
- Normalize state names to USPS codes.
- Normalize county names (strip suffixes, normalize punctuation/spacing).
- Generate robust variants (St/Ste with/without dot, article-collapsed forms like DeKalb/LaSalle/DuPage,
  apostrophe/no-apostrophe, hyphen/space flip, and fully compacted forms).
- Case-insensitive exact matching using generated variants.
- Within-state fuzzy fallback with a conservative threshold (default 0.92).
- Special state-aware overrides for a few persistent edge cases.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Iterable, Dict, List, Tuple
import pandas as pd

# --------------------------
# State normalization
# --------------------------

STATE_NAME_TO_CODE = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
    'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'district of columbia': 'DC',
    'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL',
    'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA',
    'maine': 'ME', 'maryland': 'MD', 'massachusetts': 'MA', 'michigan': 'MI',
    'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO', 'montana': 'MT',
    'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
    'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND',
    'ohio': 'OH', 'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'puerto rico': 'PR',
    'rhode island': 'RI', 'south carolina': 'SC', 'south dakota': 'SD', 'tennessee': 'TN',
    'texas': 'TX', 'utah': 'UT', 'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA',
    'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'
}


def normalize_state_to_code(v) -> str | None:
    """Convert state name or 2-letter abbreviation to USPS code (upper)."""
    if pd.isna(v):
        return None
    s = str(v).strip()
    if len(s) == 2 and s.isalpha():
        return s.upper()
    return STATE_NAME_TO_CODE.get(s.lower())


# --------------------------
# County name normalization
# --------------------------

SUFFIXES = [
    ' county', ' parish', ' borough', ' census area', ' city and borough',
    ' municipality', ' city'
]
ARTICLES = {'de', 'la', 'du', 'le'}   # generic particles that sometimes attach to next token (e.g., DeKalb)
LEADING_STE = {'st', 'ste'}           # saint forms

# Special, state-aware overrides for persistent outliers
# Keys are (state_code, lowercased county_clean); values are canonical names present in the reference.
SPECIAL_OVERRIDES: Dict[Tuple[str, str], str] = {
    ('LA', 'st john baptist'): "St. John the Baptist",
    ('SD', 'shannon'): "Oglala Lakota",
}


def strip_accents(s: str) -> str:
    """Remove diacritics (e.g., Doña -> Dona) for robust matching."""
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))


def basic_clean(s: str) -> str:
    """
    Minimal, generalized cleaning:
    - strip accents
    - normalize quotes
    - collapse spaces
    - strip a single known county-like suffix (County/Parish/City/etc.)
    - normalize spacing around hyphens/slashes
    - standardize O Brien/Obrien -> O'Brien
    """
    s = strip_accents(s or '')
    s = s.replace('’', "'").replace('"', '')
    s = re.sub(r'\s+', ' ', s).strip()

    s_l = s.lower()
    for suf in SUFFIXES:
        if s_l.endswith(suf):
            s = s[:-len(suf)].strip()
            break

    s = re.sub(r'\s*[-–—]\s*', '-', s)   # "A - B" -> "A-B"
    s = re.sub(r'\s*/\s*', '/', s)       # "A / B" -> "A/B"

    # Normalize O Brien-like patterns
    s = re.sub(r"\bO\s+Brien\b", "O'Brien", s, flags=re.IGNORECASE)
    s = re.sub(r"\bObrien\b", "O'Brien", s, flags=re.IGNORECASE)

    return s


def token_split(name: str) -> List[str]:
    """Split on spaces and hyphens (after normalization)."""
    return re.split(r'[\s-]+', name.strip()) if name else []


def join_tokens(tokens: Iterable[str]) -> str:
    return ' '.join(t for t in tokens if t)


def st_normalize_first_token(tokens: List[str]) -> List[List[str]]:
    """
    Generate variants for leading St/Ste tokens with/without period, normalized casing.
    E.g., ["st", "louis"] -> ["St.", "louis"] and ["St", "louis"].
    """
    if not tokens:
        return [tokens]
    first = tokens[0]
    first_l = first.lower().rstrip('.')
    variants = []
    if first_l in LEADING_STE:
        canonical = first_l.capitalize() + '.'
        variants.append([canonical] + tokens[1:])
        variants.append([first_l.capitalize()] + tokens[1:])  # without dot
    else:
        variants.append(tokens)
    return variants


def collapse_articles(tokens: List[str]) -> List[List[str]]:
    """
    If a token is an article (de/la/du/le), generate both spaced and collapsed variants:
      ["De","Kalb"] -> ["De Kalb"] and ["DeKalb"]
    Apply generically for any occurrence.
    """
    variants = {tuple(tokens)}
    for i, t in enumerate(tokens[:-1]):
        if t.lower() in ARTICLES:
            collapsed = tokens[:i] + [t + tokens[i + 1]] + tokens[i + 2:]
            variants.add(tuple(collapsed))
    return [list(v) for v in variants]


def apostrophe_variants(s: str) -> List[str]:
    """Keep and drop apostrophes to handle inconsistent sources."""
    return [s, s.replace("'", '')] if "'" in s else [s]


def dot_variants(s: str) -> List[str]:
    """Keep and drop dots for tokens like 'St.'."""
    return [s, s.replace('.', '')] if '.' in s else [s]


def county_variants(name: str) -> List[str]:
    """
    Build robust variants for a county name:
    - base clean
    - St/Ste with/without dot
    - particles collapsed/space-separated (De/La/Du/Le)
    - apostrophe/no-apostrophe
    - hyphen/space swap
    - compact variant (remove spaces, dots, hyphens, apostrophes)
    """
    base = basic_clean(name)
    tokens = token_split(base)

    # St/Ste variants
    st_variants: List[List[str]] = []
    for tv in st_normalize_first_token(tokens):
        st_variants.append(tv)

    # Article collapse variants
    token_variants: List[List[str]] = []
    for tv in st_variants:
        token_variants.extend(collapse_articles(tv))

    # Build string variants
    string_variants = set()
    for tv in token_variants:
        v = join_tokens(tv)
        for v1 in apostrophe_variants(v):
            for v2 in dot_variants(v1):
                string_variants.add(v2)

    # Hyphen/space flips
    more = set()
    for sv in list(string_variants):
        if ' ' in sv:
            more.add(sv.replace(' ', '-'))
        if '-' in sv:
            more.add(sv.replace('-', ' '))
    string_variants.update(more)

    # Compact variants (remove punctuation/space)
    compact = set(re.sub(r"[ .'-]", "", sv) for sv in string_variants)
    string_variants.update(compact)

    # Final unique set (non-empty)
    return sorted({sv.strip() for sv in string_variants if sv and sv.strip()})


def seq_ratio(a: str, b: str) -> float:
    """Similarity ratio in [0..1]."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# --------------------------
# Index and matching
# --------------------------

def build_ref_index(ref_df: pd.DataFrame) -> Dict[Tuple[str, str], str]:
    """
    Build an index (state_code, variant_lower) -> fips_code
    using all generated variants of the canonical county names.
    """
    idx: Dict[Tuple[str, str], str] = {}
    for _, r in ref_df.iterrows():
        sc = r['state_code']
        name = r['name']
        fips = r['fips_code']
        for v in county_variants(name):
            idx[(sc, v.lower())] = fips
    return idx


def match_counties(
    data_df: pd.DataFrame,
    ref_df: pd.DataFrame,
    state_col: str = 'state',
    county_col: str = 'county',
    fuzzy_threshold: float = 0.92
) -> pd.DataFrame:
    """
    Pipeline:
    1) Normalize state names to USPS codes.
    2) Normalize county names and generate robust variants; exact match first (case-insensitive).
    3) Fuzzy match within-state for any remaining unmatched (conservative threshold).
    Returns df with added columns: state_code, county_clean, fips_code, match_type, fuzzy_score.
    """
    df = data_df.copy()

    # 1) normalize state
    df['state_code'] = df[state_col].apply(normalize_state_to_code)

    # 2) exact match using variant index
    ref = ref_df[['state_code', 'name', 'fips_code']].drop_duplicates().copy()
    ref['name_clean'] = ref['name'].apply(basic_clean)
    ref_idx = build_ref_index(ref)

    # Prepare columns
    df['county_clean'] = df[county_col].apply(basic_clean)

    # Apply state-aware overrides BEFORE variant generation/matching
    def _apply_override(row):
        sc = row['state_code']
        cc = row['county_clean']
        if pd.isna(sc) or pd.isna(cc):
            return cc
        key = (sc, str(cc).lower())
        return SPECIAL_OVERRIDES.get(key, cc)

    df['county_clean'] = df.apply(_apply_override, axis=1)

    df['fips_code'] = None
    df['match_type'] = 'unmatched'
    df['fuzzy_score'] = None

    # Exact by variants (case-insensitive via lower())
    for i, row in df.iterrows():
        sc = row['state_code']
        if pd.isna(sc):
            continue
        variants = county_variants(row['county_clean'])
        hit = None
        for v in variants:
            hit = ref_idx.get((sc, v.lower()))
            if hit:
                break
        if hit:
            df.at[i, 'fips_code'] = hit
            df.at[i, 'match_type'] = 'exact'

    # 3) fuzzy for remaining unmatched (state-scoped)
    to_fuzzy = df[df['match_type'] == 'unmatched']
    if not to_fuzzy.empty:
        # Precompute normalized ref variants per state for fuzzy search
        ref_by_state = {sc: grp[['name', 'name_clean', 'fips_code']].copy()
                        for sc, grp in ref.groupby('state_code')}

        for i, row in to_fuzzy.iterrows():
            sc = row['state_code']
            name = row['county_clean']
            if pd.isna(sc) or pd.isna(name):
                continue

            candidates = ref_by_state.get(sc)
            if candidates is None or candidates.empty:
                continue

            # Compare base and compacted form (remove punctuation/spaces)
            a_forms = {
                name,
                re.sub(r"[ .'-]", "", name.lower())
            }

            best_fips, best_score = None, 0.0
            for _, r in candidates.iterrows():
                b = r['name_clean']
                b_forms = {
                    b,
                    re.sub(r"[ .'-]", "", b.lower())
                }
                for af in a_forms:
                    for bf in b_forms:
                        score = seq_ratio(af, bf)
                        if score > best_score:
                            best_score = score
                            best_fips = r['fips_code']

            if best_score >= fuzzy_threshold and best_fips:
                df.at[i, 'fips_code'] = best_fips
                df.at[i, 'match_type'] = 'fuzzy'
                df.at[i, 'fuzzy_score'] = round(best_score, 4)
            else:
                df.at[i, 'fuzzy_score'] = round(best_score, 4)

    return df