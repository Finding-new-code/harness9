import re
import math

# 1. Test Quote Regex with Contractions
text1 = "It's clear that the company's product was innovative."
text2 = 'Feynman famously said: "There is plenty of room at the bottom."'
text3 = "He shouted: 'Stop immediately!' and ran."
text4 = "'It's working,' said Bardeen."

def extract_quotes(text):
    quotes = []
    # Double quotes:
    for m in re.finditer(r'["“]([^"”\r\n]{3,})["”]', text):
        quotes.append(m.group(1))
    # Single quotes: must not be preceded or followed by word characters (apostrophes in contractions)
    single_pattern = r'(?:(?<=^)|(?<=[\s\(\[\{,:]))[\'‘]((?:[^\'’\r\n]|(?<=[a-zA-Z])[\'’](?=[a-zA-Z])){3,}?)[\'’](?=$|[\s.,!?;:\)\]\}])'
    for m in re.finditer(single_pattern, text):
        quotes.append(m.group(1))
    return quotes

print('Text 1 (contractions):', extract_quotes(text1))
print('Text 2 (double quotes):', extract_quotes(text2))
print('Text 3 (single quote dialogue):', extract_quotes(text3))
print('Text 4 (single quote with contraction):', extract_quotes(text4))
assert extract_quotes(text1) == []
assert len(extract_quotes(text2)) == 1
assert len(extract_quotes(text3)) == 1
assert len(extract_quotes(text4)) == 1
print('All quote extraction assertions PASSED!')

# 2. Test Word Boundary Lexical Matching
MODAL_LEVEL_3_TERMS = {
    "always", "proven", "definitely", "solely", "undoubtedly", "certainly",
    "indisputable", "conclusively", "conclusive", "undeniably", "settled",
    "fact", "irrefutably", "single-handedly", "unquestionably"
}
MODAL_LEVEL_1_TERMS = {
    "may", "suggests", "suggest", "suggesting", "one factor", "partially",
    "possibly", "could", "preliminary", "hypothesized", "might", "potentially",
    "in some cases", "tentatively", "indicated"
}

def classify_modal(text):
    lower = text.lower()
    modal_level = 2
    if any(re.search(rf'\b{re.escape(term)}\b', lower) for term in MODAL_LEVEL_3_TERMS):
        modal_level = 3
    elif any(re.search(rf'\b{re.escape(term)}\b', lower) for term in MODAL_LEVEL_1_TERMS):
        modal_level = 1
    return modal_level

assert classify_modal("The factory produced goods in June.") == 2
assert classify_modal("The artifact was discovered in the desert.") == 2
assert classify_modal("This is an indisputable fact of physics.") == 3
assert classify_modal("Findings suggest a new mechanism.") == 1
print('All modal classification assertions PASSED!')

# 3. Test Compound Growth Regex
growth_pattern = re.compile(
    r'(?:grew|increased|rose|surged|jumped|climbed)\s+from\s+(\d+(?:\.\d+)?)\s*(?:million|billion|thousand|k|m|b)?\s+to\s+(\d+(?:\.\d+)?)\s*(?:million|billion|thousand|k|m|b)?(?:,\s*|\s+)(?:a|an|\(a|\(an)?\s*(?:increase\s+of\s+|growth\s+of\s+|up\s+)?(\d+(?:\.\d+)?)%\s*(?:increase|growth)?\)?',
    re.IGNORECASE
)

for sample in [
    "Revenue grew from 10 million to 30 million, a 300% increase.",
    "Sales increased from 10 to 30, an increase of 300%.",
    "Output rose from 10 to 30 (a 300% increase).",
    "Volume surged from 10 to 30, up 300%."
]:
    m = growth_pattern.search(sample)
    assert m is not None, f"Failed on: {sample}"
    v_start, v_end, stated_pct = float(m.group(1)), float(m.group(2)), float(m.group(3))
    calc_pct = ((v_end - v_start) / v_start) * 100.0
    print(f"Sample: {sample} -> start={v_start}, end={v_end}, stated={stated_pct}%, calc={calc_pct}%")
print('All compound growth assertions PASSED!')
