# SignTalk Word Detection Accuracy Guide

## Problem Analysis

Your 10-word BISINDO gesture recognition system is struggling with accuracy. Here's why:

### Current Performance Issues

| Word | F1-Score | Precision | Recall | Test Samples | Status |
|------|----------|-----------|--------|--------------|--------|
| **Tolong** (Please) | 0.349 | 0.21 | 1.00 | 29 | 🔴 CRITICAL |
| **Maaf** (Sorry) | 0.308 | 0.18 | 1.00 | 30 | 🔴 CRITICAL |
| **Terimakasih** (Thank you) | 0.659 | 0.49 | 1.00 | 27 | 🟠 POOR |
| **Belajar** (Study/Learn) | 0.746 | 0.83 | 0.68 | 125 | 🟠 POOR |
| **Bisa** (Can) | 0.709 | 0.60 | 0.87 | 136 | 🟠 FAIR |
| Permisi (Pardon) | 0.983 | 1.00 | 0.97 | 30 | 🟢 GOOD |
| Sama sama (Welcome) | 0.900 | 0.87 | 0.93 | 29 | 🟢 GOOD |
| **Sedikit** (A little) | 1.000 | 1.00 | 1.00 | 117 | 🟢 PERFECT |
| Teman-teman (Friends) | 0.941 | 0.90 | 0.98 | 129 | 🟢 GOOD |
| Bahasa isyarat (Sign language) | 0.874 | 0.89 | 0.86 | 141 | 🟢 GOOD |

### Root Causes

#### 1. **Severe Class Imbalance**
- Letters (A-Z): 22,218 samples (avg 854/letter)
- Numbers (0-9): 7,791 samples (avg 779/number)
- Words: 3,949 samples (avg 395/word) ← **5x less data!**

**Critical imbalance for worst words:**
- Tolong: 142 samples (1/6 of a letter)
- Terimakasih: 134 samples  
- Maaf: 150 samples

#### 2. **Gesture Similarity**
Some BISINDO gestures are visually similar, causing confusion:
- **Tolong** (Please) ↔ **Terimakasih** (Thank you) - Similar hand shapes
- **Belajar** (Study) ↔ **Bisa** (Can) - Related hand movements
- **Maaf** (Sorry) ↔ **Permisi** (Pardon) - Small difference in execution

#### 3. **Low Precision, High Recall**
The model is over-predicting these words when unsure:
- Says "Tolong" 100% of the time it tries
- But only correct 21% of the time
- Means it's confusing other gestures AS these words

---

## Solution Strategy

### Phase 1: Immediate Improvements (Synthetic Data + Class Weighting)

Running now: `scripts/augment_and_retrain.py`

**What it does:**
1. **Data Augmentation** - Creates synthetic samples for low-data words
   - Jitter: Add small random noise (±2%)
   - Scale: Simulate hand moving closer/farther
   - Rotation: Simulate hand rotating slightly
   - Dropout: Simulate landmark detection failures
   
2. **Class Weighting** - Makes the model prioritize rare classes
   - Gives **1.69x weight** to Terimakasih, Tolong, Maaf
   - Forces model to learn better boundaries for these words

3. **Balanced Training** - Equalizes samples per class
   - All words: 700+ samples (up from 134-703)
   - All letters/numbers: 850+ samples

**Expected improvement:** +10-20% F1 for poor-performing words

### Phase 2: Real Data Collection (Best Solution)

If Phase 1 is not sufficient (< 0.85 F1), you must collect MORE REAL DATA:

#### Quick Data Collection Script

```bash
python scripts/collect_data.py --label "Tolong" --samples 300
python scripts/collect_data.py --label "Terimakasih" --samples 300
python scripts/collect_data.py --label "Maaf" --samples 300
python scripts/collect_data.py --label "Belajar" --samples 200
python scripts/collect_data.py --label "Bisa" --samples 200
```

#### Collection Instructions

