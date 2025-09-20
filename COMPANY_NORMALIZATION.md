# Company Name Normalization

This document describes the company name normalization feature that prevents duplicate organization folders.

## Overview

The company name normalization system automatically detects and merges similar company names to prevent duplicate folders like:
- `Bank_of_America` and `BANK_OF_AMERICA`
- `City_of_Kent_-_Utility_Billing` and `City_of_Kent_Utility_Billing`
- `Target` and `Target_Corporation`

## Features

### 1. Fuzzy Matching
- Uses similarity scoring to match company names with variations
- Handles case differences, punctuation, and common business suffixes
- Configurable similarity threshold (default: 0.75)

### 2. Automatic Duplicate Merging
- Scans existing output directory for duplicate company folders
- Automatically merges duplicates during initialization
- Preserves all files when merging folders
- Handles filename conflicts by adding numeric suffixes

### 3. Name Normalization
- Removes common prefixes: "the", "a", "an"
- Removes common suffixes: "inc", "corp", "llc", "ltd", "company", etc.
- Applies proper case formatting
- Sanitizes folder names for filesystem compatibility

## Configuration

### config.yaml
```yaml
organization:
  # Enable/disable company name normalization
  enable_company_normalization: true
  
  # Similarity threshold (0.0-1.0, higher = more strict)
  company_similarity_threshold: 0.75
```

### CLI Arguments
```bash
# Disable normalization
python cli.py --disable-normalization

# Custom similarity threshold
python cli.py --similarity-threshold 0.8
```

## How It Works

1. **Initialization**: Scans existing output directory for company folders
2. **Duplicate Detection**: Identifies folders with high similarity scores
3. **Automatic Merging**: Merges duplicate folders automatically
4. **Name Matching**: New company names are matched against existing ones
5. **Folder Creation**: Uses canonical names for consistent folder structure

## Examples

### Before Normalization
```
output/
├── Bank_of_America/
├── BANK_OF_AMERICA/
├── City_of_Kent_-_Utility_Billing/
├── City_of_Kent_Utility_Billing/
└── Target_Corporation/
```

### After Normalization
```
output/
├── Bank_of_America/          # Merged BANK_OF_AMERICA into this
├── City_of_Kent_-_Utility_Billing/  # Merged other Kent folder
└── Target/                   # Normalized from Target_Corporation
```

### Name Matching Examples
- "BANK OF AMERICA" → matches existing "Bank of America"
- "The Target Corporation" → matches existing "Target"
- "City of Kent Utility Billing" → matches "City of Kent - Utility Billing"
- "US Department of Education" → matches "U.S. Department of Education"

## Benefits

1. **Reduces Clutter**: Eliminates duplicate company folders
2. **Improves Organization**: Consistent naming across all documents
3. **Automatic**: No manual intervention required
4. **Safe**: Preserves all files during merging
5. **Configurable**: Adjustable similarity thresholds
6. **Backwards Compatible**: Works with existing folder structures

## Technical Details

### Similarity Calculation
- Uses `difflib.SequenceMatcher` for basic text similarity
- Applies word overlap scoring for better matching
- Includes subset bonus for names that are subsets of others
- Weighted combination: 60% text similarity + 30% word overlap + 10% subset bonus

### Merge Strategy
- Keeps folder with more files
- Uses shorter canonical name as tiebreaker
- Moves all files preserving directory structure
- Handles filename conflicts automatically
- Removes empty source folders after merging

### Performance
- Scans existing folders only once during initialization
- O(n²) complexity for duplicate detection (acceptable for typical use cases)
- Minimal overhead during normal processing
