# Uzhavan M4 V2.3 Specification: Targeted Pure-Green Healthy Balancing

## 1. Problem Statement & Audit Finding
The M4 V2.2 three-seed replication established that:
- External test Healthy recall fluctuates violently across random initializations: $70.33\% \to 34.00\% \to 97.33\%$.
- Healthy $\to$ Rust confusion is $0.00\%$ across all three seeds ($0 / 600$).
- The entire failure mode is Healthy leaves being misclassified as **Tikka Leaf Spot**.
- In the training set (`in_tn_multicrop_vitc`), `healthy_or_abiotic` contains 1,164 nutrient deficiency images (chlorosis, necrosis) and only **285 pure-green healthy images**, while Tikka has **2,236 images** ($7.8:1$ ratio).
- Because pure-green foliage was starved in training, the network's hyperplane between pristine green leaves and early Tikka lesions is unconstrained and shifts randomly under standard SGD/AdamW initialization.

## 2. V2.3 Intervention
Maintain **100% parity** with V2.2 in:
- Model architecture: EfficientNetV2-S
- Taxonomy: 3 classes (`healthy_or_abiotic`, `rust`, `tikka_leaf_spot`)
- Dataset & Splits: 5,920 train samples, zero West Bengal contamination
- Augmentations: Field shadow simulation, Gaussian blur, Color jitter, RandomResizedCrop
- Loss: Weighted Cross-Entropy (WCE), Rust weight multiplier = $1.0\times$
- Optimization: AdamW, lr = 1e-4, weight_decay = 1e-2, batch_size = 32, epochs = 15, AMP float16

**Single Controlled Change:**
Implement a deterministic targeted oversampling sampler during training:
- Pure-green Healthy training images ($N=285$) receive weight multiplier:
  $$w_{\text{green}} = \frac{N_{\text{tikka}}}{N_{\text{green}}} = \frac{2236}{285} \approx 7.8456$$
- Tikka ($N=2236$), Rust ($N=2235$), and Nutrient Deficiency ($N=1164$) receive weight $1.0$.
- In any sampled batch, the effective probability of drawing a pure-green Healthy image equals the probability of drawing a Tikka image ($28.4\% : 28.4\%$, exactly $1:1$).
- Sampler uses a deterministic generator keyed to `--seed`.