1. **Setup**
   ```bash
   python scripts/collect_data.py --label "Tolong" --samples 300
   ```

2. **During collection:**
   - Show ONLY the right gesture for "Tolong"
   - Vary hand position: left, right, center
   - Vary distance: arm extended, closer to camera
   - Vary rotation: turn hand slightly
   - Collect from different people if possible
   - Ensure good lighting

3. **Quality check:**
   - After collection, run: `python tools/check_dataset.py`
   - Verify the new label has 300+ samples

4. **Retrain:**
   ```bash
   python scripts/prepare_dataset.py
   python scripts/train_model.py
   ```

#### Why This Works

- **Sedikit (A little)**: F1 = 1.0 with only 583 samples ✓
- **Permisi (Pardon)**: F1 = 0.983 with 149 samples ✓
- **Tolong (Please)**: F1 = 0.349 with 142 samples ✗

The difference: Data quality and class distinctiveness. When you collect real data:
1. Model learns true gesture boundaries
2. Augmentation can then amplify those boundaries
3. Prevents overfitting to synthetic patterns

---

## Implementation Plan

### Week 1: Synthetic + Weighted Model

```
Day 1-2: Train augmented model
  ↓ Run: python scripts/augment_and_retrain.py
  ↓ Check: model/random_forest_v3_augmented.pkl
  ↓ Test on demo website

Day 3: Evaluate results
  ↓ If F1 ≥ 0.85 for all words → Deploy v3
  ↓ If F1 < 0.85 → Go to Phase 2
```

### Week 2-3: Targeted Data Collection (if needed)

```
If words still < 0.85 F1:
  1. Identify worst 3 words (likely Tolong, Terimakasih, Maaf)
  2. Collect 200-300 NEW samples each
  3. Retrain model
  4. Repeat until F1 ≥ 0.90
```

---

## Confusion Analysis: Why Gestures Get Misclassified

### Example: Tolong (Please) Misclassifications

When the model predicts "Tolong":
- ✗ Correct 21% of the time
- ✗ Confuses it with: Maaf, Belajar, Terimakasih (similar hand shapes)
- ✗ These words have similar upward/outward hand movements

**Solution:** Collect "Tolong" samples that clearly distinguish:
- Hand position
- Finger configuration
- Movement direction

---

## Monitoring Progress

After training, check this file:
- `model/model_v3_augmented_meta.json` - Training metadata
- `model/random_forest_v3_augmented.pkl` - The new model

Compare with original:
- Original v2: Accuracy 81.45%, word F1 avg 0.74
- Augmented v3: Expected 85%+, word F1 avg 0.85+

---

## FAQ

### Q: Do I need to collect data myself?
**A:** Ideally yes for final perfection. But the augmented synthetic model (Phase 1) should improve significantly and be deployable.

### Q: Can you generate synthetic gesture data?
**A:** The `augment_and_retrain.py` script does this now! It creates 3,054 synthetic samples using:
- Random jitter
- Scaling
- Rotation
- Dropout

### Q: Why not just use a different model?
**A:** 
- RandomForest is fast and interpretable
- The problem is **DATA** imbalance, not model architecture
- Switching to neural nets without more data won't help
- Once data is balanced, RF performs very well

### Q: How long does training take?
**A:** ~3-5 minutes on a modern machine (200 trees, 37k samples)

### Q: Should I delete my current model?
**A:** No! Keep both:
- `random_forest_v2.pkl` (current, 81.45% accuracy)
- `random_forest_v3_augmented.pkl` (new, expected 85%+)

Test both and use whichever performs better.

---

## Next Steps

1. ✅ **Running now:** `python scripts/augment_and_retrain.py`
2. **When done:** Check results in console output
3. **If F1 > 0.85:** Deploy v3 model (update app.py to use v3)
4. **If F1 < 0.85:** Collect more real data using collection script

See you in a few minutes with the results!
